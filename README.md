# blender-kitti

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

| ![KITTI Point Cloud](img/blender_kitti_render_point_cloud_main.png?raw=true "Main view") |![KITTI Point Cloud](img/blender_kitti_render_point_cloud_top.png?raw=true "Top view") |
|:-------------------------:|:-------------------------:|
| ![KITTI Point Cloud](img/blender_kitti_render_voxels_main.png?raw=true "Main view voxels") |![KITTI Point Cloud](img/blender_kitti_render_voxels_top.png?raw=true "Top view voxels") |
| ![KITTI Scene Flow](img/blender_kitti_render_scene_flow_main.png?raw=true "Main view scene flow") |![KITTI Scene Flow](img/blender_kitti_render_scene_flow_top.png?raw=true "Top view scene flow") |
| ![KITTI Bounding Boxes](img/blender_kitti_render_boxes_main.png?raw=true "Main view boxes") |![KITTI Bounding Boxes](img/blender_kitti_render_boxes_top.png?raw=true "Top view bounding boxes") |

## About

This repository contains some code to create large particle collections (voxel grids, point clouds)
together with color information in Blender.
`blender-kitti` has two goals in mind:
* The created objects are exact, meaning that all particles are created at their defined location
and all colors have the exact RGB-value as specified. All particles can be colored individually.
* Performance of the scrips is acceptable. It should not take much longer than a second to create a 100k point cloud.

Together, these qualities enable `blender-kitti` to render large scale data from the KITTI dataset
(hence the name) or related datasets.

When it comes to visualization, everyone has a different usecase. So this is not a
one-fits-all solution but rather a collection of techniques that can be adapted
to individual usecases.

There is example code that renders the demo images above. Use this to verify that
your installation works and as a starting point for your modifications.

## Installation into Blender's bundled python

```
# Wherever your Blender installation is located. E.g. cd /opt/blender-2.90.1-linux64/2.90/python
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

Render the bundled KITTI point cloud with pseudo odometry for hsv colored scene flow from two different camera perspectives. This writes two image files to the `/tmp` folder.

```
$ blender --background --python-console

>>> import blender_kitti_examples
>>> blender_kitti_examples.render_kitti_scene_flow()
```

Render the bundled KITTI point cloud with some random bounding boxes (with random colors). This writes two image files to the `/tmp` folder.

```
$ blender --background --python-console

>>> import blender_kitti_examples
>>> blender_kitti_examples.render_kitti_bounding_boxes()


## Work on a scene in Blender

You can import and use `blender-kitti` in the python console window in the Blender-GUI
itself to work on a given scene.

```
# Create a random [Nx3] numpy array and add as point cloud to a scene in blender.
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

* Track all created objects/meshes/images and be able to completely remove them later
* Handle name clashes or overwrite existing objects
* Define the rotation/scale of individual particles
* Create a useful, small API
* Finally be able to build Blender-bpy as module (Dockerfile)


