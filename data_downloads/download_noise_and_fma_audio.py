import os
from tqdm import tqdm
import scipy.io.wavfile
import numpy as np
from datasets import load_dataset, Dataset, Audio
from pathlib import Path
import subprocess

# Audioset Dataset (https://research.google.com/audioset/dataset/index.html)
# Download one part of the audioset .tar files, extract, and convert to 16khz
# For full-scale training, it's recommended to download the entire dataset from
# https://huggingface.co/datasets/agkphysics/AudioSet, and
# even potentially combine it with other background noise datasets (e.g., FSD50k, Freesound, etc.)

if not os.path.exists("audioset"):
    os.mkdir("audioset")

fname = "bal_train09.tar"
out_dir = f"audioset/{fname}"
link = "https://huggingface.co/datasets/agkphysics/AudioSet/resolve/main/data/" + fname

# Download the file
subprocess.run(["wget", "-O", out_dir, link], check=True)

# Extract the .tar file
subprocess.run(["tar", "-xvf", out_dir, "-C", "audioset"], check=True)

output_dir = "./audioset_16k"
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

# Convert audioset files to 16khz sample rate
audioset_dataset = Dataset.from_dict({"audio": [str(i) for i in Path("audioset/audio").glob("**/*.flac")]})
audioset_dataset = audioset_dataset.cast_column("audio", Audio(sampling_rate=16000))
for row in tqdm(audioset_dataset):
    name = row['audio']['path'].split('/')[-1].replace(".flac", ".wav")
    scipy.io.wavfile.write(os.path.join(output_dir, name), 16000, (row['audio']['array'] * 32767).astype(np.int16))

# Free Music Archive dataset (https://github.com/mdeff/fma)
output_dir = "./fma"
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

fma_dataset = load_dataset("rudraml/fma", name="small", split="train", streaming=True)
fma_dataset = iter(fma_dataset.cast_column("audio", Audio(sampling_rate=16000)))

n_hours = 1  # use only 1 hour of clips for this example, recommend increasing for full-scale training
for i in tqdm(range(n_hours * 3600 // 30)):  # this works because the FMA dataset is all 30 second clips
    row = next(fma_dataset)
    name = row['audio']['path'].split('/')[-1].replace(".mp3", ".wav")
    scipy.io.wavfile.write(os.path.join(output_dir, name), 16000, (row['audio']['array'] * 32767).astype(np.int16))
    i += 1
    if i == n_hours * 3600 // 30:
        break