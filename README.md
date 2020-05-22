# blender_kitti

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

| ![KITTI Point Cloud](img/blender_kitti_render_point_cloud_main.png?raw=true "Main view") |![KITTI Point Cloud](img/blender_kitti_render_point_cloud_top.png?raw=true "Top view") |
|:-------------------------:|:-------------------------:|
| ![KITTI Point Cloud](img/blender_kitti_render_voxels_main.png?raw=true "Main view voxels") |![KITTI Point Cloud](img/blender_kitti_render_voxels_top.png?raw=true "Top view voxels") |

Currently this repository serves as a small collection of techniques to accurately
render data in blender.

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

Render the bundled KITTI point cloud with semantic coloring from two different camera
perspectives. This writes two image files to the `/tmp` folder.

```
$ blender --background --python-console

>>> import blender_kitti_examples
>>> blender_kitti_examples.render_kitti_point_cloud()
```

Render the bundled Semantic KITTI voxel grid as top view and close-up image.
This writes two image files to the `/tmp` folder.
```
$ blender --background --python-console

>>> import blender_kitti_examples
>>> blender_kitti_examples.render_kitti_voxels()
```
