# blender-kitti

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

| ![KITTI Point Cloud](img/blender_kitti_render_point_cloud_main.png?raw=true "Main view") |![KITTI Point Cloud](img/blender_kitti_render_point_cloud_top.png?raw=true "Top view") |
|:-------------------------:|:-------------------------:|
| ![KITTI Point Cloud](img/blender_kitti_render_voxels_main.png?raw=true "Main view voxels") |![KITTI Point Cloud](img/blender_kitti_render_voxels_top.png?raw=true "Top view voxels") |
| ![KITTI Scene Flow](img/blender_kitti_render_scene_flow_main.png?raw=true "Main view scene flow") |![KITTI Scene Flow](img/blender_kitti_render_scene_flow_top.png?raw=true "Top view scene flow") |
| ![KITTI Bounding Boxes](img/blender_kitti_render_boxes_main.png?raw=true "Main view boxes") |![KITTI Bounding Boxes](img/blender_kitti_render_boxes_top.png?raw=true "Top view bounding boxes") |

## Update (2025):
* Now uses the official `bpy` package published on PyPI. Both headless rendering and development are much more convenient.
* Fixed compatibility for **Blender 4.5**
* Switched to **uv** for project management
* Changed texture image shape for better GPU compatibility

## About

`blender-kitti` contains utilities to create and render large particle collections in Blender (voxel grids, point clouds) with per-particle color information.
This project has two goals:
* **Exactness**. Particles are created at the exact coordinates you provide and colors match the specified RGB values. Every particle can be colored individually.
* **Performance**. Creating a 100k-point point cloud should be on the order of seconds. Fast enough for practical, altough offline, renders.

These properties make `blender-kitti` useful for rendering large-scale datasets such as KITTI (hence the name) and similar data. This repository is intentionally a toolbox of techniques rather than a one-size-fits-all visualization package. You will probably need to adapt the snippets to your use case.
There are example scripts that reproduce the demo images. use them to verify your installation and as a starting point for changes.

## Render demo images

You can use `uv` to run the blender kitti examples script.
By default, output images are created in `blender_kitti_examples/img/`.
```
uv run blender_kitti_render_demo point_cloud
uv run blender_kitti_render_demo voxels
uv run blender_kitti_render_demo scene_flow
uv run blender_kitti_render_demo boxes
```

## Installation into Blender's bundled Python
If you want to work interactively inside Blender's GUI, install the package into Blender's bundled Python virtualenv.
```
# Change into your Blender installation's python directory, e.g.:
# cd /opt/blender-2.90.1-linux64/2.90/python
$ cd <blender_directory>/<blender_version>/python

# Ensure that pip available
$ ./bin/python3.11 lib/python3.11/ensurepip

# Install the package in editable mode
$ ./bin/python3.11 -m pip install -e <path_to_blender_kitti>

```

## Work on a scene in Blender

You can import and use `blender-kitti` in the Python console inside the Blender GUI to manipulate a scene interactively.

```
# Create a random [Nx3] numpy array and add as point cloud to the scene.
import bpy
import numpy as np
from blender_kitti import add_point_cloud

# create some points
points = np.random.normal(loc=0.0, scale=2.0, size=(100, 3))

# get current scene
scene = bpy.context.scene

# create point cloud object and link to scene
add_point_cloud(points=points, scene=scene, particle_radius=0.2)
```

Result:

![KITTI Point Cloud](img/demo_point_cloud_random.png?raw=true "Main view")

## Ideas for future development

* Track created objects/meshes/images so entire scenes can be cleaned up programmatically.
* Handle name clashes or optionally overwrite existing objects.
* Allow specifying per-particle rotation/scale.
* Design a small API for common usecases.
