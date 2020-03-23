# -*- coding: utf-8 -*-
""""""
import typing
import numpy as np

from .bpy_helper import needs_bpy
from .scene_setup import setup_scene
from .object_spotlight import add_spotlight_ground


def execute_data_tasks(tasks: {str: typing.Any}, scene):

    for instance_name, (task_f, task_kwargs) in tasks.items():
        if "scene" not in task_kwargs:
            task_kwargs["scene"] = scene
        task_f(**task_kwargs)


def make_scene_single_object(scene, config):
    add_spotlight_ground(scene)


def make_scene(config: typing.Union[typing.Dict[str, typing.Any], None] = None):
    if config is None:
        config = {}

    # Todo some kind of default?
    use_background_image = True
    scene_name = "blender_kitti"

    def dummy(_scene, _config):
        pass

    scene_maker = dummy

    if "scene_setup" in config:
        scene_mode = config["scene_setup"]
        if scene_mode == "single_object":
            use_background_image = True
            scene_maker = make_scene_single_object
        else:
            raise NotImplementedError()

    if "sample_id" in config:
        scene_name = config["sample_id"]

    scene, cameras = setup_scene(
        name=scene_name, use_background_image=use_background_image
    )

    scene_maker(scene, config)
    return scene, cameras
