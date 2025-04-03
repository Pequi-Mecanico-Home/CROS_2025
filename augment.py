import os
import sys
import tempfile
import torch
import numpy as np
import scipy
import logging
from tqdm import tqdm
import yaml
from pathlib import Path
import openwakeword
from openwakeword.data import generate_adversarial_texts, augment_clips, mmap_batch_generator
from openwakeword.utils import compute_features_from_generator
from openwakeword.utils import AudioFeatures
import librosa
from librosa import resample
import soundfile as sf # for resampling audio files


def resample_audio(data, original_sample_rate, target_sample_rate):
        resampled_data = resample(data, orig_sr=original_sample_rate, target_sr=target_sample_rate)
        return resampled_data

#  Função para verificar e resamplear um arquivo de áudio, se necessário
def resample_if_needed(clip_path, target_sample_rate):
    try:
            # Verificar se o arquivo é um arquivo de áudio válido
        if not clip_path.endswith(".wav"):
            print(f"Skipping non-audio file: {clip_path}")
            return
        
        # Ler o arquivo de áudio
        data, sample_rate = sf.read(clip_path)
        # Verificar se a taxa de amostragem é diferente da desejada
        if sample_rate != target_sample_rate:
            # print(f"Resampling {clip_path} from {sample_rate}Hz to {target_sample_rate}Hz")
            
            # Resamplear o áudio
            data_resampled = resample_audio(data, sample_rate, target_sample_rate)
            
            # Salvar o arquivo resampleado no mesmo diretório
            sf.write(clip_path, data_resampled, target_sample_rate)
    except Exception as e:
        print(f"Error processing {clip_path}: {e}")

if __name__ == '__main__':
    # Get training config file
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--training_config",
        help="The path to the training config file (required)",
        type=str,
        required=True
    )
    parser.add_argument(
        "--overwrite",
        help="Overwrite existing openwakeword features when the --augment_clips flag is used",
        action="store_true",
        default="False",
        required=False
    )
    args = parser.parse_args()
    config = yaml.load(open(args.training_config, 'r').read(), yaml.Loader)

    # Define output locations
    config["output_dir"] = os.path.abspath(config["output_dir"])
    if not os.path.exists(config["output_dir"]):
        os.mkdir(config["output_dir"])
    if not os.path.exists(os.path.join(config["output_dir"], config["model_name"])):
        os.mkdir(os.path.join(config["output_dir"], config["model_name"]))

    
    # Diretórios de entrada e saída
    positive_train_output_dir = os.path.join(config["output_dir"], config["model_name"], "positive_train")
    positive_train_output_dir = config["positive_train_output_dir"] if "positive_train_output_dir" in config else positive_train_output_dir
    positive_test_output_dir = os.path.join(config["output_dir"], config["model_name"], "positive_test")
    positive_test_output_dir = config["positive_test_output_dir"] if "positive_test_output_dir" in config else positive_test_output_dir
    negative_train_output_dir = os.path.join(config["output_dir"], config["model_name"], "negative_train")
    negative_train_output_dir = config["negative_train_output_dir"] if "negative_train_output_dir" in config else negative_train_output_dir
    negative_test_output_dir = os.path.join(config["output_dir"], config["model_name"], "negative_test")
    negative_test_output_dir = config["negative_test_output_dir"] if "negative_test_output_dir" in config else negative_test_output_dir
    feature_save_dir = os.path.join(config["output_dir"], config["model_name"])

    # Obter caminhos para os arquivos de áudio
    positive_clips_train = [str(i) for i in Path(positive_train_output_dir).glob("*.wav")]
    positive_clips_test = [str(i) for i in Path(positive_test_output_dir).glob("*.wav")]
    negative_clips_train = [str(i) for i in Path(negative_train_output_dir).glob("*.wav")]
    negative_clips_test = [str(i) for i in Path(negative_test_output_dir).glob("*.wav")]

    # Verificar se há arquivos positivos nos diretórios
    if not positive_clips_train or not positive_clips_test:
        raise ValueError("No positive clips found in the specified directories.")

    target_sample_rate = 16000

    # Verificar e resamplear os arquivos de áudio, se necessário
    for clip in positive_clips_train + positive_clips_test + negative_clips_train + negative_clips_test:
        resample_if_needed(clip, target_sample_rate)

    # Get paths for impulse response and background audio files
    rir_paths = [i.path for j in config["rir_paths"] for i in os.scandir(j) if i.name.endswith(".wav")]

    # Filtrar apenas arquivos .wav em background_paths
    background_paths = []
    if len(config["background_paths_duplication_rate"]) != len(config["background_paths"]):
        config["background_paths_duplication_rate"] = [1] * len(config["background_paths"])
    for background_path, duplication_rate in zip(config["background_paths"], config["background_paths_duplication_rate"]):
        background_paths.extend([i.path for i in os.scandir(background_path) if i.name.endswith(".wav")] * duplication_rate)
    
    
    # Resample audio files in rir_paths and background_paths if needed
    for clip in rir_paths + background_paths:
        resample_if_needed(clip, target_sample_rate)


    # Set the total length of the training clips based on the ~median generated clip duration, rounding to the nearest 1000 samples
    # and setting to 32000 when the median + 750 ms is close to that, as it's a good default value
        n = 50  # sample size
        positive_clips = [str(i) for i in Path(positive_test_output_dir).glob("*.wav")]
        duration_in_samples = []
        for i in range(n):
            sr, dat = scipy.io.wavfile.read(positive_clips[np.random.randint(0, len(positive_clips))])
            duration_in_samples.append(len(dat))

        config["total_length"] = int(round(np.median(duration_in_samples)/1000)*1000) + 12000  # add 750 ms to clip duration as buffer
        if config["total_length"] < 32000:
            config["total_length"] = 32000  # set a minimum of 32000 samples (2 seconds)
        elif abs(config["total_length"] - 32000) <= 4000:
            config["total_length"] = 32000

    # Do Data Augmentation

    if not os.path.exists(os.path.join(feature_save_dir, "positive_features_train.npy")) or args.overwrite is True:
    
        positive_clips_train = [str(i) for i in Path(positive_train_output_dir).glob("*.wav")]*config["augmentation_rounds"]
        positive_clips_train_generator = augment_clips(positive_clips_train, total_length=config["total_length"],
                                                       batch_size=config["augmentation_batch_size"],
                                                       background_clip_paths=background_paths,
                                                       RIR_paths=rir_paths)
        positive_clips_test = [str(i) for i in Path(positive_test_output_dir).glob("*.wav")]*config["augmentation_rounds"]
        positive_clips_test_generator = augment_clips(positive_clips_test, total_length=config["total_length"],
                                                      batch_size=config["augmentation_batch_size"],
                                                      background_clip_paths=background_paths,
                                                      RIR_paths=rir_paths)
        negative_clips_train = [str(i) for i in Path(negative_train_output_dir).glob("*.wav")]*config["augmentation_rounds"]
        negative_clips_train_generator = augment_clips(negative_clips_train, total_length=config["total_length"],
                                                       batch_size=config["augmentation_batch_size"],
                                                       background_clip_paths=background_paths,
                                                       RIR_paths=rir_paths)
        negative_clips_test = [str(i) for i in Path(negative_test_output_dir).glob("*.wav")]*config["augmentation_rounds"]
        negative_clips_test_generator = augment_clips(negative_clips_test, total_length=config["total_length"],
                                                      batch_size=config["augmentation_batch_size"],
                                                      background_clip_paths=background_paths,
                                                      RIR_paths=rir_paths)
        # Compute features and save to disk via memmapped arrays
        logging.info("#"*50 + "\nComputing openwakeword features for generated samples\n" + "#"*50)
        n_cpus = os.cpu_count()
        if n_cpus is None:
            n_cpus = 1
        else:
            n_cpus = n_cpus//2
        compute_features_from_generator(positive_clips_train_generator, n_total=len(os.listdir(positive_train_output_dir)),
                                        clip_duration=config["total_length"],
                                        output_file=os.path.join(feature_save_dir, "positive_features_train.npy"),
                                        device="gpu" if torch.cuda.is_available() else "cpu",
                                        ncpu=n_cpus if not torch.cuda.is_available() else 1,)
        compute_features_from_generator(negative_clips_train_generator, n_total=len(os.listdir(negative_train_output_dir)),
                                        clip_duration=config["total_length"],
                                        output_file=os.path.join(feature_save_dir, "negative_features_train.npy"),
                                        device="gpu" if torch.cuda.is_available() else "cpu",
                                        ncpu=n_cpus if not torch.cuda.is_available() else 1)
        compute_features_from_generator(positive_clips_test_generator, n_total=len(os.listdir(positive_test_output_dir)),
                                        clip_duration=config["total_length"],
                                        output_file=os.path.join(feature_save_dir, "positive_features_test.npy"),
                                        device="gpu" if torch.cuda.is_available() else "cpu",
                                        ncpu=n_cpus if not torch.cuda.is_available() else 1)
        compute_features_from_generator(negative_clips_test_generator, n_total=len(os.listdir(negative_test_output_dir)),
                                        clip_duration=config["total_length"],
                                        output_file=os.path.join(feature_save_dir, "negative_features_test.npy"),
                                        device="gpu" if torch.cuda.is_available() else "cpu",
                                        ncpu=n_cpus if not torch.cuda.is_available() else 1)
    else:
        logging.warning("Openwakeword features already exist, skipping data augmentation and feature generation")