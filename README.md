# CROS_2025

Clone o repositório
```bash
git clone --recursive-submodules git@github.com:Pequi-Mecanico-Home/CROS_2025.git
cd CROS_2025
```

Crie a imagem docker:
```bash
docker build -t miss_wakeword docker/
```
Pendente: Incluir colcon build --symlink-install && source install/setup.bash no Dockerfile

Abra um container
```bash
xhost local: && docker run  -it  --rm  --name miss_wakeword --privileged    --net=host  --env 'DISPLAY'  --env="QT_X11_NO_MITSHM=1" --volume "/tmp/.X11-unix:/tmp/.X11-unix:rw"  --volume "/dev:/dev"  --volume "./modules/miss_mic/:/workspace/miss_mic/src"  --volume "./modules/miss_wakeword/:/workspace/miss_wakeword/src"  --runtime nvidia  --ulimit memlock=-1  --ulimit stack=67108864  miss_wakeword
```


Liste os dispositivos disponíveis

```bash
python3 -m sounddevice
```

Iniciar nó do microfone
```bash
ros2 run miss_mic --ros-args -p device:=<index_mic>
```

Executar wake word
```bash
ros2 run miss_wakeword inference
```

