#!/bin/env python
# -*- coding: utf-8 -*-
""" """

import click
import logging
import typing

import bpy
from ruamel.yaml import YAML

from .blender_kitti import (
    add_objects_from_data,
    make_scene,
    extract_data_tasks_from_file,
)
from .system_setup import enable_devices
from .scene_setup import add_cameras_default

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def process_file(filename: str, scene=None):
    tasks, global_config = extract_data_tasks_from_file(filename)
    if scene is None:
        try:
            scene = make_scene(global_config)
        except ImportError:
            logger.warning("Ignoring scene setup.")
            scene, cameras = None, None

    try:
        add_objects_from_data(tasks, scene)
    except ImportError:
        pass
    return scene, global_config


def make_scene_from_data_files(render_config: typing.Union[str, None], filenames):
    if render_config is not None:
        yaml = YAML(typ="safe")
        config = yaml.load(render_config)
    else:
        config = {}

    tasks = {}

    if isinstance(filenames, str):
        filenames = [filenames]

    for filename in filenames:
        tasks_from_file, config_from_file = extract_data_tasks_from_file(filename)
        # Todo check for conflicts and abort if necessary
        tasks.update(tasks_from_file)
        config.update(config_from_file)

    try:
        scene = make_scene(config)
    except ImportError:
        logger.warning("Ignoring scene setup.")
        scene = None

    if "whitelist" in config:
        # only keep the instances that are in the whitelist
        instance_whitelist = set(config["whitelist"])
        tasks = dict((k, v) for k, v in tasks.items() if k in instance_whitelist)

    add_objects_from_data(tasks, scene)

    enable_gpu_rendering = True
    if enable_gpu_rendering:
        enable_devices()
        scene.cycles.device = "GPU"

    return scene, config


def render_scene():
    bpy.ops.render.render(write_still=True)


@click.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.option("--python", required=False)
@click.option("--background/--no-background", required=False)
@click.option("--render_config", default=None)
@click.argument("filenames", type=click.Path(exists=True), nargs=-1)
def render(python, background, render_config: typing.Union[str, None], filenames):
    """ """
    scene, config = make_scene_from_data_files(render_config, filenames)
    add_cameras_default(scene)

    scene.render.filepath = "/tmp/test.png"
    render_scene()
