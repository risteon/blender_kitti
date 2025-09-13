# -*- coding: utf-8 -*-
"""Example renders of point cloud and voxels"""

from dataclasses import dataclass
import enum
import pathlib
import typing

import bpy
import numpy as np
import tyro


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


class DemoScene(enum.StrEnum):
    POINT_CLOUD = enum.auto()
    VOXELS = enum.auto()
    SCENE_FLOW = enum.auto()
    ALL = enum.auto()


@dataclass
class Args:
    demo_scene: tyro.conf.Positional[tyro.conf.EnumChoicesFromValues[DemoScene]]
    """Select the demo scene to render."""

    use_gpu: bool = False
    """Set to true to enable GPU usage for rendering"""

    output_path: pathlib.Path = pathlib.Path(__file__).parent / "img"
    """"""


def render(scene, cameras, output_path, scene_name):
    for cam in cameras:
        p = output_path / f"blender_kitti_demo_{scene_name}_{cam.data.name}.png"
        scene.camera = cam
        scene.render.filepath = str(p)
        bpy.ops.render.render(write_still=True, scene=scene.name)


def add_demo_point_cloud(scene) -> None:
    point_cloud, colors = get_semantic_kitti_point_cloud()
    _ = add_point_cloud(points=point_cloud, colors=colors, scene=scene)


def add_demo_scene_flow(scene):
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


def add_cameras_voxels(scene):
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
    return [cam_main, cam_top]


def add_demo_voxels(scene):
    voxels, colors = get_semantic_kitti_voxels()
    _ = add_voxels(voxels=voxels, colors=colors, scene=scene)


def render_demo_images(
    demo_scenes: typing.List[DemoScene], output_path: pathlib.Path, use_gpu: bool
) -> None:
    for demo_scene in demo_scenes:
        if demo_scene == DemoScene.ALL:
            continue

        scene = setup_scene(name=f"demo_{str(demo_scene)}")
        if demo_scene == DemoScene.VOXELS:
            cameras = add_cameras_voxels(scene)
        else:
            cameras = add_cameras_default(scene)

        # there should be a single view layer available
        scene.view_layers[0].cycles.use_denoising = True
        scene.render.resolution_percentage = 100
        scene.render.resolution_x = 640
        scene.render.resolution_y = 480
        # alpha background
        scene.render.film_transparent = True
        #
        if use_gpu:
            scene.cycles.device = "GPU"
        else:
            scene.cycles.device = "CPU"

        add_f = {
            DemoScene.POINT_CLOUD: add_demo_point_cloud,
            DemoScene.VOXELS: add_demo_voxels,
            DemoScene.SCENE_FLOW: add_demo_scene_flow,
        }
        add_f[demo_scene](scene)

        render(scene, cameras, output_path, str(demo_scene))


def main() -> None:
    args = tyro.cli(Args)
    args.output_path.mkdir(exist_ok=True)

    if args.demo_scene == DemoScene.ALL:
        demo_scenes = list(DemoScene)
    else:
        demo_scenes = [args.demo_scene]

    render_demo_images(demo_scenes, args.output_path, args.use_gpu)


if __name__ == "__main__":
    main()
