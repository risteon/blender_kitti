# blender_kitti

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

| ![KITTI Point Cloud](img/blender_kitti_render_point_cloud_main.png?raw=true "Main view") | ![KITTI Point Cloud](img/blender_kitti_render_point_cloud_top.png?raw=true "Top view") |
|:-------------------------:|:-------------------------:|

## Installation into Blender's bundled python

```
# e.g. cd /opt/blender-2.80-linux-glibc217-x86_64/2.80/python
$ cd <blender_directory>/<blender_version>/python

# make pip available
$ ./bin/python3.Xm lib/python3.X/ensurepip

# install
$ ./bin/pip3 install -e <path_to_blender_kitti>

```

## Render demo images

Render the bundled KITTI point cloud with semantic coloring from two cameras.

```
$ blender --background --python-console

>>> import blender_kitti_examples
>>> blender_kitti_examples.render_kitti_point_cloud()
```

