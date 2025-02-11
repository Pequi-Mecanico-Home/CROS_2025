import os
import csv
import argparse
from random import choice
import soundfile as sf
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from tqdm import tqdm
import numpy as np
import librosa
import tempfile
import sys
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.adversarial_text import gerar_palavra_aleatoria, gerar_amostras_negativas

# Ensure output files are saved in the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

def text_to_speech(model, config, text, output_file, voice_name):
    try:
        outputs = model.synthesize(
            text.replace(".", " | "),
            config,
            speaker_wav=voice_name,
            gpt_cond_len=3,
            language="pt",
        )

        wav_16k = librosa.resample(outputs.get("wav"), orig_sr=24000, target_sr=16000)
        sf.write(output_file,wav_16k, 16000)
    except Exception as e:
        print(f"Error synthesizing audio for {output_file}: {e}")

def combine_audios(audio1_path, audio2_path):
    audio1, sr1 = sf.read(audio1_path)
    audio2, sr2 = sf.read(audio2_path)
    
    # Resamplear se as taxas de amostragem forem diferentes
    if sr1 != sr2:
        if sr1 > sr2:
            audio2 = librosa.resample(audio2, sr2, sr1)
            sr2 = sr1
        else:
            audio1 = librosa.resample(audio1, sr1, sr2)
            sr1 = sr2
    
    # Concatenar os áudios
    combined_audio = np.concatenate((audio1, audio2))

    # Salvar o áudio combinado em um arquivo temporário
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
        sf.write(temp_audio_file.name, combined_audio, sr1)
        temp_audio_path = temp_audio_file.name

    return temp_audio_path, sr1

def generate_audios_negatives(model, config, speakers_dict, fake_words, n_samples, output_folder):
    voices = list(speakers_dict.keys())
    output_folder = os.path.join(output_folder)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    metadata_file = os.path.join(output_folder, "metadata.csv")

    used_voices = set()
    combined_voices = [(voice1, voice2) for i, voice1 in enumerate(voices) for voice2 in voices[i+1:]]
    np.random.shuffle(combined_voices)
    voices = combined_voices

    with open(metadata_file, "w", encoding="utf-8", newline="") as metadata:
        metadata_writer = csv.writer(metadata)
        metadata_writer.writerow(["Sample", "Voice", "file_name", "Word"])

        for i in tqdm(range(n_samples)):
            available_voices = [voice for voice in voices if voice not in used_voices]

            if not available_voices:
                print("All voices have been used. Resetting used voices.")
                used_voices.clear()
                available_voices = voices
            
            voice = choice(available_voices)

            if isinstance(voice, tuple):
                voice1, voice2 = voice
                voice = [choice(speakers_dict[voice1]), choice(speakers_dict[voice2])]
                voice_name = f"{voice1}_{voice2}"
            else:
                voice_name = voice
                voice = choice(speakers_dict[voice_name])
            used_voices.add(voice_name)

            random_id = os.urandom(4).hex()
            output_file = os.path.join(output_folder, f"{voice_name}_{random_id}.wav")
            audio_file = os.path.basename(output_file)

            # Generate false word
            word = fake_words[i]

            # Generate audio
            text_to_speech(model, config, word, output_file, voice)

            # Write metadata with cleaned voice
            metadata_writer.writerow([i+1, voice_name, audio_file, word])

def main():
    parser = argparse.ArgumentParser(description="Generate speech audio from CSV using Azure Speech Service.")
    # parser.add_argument("--csv_file", type=str, required=False, help="Path to input CSV file.")
    # parser.add_argument("--output_folder", type=str, required=True, help="Path to output folder for audio files.")
    # parser.add_argument("--n_samples", type=int, required=False, help="Number of samples to generate for the keyword.")
    # parser.add_argument("--random", action="store_true", help="Generate random samples.")
    parser.add_argument("--config", type=str, required=False, default = 'config.yaml', help="Path to the configuration YAML file.")

    args = parser.parse_args()

    with open(args.config, "r") as file:
        config = yaml.safe_load(file)
    
    csv_file = config.get("csv_file")
    output_folder = config.get("output_folder")
    n_samples = config.get("n_samples_negative")
    random = config.get("random",False)

    config = XttsConfig()
    config.load_json("XTTS-v2/config.json")
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir="XTTS-v2", eval=True)
    model.cuda()
    print("Inferências...")

    if csv_file:
        speakers_dict = {}
        with open(csv_file, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header
            for row in reader:
                path, speaker_id = row
                if speaker_id not in speakers_dict:
                    speakers_dict[speaker_id] = []
                speakers_dict[speaker_id].append(path)

    if random:
        fake_words = [gerar_palavra_aleatoria() for _ in range(n_samples)]
    else:
        fake_words = gerar_amostras_negativas(n_samples)

    generate_audios_negatives(model, config, speakers_dict, fake_words, n_samples, output_folder)

if __name__ == "__main__":
    main()