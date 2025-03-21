#!/bin/bash

# Update and intall wget inside the docker container if not installed
apt-get update && apt-get install -y wget

# Create the directory structure for the models
mkdir -p /opt/conda/lib/python3.10/site-packages/openwakeword/resources/models/

# Install melspectrogram.onnx model and 
wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.onnx -O /opt/conda/lib/python3.10/site-packages/openwakeword/resources/models/melspectrogram.onnx
wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.onnx -O /opt/conda/lib/python3.10/site-packages/openwakeword/resources/models/embedding_model.onnx
wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/melspectrogram.onnx -O /opt/conda/lib/python3.10/site-packages/openwakeword/resources/models/melspectrogram.tflite
wget https://github.com/dscripka/openWakeWord/releases/download/v0.5.1/embedding_model.onnx -O /opt/conda/lib/python3.10/site-packages/openwakeword/resources/models/embedding_model.tflite


# training set (~2,000 hours from the ACAV100M Dataset)
# See https://huggingface.co/datasets/davidscripka/openwakeword_features for more information
wget https://huggingface.co/datasets/davidscripka/openwakeword_features/resolve/main/openwakeword_features_ACAV100M_2000_hrs_16bit.npy

# validation set for false positive rate estimation (~11 hours)
wget https://huggingface.co/datasets/davidscripka/openwakeword_features/resolve/main/validation_set_features.npy