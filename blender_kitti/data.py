# -*- coding: utf-8 -*-
""""""
import pathlib
import numpy as np
from ruamel.yaml import YAML


def read_semantic_kitti_voxel_label(filepath):
    voxel_dims = (256, 256, 32)
    label = np.fromfile(str(filepath), dtype=np.int16)
    label = label.reshape(voxel_dims)
    return label


def get_semantic_kitti_voxels():


    file_voxel_label = pathlib.Path(__file__).parent.parent / 'data' \
        / 'voxel_label_kitti_odometry_08_001000.label'
    if not file_voxel_label.is_file():
        raise FileNotFoundError("Cannot find voxel label file.")

    file_config_semantic = pathlib.Path(__file__).parent.parent / 'config' / 'semantic-kitti.yaml'
    if not file_config_semantic.is_file():
        raise FileNotFoundError("Cannot find semantic kitti config file.")

    # read config
    with open(str(file_config_semantic), 'r') as file_conf_sem:
        yaml = YAML()
        data = yaml.load(file_conf_sem)
        config_data = {k: dict(v) for k, v in data.items()}

    color_bgr = dict(config_data['color_map'])
    learning_map = dict(config_data['learning_map'])
    learning_map_inv = dict(config_data['learning_map_inv'])

    mapping = {k: v for k, v in zip(learning_map.keys(), range(len(learning_map)))}

    voxel_label = read_semantic_kitti_voxel_label(file_voxel_label)
    voxel_label = np.vectorize(mapping.get, otypes=[np.int16])(voxel_label)

    semantic_colors = np.asarray([list(color_bgr[k]) for k in learning_map.keys()], np.uint8)

    color_grid = semantic_colors[voxel_label]


if __name__ == '__main__':
    get_semantic_kitti_voxels()
