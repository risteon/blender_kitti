#!/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import click
import logging

from .blender_kitti import execute_data_tasks, make_scene, extract_data_tasks_from_file
from .system_setup import setup_system

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def process_file(filename: str):
    tasks, config = extract_data_tasks_from_file(filename)
    try:
        scene, cameras = make_scene(config)
    except ImportError:
        logger.warning("Ignoring scene setup.")
        scene, cameras = None, None

    try:
        execute_data_tasks(tasks, scene)
    except ImportError:
        pass
    return scene, cameras


@click.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.option("--python", required=False)
@click.option("--background/--no-background", required=False)
@click.option("--render_config", default=None)
@click.argument("filenames", type=click.Path(exists=True), nargs=-1)
def render(python, background, render_config, filenames):
    """

    """
    for filename in filenames:
        scene, cameras = process_file(filename)

        # Todo read and apply render config
        try:
            setup_system(enable_gpu_rendering=True, scene=scene)
        except ImportError:
            pass
