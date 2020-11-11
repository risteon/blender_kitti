# -*- coding: utf-8 -*-
""""""
import colorsys
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
    d = {
        "bin": True,
        "invalid": True,
        "label": False,
        "occluded": True,
    }
    voxel_dims = (256, 256, 32)

    data = {}
    for k, compressed in d.items():
        filepath = semantic_kitti_sample.parent / (semantic_kitti_sample.stem + "." + k)
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


def get_semantic_kitti_config():
    file_config_semantic = (
        pathlib.Path(__file__).parent.parent / "data" / "config" / "semantic-kitti.yaml"
    )
    if not file_config_semantic.is_file():
        raise FileNotFoundError("Cannot find semantic kitti config file.")

    # read config
    with open(str(file_config_semantic), "r") as file_conf_sem:
        yaml = YAML()
        data = yaml.load(file_conf_sem)
        config_data = {k: dict(v) for k, v in data.items()}
    return config_data


def get_semantic_kitti_voxels():
    config_data = get_semantic_kitti_config()

    color_bgr = dict(config_data["color_map"])
    learning_map = dict(config_data["learning_map"])

    mapping = {k: v for k, v in zip(learning_map.keys(), range(len(learning_map)))}

    semantic_kitti_sample = (
        pathlib.Path(__file__).parent.parent
        / "data"
        / "voxel_label_kitti_odometry_08_001000"
    )
    data = read_semantic_kitti_voxel_label(semantic_kitti_sample)
    voxel_label = np.vectorize(mapping.get, otypes=[np.int16])(data["label"])

    semantic_colors = np.asarray(
        [list(color_bgr[k]) for k in learning_map.keys()], np.uint8
    )
    # BGR -> RGB
    semantic_colors = semantic_colors[..., ::-1]
    color_grid = semantic_colors[voxel_label]
    return data["label"] != 0, color_grid


def get_semantic_kitti_point_cloud():

    file_point_cloud = (
        pathlib.Path(__file__).parent.parent
        / "data"
        / "velodyne_kitti_odometry_08_001000.bin"
    )
    if not file_point_cloud.is_file():
        raise FileNotFoundError("Cannot find kitti point cloud file.")

    file_semantic_label = (
        pathlib.Path(__file__).parent.parent
        / "data"
        / "semantic_label_kitti_odometry_08_001000.label"
    )
    if not file_semantic_label.is_file():
        raise FileNotFoundError("Cannot find semantic kitti label file.")

    config_data = get_semantic_kitti_config()
    point_cloud = np.fromfile(str(file_point_cloud), dtype=np.float32).reshape(
        (
            -1,
            4,
        )
    )
    label = np.fromfile(str(file_semantic_label), dtype=np.uint32).reshape((-1,))
    label_sem = label & 0xFFFF  # semantic label in lower half
    label_inst = label >> 16  # instance id in upper half
    # sanity check
    assert (label_sem + (label_inst << 16) == label).all()

    color_bgr = dict(config_data["color_map"])
    learning_map = dict(config_data["learning_map"])
    mapping = {k: v for k, v in zip(learning_map.keys(), range(len(learning_map)))}
    semantic_colors = np.asarray(
        [list(color_bgr[k]) for k in learning_map.keys()], np.uint8
    )
    # BGR -> RGB
    semantic_colors = semantic_colors[..., ::-1]

    label = np.vectorize(mapping.get, otypes=[np.int16])(label_sem)
    colors = semantic_colors[label]
    return point_cloud[:, :3], colors


def get_pseudo_flow(point_cloud):

    points_homog = np.concatenate(
        [point_cloud, np.ones((point_cloud.shape[0], 1))], axis=-1
    )

    rot_angle = np.pi / 32.0
    ca = np.cos(rot_angle)
    sa = np.sin(rot_angle)
    rot_homog = np.eye(4)
    rot_homog[0, 0] = ca
    rot_homog[0, 1] = -sa
    rot_homog[1, 0] = sa
    rot_homog[1, 1] = ca

    rot_around_y = 5.0
    transl_homog = np.eye(4)
    transl_homog_reverse = np.eye(4)
    transl_homog[1, 3] = rot_around_y
    transl_homog_reverse[1, 3] = -rot_around_y

    odom = np.matmul(transl_homog, np.matmul(rot_homog, transl_homog_reverse))

    odom[0, 3] = -1.0

    flow = ((np.matmul(odom, points_homog.T) - points_homog.T).T)[..., 0:3]

    colors_hsv = np.ones_like(flow)

    flow_azi = np.arctan2(flow[..., 1], flow[..., 0])
    colors_hsv[..., 0] = np.fmod(flow_azi + np.pi, 2 * np.pi) / (2 * np.pi)

    colors = []
    for color in colors_hsv:
        colors.append(colorsys.hsv_to_rgb(color[0], color[1], color[2]))
    colors_rgb = np.array(colors)
    colors_rgba = np.concatenate(
        [
            colors_rgb,
            0.3 * np.ones(colors_rgb.shape[0])[..., None],
        ],
        axis=-1,
    ).astype(np.float32)
    return flow, colors_rgba
