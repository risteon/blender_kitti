# -*- coding: utf-8 -*-
"""Example renders of point cloud and voxels"""

import pathlib

import bpy
import numpy as np

from blender_kitti import (
    add_point_cloud,
    add_voxels,
    setup_scene,
    add_cameras_default,
    add_flow_mesh,
)
from blender_kitti.scene_setup import (
    create_camera_top_view_ortho,
    create_camera_perspective,
)
from .data import (
    get_semantic_kitti_point_cloud,
    get_semantic_kitti_voxels,
    get_pseudo_flow,
)


def render(scene, cameras, output_path):
    for cam in cameras:
        if isinstance(output_path, str):
            p = output_path.format(cam.data.name)
        elif isinstance(output_path, pathlib.Path):
            p = output_path / (cam.data.name + ".png")
        elif callable(output_path):
            p = output_path(cam.data.name)
        else:
            raise ValueError(
                "Cannot handle output path type {}".format(type(output_path))
            )

        scene.camera = cam
        scene.render.filepath = p
        bpy.ops.render.render(write_still=True, scene=scene.name)


def render_kitti_point_cloud(gpu_compute=False):
    scene = setup_scene()
    cameras = add_cameras_default(scene)

    # there should be a single view layer available
    scene.view_layers[0].cycles.use_denoising = True
    scene.render.resolution_percentage = 100
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    # alpha background
    scene.render.film_transparent = True
    #
    if gpu_compute:
        scene.cycles.device = "GPU"
    else:
        scene.cycles.device = "CPU"

    point_cloud, colors = get_semantic_kitti_point_cloud()
    _ = add_point_cloud(points=point_cloud, colors=colors, scene=scene)
    render(scene, cameras, "/tmp/blender_kitti_render_point_cloud_{}.png")


def render_kitti_scene_flow(gpu_compute=False):
    scene = setup_scene()
    cameras = add_cameras_default(scene)

    # there should be a single view layer available
    scene.view_layers[0].cycles.use_denoising = True
    scene.render.resolution_percentage = 100
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    # alpha background
    scene.render.film_transparent = True
    #
    if gpu_compute:
        scene.cycles.device = "GPU"
    else:
        scene.cycles.device = "CPU"

    # reduce number of points, especially near vehicle
    point_cloud, _ = get_semantic_kitti_point_cloud()
    num_pts = 6000
    dist = np.linalg.norm(point_cloud, axis=-1)
    prob = (dist - dist.min()) / (dist.max() - dist.min())
    prob_normed = prob / prob.sum()
    indices = np.arange(point_cloud.shape[0])
    indices = np.random.choice(indices, size=num_pts, replace=False, p=prob_normed)
    point_cloud_downsample = point_cloud[indices, ...]

    flow, colors = get_pseudo_flow(point_cloud_downsample)
    _ = add_flow_mesh(
        point_cloud=point_cloud_downsample, flow=flow, colors_rgba=colors, scene=scene
    )
    render(scene, cameras, "/tmp/blender_kitti_render_scene_flow_{}.png")


def render_kitti_voxels(gpu_compute=False):
    scene = setup_scene()
    cam_main = create_camera_perspective(
        location=(2.86, 17.52, 3.74),
        rotation_quat=(0.749, 0.620, -0.150, -0.181),
    )
    scene.collection.objects.link(cam_main)

    cam_top = create_camera_top_view_ortho(
        center=(25.5, 25.5), scale=51.0, name="CameraTop"
    )
    scene.collection.objects.link(cam_top)
    scene.camera = cam_main

    scene.view_layers["View Layer"].cycles.use_denoising = True
    scene.render.resolution_percentage = 100
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    # alpha background
    scene.render.film_transparent = True
    #
    if gpu_compute:
        scene.cycles.device = "GPU"
    else:
        scene.cycles.device = "CPU"

    voxels, colors = get_semantic_kitti_voxels()
    _ = add_voxels(voxels=voxels, colors=colors, scene=scene)
    render(scene, [cam_top, cam_main], "/tmp/blender_kitti_render_voxels_{}.png")
