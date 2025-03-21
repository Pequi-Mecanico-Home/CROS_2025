import os
from tqdm import tqdm
import scipy.io.wavfile
import numpy as np
from datasets import load_dataset

# Download room impulse responses collected by MIT
# https://mcdermottlab.mit.edu/Reverb/IR_Survey.html

# O room impulse response é uma ferramenta essencial para entender e 
# replicar as propriedades acústicas de um ambiente, 
# permitindo desde a melhoria da qualidade sonora em espaços reais 
# até a criação de experiências imersivas em ambientes digitais.

output_dir = "./mit_rirs"
if not os.path.exists(output_dir):
    os.mkdir(output_dir)

rir_dataset = load_dataset("davidscripka/MIT_environmental_impulse_responses", split="train", streaming=True)

# Save clips to 16-bit PCM wav files
for row in tqdm(rir_dataset):
    name = row['audio']['path'].split('/')[-1]
    scipy.io.wavfile.write(os.path.join(output_dir, name), 16000, (row['audio']['array'] * 32767).astype(np.int16))