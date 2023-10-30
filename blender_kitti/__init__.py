# -*- coding: utf-8 -*-

__author__ = """Christoph Rist"""
__email__ = "c.rist@posteo.de"

from .particles import add_voxels, add_point_cloud, add_flow_mesh, add_boxes
from .scene_setup import setup_scene, add_cameras_default
from .system_setup import setup_system
from .object_spotlight import add_spotlight_ground
from .cli import process_file
import numpy as np


__all__ = [
    "add_boxes",
    "add_voxels",
    "add_point_cloud",
    "add_cameras_default",
    "add_flow_mesh",
    "setup_scene",
    "setup_system",
    "add_spotlight_ground",
    "process_file",
]


def calc_distances(p0, points):
    return ((p0 - points) ** 2).sum(axis=1)


def furthest_point_sampling_thresh(pts, dist_thresh: float = 0.1):
    farthest_pts = []
    farthest_pts_idxs = []
    first_idx = np.random.randint(len(pts))
    farthest_pts_idxs.append(first_idx)
    farthest_pts.append(pts[first_idx])
    distances = calc_distances(farthest_pts[0], pts)
    while True:
        farthest_pt_idx = np.argmax(distances)
        if distances[farthest_pt_idx] < dist_thresh:
            break
        farthest_pts.append(pts[farthest_pt_idx])
        farthest_pts_idxs.append(farthest_pt_idx)
        distances = np.minimum(distances, calc_distances(farthest_pts[-1], pts))
    return np.stack(farthest_pts, axis=0), np.array(farthest_pts_idxs)


