#!/bin/bash

# Update and intall wget inside the docker container if not installed
apt-get update && apt-get install -y wget

# training set (~2,000 hours from the ACAV100M Dataset)
# See https://huggingface.co/datasets/davidscripka/openwakeword_features for more information
wget https://huggingface.co/datasets/davidscripka/openwakeword_features/resolve/main/openwakeword_features_ACAV100M_2000_hrs_16bit.npy

# validation set for false positive rate estimation (~11 hours)
wget https://huggingface.co/datasets/davidscripka/openwakeword_features/resolve/main/validation_set_features.npy