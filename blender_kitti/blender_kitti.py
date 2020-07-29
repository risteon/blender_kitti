# -*- coding: utf-8 -*-
"""

"""
import typing
import logging
import re
import numpy as np

from collections import defaultdict
from ruamel.yaml import YAML

from .particles import add_point_cloud, add_voxels
from .mesh import add_object_from_mesh
from .scene_setup import setup_scene
from .object_spotlight import add_spotlight_ground

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

"""
TYPE+INSTANCE_NAME+ARG_NAME/OPTIONAL_DICT_KEY
e.g. 'point_cloud+some_name+points
e.g. 'mesh+some_name+vertices
e.g. 'mesh+some_name+vertex_colors/semantics
"""
regex_key = re.compile(
    r"([a-zA-Z0-9_-]+)\+([a-zA-Z0-9_-]+)\+([a-zA-Z0-9_-]+)(?:\/([a-zA-Z0-9_-]+))?"
)

global_config_key = "config"
data_structures = {
    "point_cloud": add_point_cloud,
    "voxels": add_voxels,
    "mesh": add_object_from_mesh,
}
data_tree = defaultdict(lambda: defaultdict(dict))


def execute_data_tasks(tasks: {str: typing.Any}, scene):

    for instance_name, (task_f, task_kwargs) in tasks.items():
        if "scene" not in task_kwargs:
            task_kwargs["scene"] = scene
        try:
            task_f(**task_kwargs)
        except ImportError:
            logger.warning("Ignoring task.")


def make_scene_single_object(scene, _config):
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

    scene = setup_scene(name=scene_name, use_background_image=use_background_image)
    scene_maker(scene, config)
    return scene


def extract_config_from_data(data) -> dict:
    try:
        conf = data[global_config_key]
        conf = bytes(conf).decode("utf-8")
        yaml = YAML(typ="safe")
        return yaml.load(conf)
    except KeyError:
        return {}


def extract_data_tasks_from_file(
    filepath: str,
) -> {str: (typing.Callable, {str: typing.Any})}:
    logger.info("Processing data file '{}'.".format(filepath))
    data = np.load(filepath)

    global_config = extract_config_from_data(data)

    def filter_fn(x):
        if x[1] is None and x[0] != global_config_key:
            logger.warning("Ignoring unknown entry key '{}'.".format(x[0]))
        return x[1] is not None

    matches = [(x, regex_key.fullmatch(x)) for x in data.keys()]
    matches = list(filter(filter_fn, matches))
    matches = [(data[x[0]], x[1].groups()) for x in matches]

    x = data_tree
    for d, key in matches:
        if key[3] is None:
            x[key[0]][key[1]][key[2]] = d
        else:
            try:
                arg_dict = x[key[0]][key[1]][key[2]]
            except KeyError:
                arg_dict = {}
                x[key[0]][key[1]][key[2]] = arg_dict

            arg_dict[key[3]] = d

    tasks = {}
    for data_type, instances in x.items():
        try:
            f = data_structures[data_type]
            tasks.update(
                {k: (f, {"name_prefix": k, **v}) for k, v in instances.items()}
            )

        except KeyError:
            logger.warning("Ignoring unknown entry '{}'.".format(data_type))

    def m(task):
        kwargs = task[1]
        try:
            yaml = YAML(typ="safe")
            kwargs["config"] = yaml.load(kwargs["config"])
        except KeyError:
            pass
        return task

    tasks = {k: m(v) for k, v in tasks.items()}
    return tasks, global_config
