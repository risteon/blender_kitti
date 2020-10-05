# -*- coding: utf-8 -*-
""""""
import typing
import logging
import numpy as np

from .bpy_helper import needs_bpy_bmesh
from .material_shader import create_simple_material, create_uv_mapped_material


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


@needs_bpy_bmesh()
def _create_instancer_mesh(positions: np.ndarray, name="mesh_points", *, bpy):
    """Create mesh with where each point is a pseudo face
    (three vertices at the same position.
    """
    assert positions.ndim == 2
    assert positions.shape[1] == 3

    if name in bpy.data.meshes:
        raise RuntimeError("Mesh '{}' already exists.".format(name))
    mesh = bpy.data.meshes.new(name=name)

    num_vertices = len(positions)
    mesh.vertices.add(num_vertices * 3)
    mesh.vertices.foreach_set("co", np.repeat(positions, 3, axis=0).reshape((-1)))
    mesh.loops.add(num_vertices * 3)
    mesh.loops.foreach_set("vertex_index", np.arange(0, 3 * num_vertices))

    loop_start = np.arange(0, 3 * num_vertices, 3, np.int32)
    loop_total = np.full(fill_value=3, shape=(num_vertices,), dtype=np.int32)
    num_loops = loop_start.shape[0]

    mesh.polygons.add(num_loops)
    mesh.polygons.foreach_set("loop_start", loop_start)
    mesh.polygons.foreach_set("loop_total", loop_total)

    mesh.update()
    mesh.validate()

    logger.info("Created instancer mesh with {} vertices.".format(len(positions)))

    return mesh


@needs_bpy_bmesh()
def _create_instancer_obj(
    positions: np.ndarray, name_instancer_obj: str, name_mesh: str, *, bpy
):
    assert positions.ndim == 2 and positions.shape[1] == 3

    if name_instancer_obj in bpy.data.objects:
        raise RuntimeError("Object '{}' already exists.".format(name_instancer_obj))

    mesh = _create_instancer_mesh(positions, name_mesh)

    vert_uvs = np.repeat(np.arange(0, len(mesh.vertices)), 3, axis=0)
    # add zero y coordinate
    vert_uvs = np.stack((vert_uvs, np.zeros_like(vert_uvs)), axis=-1)
    mesh.uv_layers.new(name="per_vertex_dummy_uv")
    mesh.uv_layers[-1].data.foreach_set(
        "uv",
        [
            uv
            for pair in [vert_uvs[loop.vertex_index] for loop in mesh.loops]
            for uv in pair
        ],
    )

    obj_instancer = bpy.data.objects.new(name_instancer_obj, mesh)
    return obj_instancer


@needs_bpy_bmesh()
def _create_color_image(colors: np.ndarray, name: str, alpha: bool = True, *, bpy):
    # dtype and alpha channel checks
    if colors.dtype == np.float32:
        pass
    elif colors.dtype == np.uint8:
        colors = colors.astype(np.float32) / 255.0
    else:
        raise NotImplementedError(
            "Cannot handle colors_rgba with dtype {}.".format(str(colors.dtype))
        )

    if colors.ndim != 3:
        raise ValueError("Wrong number of dimensions.")
    if colors.shape[2] not in [3, 4]:
        raise ValueError(
            "Cannot handle colors array with shape {}.".format(colors.shape)
        )

    if colors.shape[2] == 3:
        colors = np.concatenate((colors, np.ones_like(colors[:, :, :1])), axis=-1)
    elif colors.shape[2] == 4:
        pass

    if name in bpy.data.images:
        raise RuntimeError("Image '{}' already exists.".format(name))
    image = bpy.data.images.new(
        name, width=colors.shape[1], height=colors.shape[0], alpha=alpha
    )
    image.pixels = colors.ravel()
    # super important. Otherwise the pixel data will just vanish from memory and be
    # lost after saving + loading the file.
    image.pack()
    return image


def _create_particle_instancer(
    name_prefix: str,
    positions: np.ndarray,
    colors: typing.Union[None, np.ndarray],
    obj_particle,
):
    # created entities
    name_mesh = "{}_mesh".format(name_prefix)
    name_obj = "{}_obj_instancer".format(name_prefix)
    name_image = "{}_colors".format(name_prefix)
    name_material = "{}_material".format(name_prefix)

    obj_instancer = _create_instancer_obj(positions, name_obj, name_mesh)

    if colors is not None:
        image = _create_color_image(colors[None, :, :], name_image)
        # the particle obj will use this material
        material, color_selector = create_uv_mapped_material(image, name_material)
    else:
        material, color_selector = create_simple_material(
            base_color=(0.1, 0.1, 0.1, 1.0), name_material=name_material
        )

    obj_particle.parent = obj_instancer
    # instancing from 'fake' faces is necessary for uv mapping to work.
    obj_instancer.instance_type = "FACES"
    obj_instancer.show_instancer_for_render = False

    obj_particle.data.materials.append(material)
    return obj_instancer, color_selector


@needs_bpy_bmesh()
def create_cube(name_prefix: str, *, edge_length: float = 0.16, bpy, bmesh):

    bm = bmesh.new()
    bmesh.ops.create_cube(
        bm, size=edge_length, calc_uvs=False,
    )

    me = bpy.data.meshes.new("{}_mesh".format(name_prefix))
    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new("{}_obj".format(name_prefix), me)
    return obj


@needs_bpy_bmesh()
def create_icosphere(
    name_prefix: str, *, subdivisions: int = 3, radius: float = 0.02, bpy, bmesh
):

    bm = bmesh.new()
    bmesh.ops.create_icosphere(
        bm, subdivisions=subdivisions, diameter=2.0 * radius, calc_uvs=False,
    )

    me = bpy.data.meshes.new("{}_mesh".format(name_prefix))
    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new("{}_obj".format(name_prefix), me)
    return obj


def create_voxel_particle_obj(
    coords: np.ndarray, colors: np.ndarray, name_prefix: str, scene
):
    obj_particle = create_cube(name_prefix + "_cube")
    scene.collection.objects.link(obj_particle)

    obj_voxels, color_selector = _create_particle_instancer(
        name_prefix, coords, colors, obj_particle
    )
    if scene is not None:
        scene.collection.objects.link(obj_voxels)
    return obj_voxels, color_selector


def add_voxels(
    *,
    voxels: np.ndarray,
    colors: np.ndarray = None,
    name_prefix: str = "voxels",
    scene,
):
    """

    :param voxels: boolean array marking occupancy
    :param colors:
    :param name_prefix:
    :param scene:
    :return:
    """
    assert voxels.ndim == 3
    assert voxels.dtype == np.bool

    dtype = np.float32
    deltas = np.asarray([0.2, 0.2, 0.2], dtype=dtype)

    coords = np.mgrid[[slice(x) for x in voxels.shape]].astype(dtype)
    coords = np.moveaxis(coords, 0, 3)
    coords *= deltas
    coords = coords[voxels]
    colors = colors[voxels]

    obj_voxels, color_selector = create_voxel_particle_obj(
        coords, colors, name_prefix, scene
    )
    return obj_voxels, {"color_selector": color_selector}


def add_voxel_list(
    *,
    indices: np.ndarray,
    grid_shape: np.ndarray,
    grid_origin: np.ndarray,
    voxel_size: np.ndarray,
    colors: np.ndarray = None,
    name_prefix: str = "voxel_list",
    scene,
):
    """

    """
    assert indices.ndim == 1
    assert grid_shape.ndim == 1
    assert indices.shape[0] == colors.shape[0]

    dtype = np.float32
    # cubic voxels
    deltas = np.repeat(voxel_size, 3)

    coords = np.mgrid[[slice(x) for x in grid_shape]].astype(dtype)
    coords = np.moveaxis(coords, 0, 3)
    coords *= deltas
    coords += grid_origin

    coords = coords.reshape([-1, 3])
    coords = coords[indices]

    obj_voxels, color_selector = create_voxel_particle_obj(
        coords, colors, name_prefix, scene
    )
    return obj_voxels, {"color_selector": color_selector}


def add_point_cloud(
    *,
    points: np.ndarray,
    colors: np.ndarray = None,
    reflectivity: np.ndarray = None,
    row_splits: np.ndarray = None,
    name_prefix: str = "point_cloud",
    scene,
    particle_radius: float = 0.02,
):
    # created entities
    obj_particle = create_icosphere(name_prefix + "_icosphere", radius=particle_radius)
    scene.collection.objects.link(obj_particle)

    obj_point_cloud, color_selector = _create_particle_instancer(
        name_prefix, points, colors, obj_particle
    )

    scene.collection.objects.link(obj_point_cloud)
    return obj_point_cloud, {"color_selector": color_selector}
