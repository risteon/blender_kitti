# -*- coding: utf-8 -*-
"""Example renders of point cloud and voxels"""

import pathlib
from blender_kitti.bpy_helper import needs_bpy_bmesh
from blender_kitti import add_point_cloud, add_voxels, setup_scene, add_cameras_default
from blender_kitti.scene_setup import (
    create_camera_top_view_ortho,
    create_camera_perspective,
)
from .data import get_semantic_kitti_point_cloud, get_semantic_kitti_voxels


def dry_render(_scene, cameras, output_path):
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
        print("Render camera {} to file path {}.".format(cam.data.name, p))


@needs_bpy_bmesh(alternative_func=dry_render)
def render(scene, cameras, output_path, *, bpy):
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

    point_cloud, colors = get_semantic_kitti_point_cloud()
    _ = add_point_cloud(points=point_cloud, colors=colors, scene=scene)
    render(scene, cameras, "/tmp/blender_kitti_render_point_cloud_{}.png")


def render_kitti_voxels(gpu_compute=False):

    scene = setup_scene()
    cam_main = create_camera_perspective(
        location=(2.86, 17.52, 3.74), rotation_quat=(0.749, 0.620, -0.150, -0.181),
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
