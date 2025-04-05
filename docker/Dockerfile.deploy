# Use a ROS Humble base image
FROM ros:humble

# Set the working directory to /ros
WORKDIR /workspace

# Update the package list
RUN apt update

# Install dependencies
RUN apt install -y \
    python3-pip \
    portaudio19-dev \
    libasound2-dev \
    libportaudio2

# Install OpenWakeWord and PyAudio using pip
RUN pip3 install \
    openwakeword==0.5 \
    pyaudio \
    sounddevice

# why god why god do i gotta suffer
# WORKDIR /workspace/miss_mic
# RUN colcon build --symlink-install && \
#     bash -c "source install/setup.bash"

# WORKDIR /workspace/miss_wakeword
# RUN colcon build --symlink-install && \
#     bash -c "source install/setup.bash"
