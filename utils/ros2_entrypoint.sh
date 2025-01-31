#uncomment the following lines to build the workspace when starting container
colcon build --symlink-install
source install/setup.bash

exec "$@"