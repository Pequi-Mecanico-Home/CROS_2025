# A Simplified Pipeline for Wakeword Creation and Deployment: Leveraging Zero-Shot Text-to-Speech and ROS2 for Robotic Systems

This repository provides a complete pipeline for training and deploying a custom wakeword detection model. It leverages zero-shot text-to-speech (xTTS) to generate synthetic training data, combined with data augmentation techniques such as real-world background noise and room impulse responses (RIRs) for acoustic realism.

The trained model is deployed in a robotics environment using ROS2, enabling real-time voice interaction. The entire setup is containerized using Docker, ensuring reproducibility and ease of deployment across systems.

## Overview
Key features:
- End-to-end pipeline for wakeword model generation.

- Synthetic audio generation using zero-shot TTS (XTTS).

- Audio augmentation with noise and RIRs.

- Training with OpenWakeWord architecture.

- ROS2 deployment for real-time use in robotic systems.


## Clone Repository

```bash
git clone --recurse-submodules git@github.com:Pequi-Mecanico-Home/CROS_2025.git
cd CROS_2025
```

## Synthetic Data generation:

### Install Dependencies

Ensure you have Python 3 and pip installed. Then run the following scripts to download required resources:

```bash
python3 data_downloads/download_mit_rirs.py
python3 data_downloads/download_noise_and_fma_audio.py
./data_downloads/setup_openwakeword_resources.sh
```

### Donwload Repositories and Models

Clone TTS tools and download voice datasets:

```bash
git clone https://github.com/coqui-ai/TTS.git
git clone https://huggingface.co/coqui/XTTS-v2
wget https://www.openslr.org/resources/146/cml_tts_dataset_portuguese_v0.1.tar.bz
```
Extract the dataset:

```bash
tar -xvjf cml_tts_dataset_portuguese_v0.1.tar.bz2
```

### Docker Setup

Pull and run a prebuilt Docker image with GPU and audio dependencies:

```bash
docker pull gpettro/cros2025:xtts
```

Start the container (replace /home/your/directory to your workspace path):

``` bash
docker run -it --gpus all --ipc host -v /home/seu/diretório:/workspace_cros2025  gpettro/cros2025:xtts bash 
```

### Generate Audio Samples

The project generates positive and negative samples using a TTS model. You configure this using a YAML file and the provided scripts.

The generated files are saved in separate directories.

### Project Structure

- config.yaml: Configuration file containing parameters for sample generation.
- infer_dataset.py: Script to generate positive audio samples.
- infer_dataset_negative.py: Script to generate negative audio samples.
- selected_audios_cml.csv: CSV file containing audio paths and speaker IDs.
- utils_infer/: Directory containing utilities for adversarial text generation.
- XTTS-v2/: Directory containing the text-to-speech synthesis model.

## Configuration (config.yaml Example)

```yaml
csv_file: 'selected_audios_cml.csv'          # CSV containing audio data
output_folder: 'generated_samples'           # Folder for positive samples
negative_output_folder: 'negative_samples'   # Folder for negative samples
n_samples_positive: 5000                     # Number of positive samples
n_samples_negative: 5000                     # Number of negative samples
keyword: 'Hey Miss'                          # Wake word for positive samples
random: True                                 # Generate random samples
```

### Generating Samples
To generate positive audio samples:

```bash
python3 inference/infer_dataset.py --config configs/config.yaml
```

To generate negative audio samples:

```bash
python3 inference/infer_dataset_negative.py --config configs/config.yaml
```

The files will be saved in the folders defined in config.yaml, with a metadata.csv file in each folder containing sample details.


## Model Training :
### Data Augmentation

Add realistic acoustic effects to your data:

```bash
python3 augment.py --training_config configs/my_model.yml --overwrite
```

### Train the Wakeword Model

Train using your YAML config:

```bash 
python3 train.py --training_config configs/my_model.yml
```

Example (my_model.yml):

The training process uses a YAML configuration file (e.g., my_model.yml) defining:
- Model name and target wake word/phrase.
- Number of training and validation samples.
- Resource directories (RIR, AudioSet, and FMA noise data).
- Augmentation parameters, batch sizes, and model settings (type, layer size, training steps, etc.).
- Output directories for positive/negative clips and precomputed features.


## Deployment


### Build Docker image for ROS2 integration:
```bash
docker build -t miss_wakeword docker/
```

### Start the ROS2 container:
```bash
xhost local: && docker run  -it  --rm  --name miss_wakeword --privileged    --net=host  --env 'DISPLAY'  --env="QT_X11_NO_MITSHM=1" --volume "/tmp/.X11-unix:/tmp/.X11-unix:rw"  --volume "/dev:/dev"  --volume "./modules/miss_mic/:/workspace/miss_mic/src"  --volume "./modules/miss_wakeword/:/workspace/miss_wakeword/src"  --runtime nvidia  --ulimit memlock=-1  --ulimit stack=67108864  miss_wakeword
```


### List available devices:

Identify the correct microphone device index: 

```bash
python3 -m sounddevice
```

### Start Microphone Node and WakeWord detection:

Run with selected device index:

```bash
ros2 run miss_mic --ros-args -p device:=<index_mic>
```

Run Wakeword Node:
```bash
ros2 run miss_wakeword inference
```
