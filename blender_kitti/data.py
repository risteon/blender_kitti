# -*- coding: utf-8 -*-
""""""
import pathlib
import numpy as np
from ruamel.yaml import YAML


def unpack(compressed: np.ndarray):
    assert compressed.ndim == 1
    uncompressed = np.zeros(compressed.shape[0] * 8, dtype=np.bool)
    for b in range(8):
        uncompressed[b::8] = compressed >> (7 - b) & 1
    return uncompressed


def read_semantic_kitti_voxel_label(semantic_kitti_sample) -> {str: np.ndarray}:
    # compressed/uncompressed
    d = {'bin': True, 'invalid': True, 'label': False, 'occluded': True, }
    voxel_dims = (256, 256, 32)

    data = {}
    for k, compressed in d.items():
        filepath = semantic_kitti_sample.parent / (semantic_kitti_sample.stem + '.' + k)
        if not filepath.is_file():
            raise FileNotFoundError("Cannot find voxel label file '{}'.".format(k))

        if compressed:
            x = np.fromfile(str(filepath), dtype=np.uint8)
            x = unpack(x)
        else:
            x = np.fromfile(str(filepath), dtype=np.int16)
        x = x.reshape(voxel_dims)
        data[k] = x
    return data


def get_semantic_kitti_voxels():

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

    semantic_kitti_sample = pathlib.Path(__file__).parent.parent / 'data' \
        / 'voxel_label_kitti_odometry_08_001000'
    data = read_semantic_kitti_voxel_label(semantic_kitti_sample)
    voxel_label = np.vectorize(mapping.get, otypes=[np.int16])(data['label'])

    semantic_colors = np.asarray([list(color_bgr[k]) for k in learning_map.keys()], np.uint8)
    color_grid = semantic_colors[voxel_label]
    return data['label'] == 0, color_grid


if __name__ == '__main__':
    occupied, color = get_semantic_kitti_voxels()
