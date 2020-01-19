# -*- coding: utf-8 -*-
"""Example renders of point cloud and voxels"""

import bpy
from blender_kitti import add_point_cloud, add_voxels, setup_scene
from .data import get_semantic_kitti_point_cloud, get_semantic_kitti_voxels


def render_kitti_point_cloud(gpu_compute=False):

    scene, cameras = setup_scene()
    scene.view_layers['View Layer'].cycles.use_denoising = True
    scene.render.resolution_percentage = 100
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    # alpha background
    scene.render.film_transparent = True
    #
    if gpu_compute:
        scene.cycles.device = 'GPU'
    else:
        scene.cycles.device = 'CPU'

    point_cloud, color = get_semantic_kitti_point_cloud()
    _ = add_point_cloud(point_cloud, color, scene=scene)

    for cam, name in zip(cameras, ['main', 'top']):
        scene.camera = cam
        scene.render.filepath = '/tmp/blender_kitti_render_point_cloud_{}.png'.format(name)
        bpy.ops.render.render(write_still=True)


def render_kitti_voxels():
    voxels, color = get_semantic_kitti_voxels()
    obj_voxels = add_voxels(voxels, color)
