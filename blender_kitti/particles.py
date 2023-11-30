# -*- coding: utf-8 -*-
""""""
import typing
import logging
import numpy as np

import bpy
import bmesh

from .material_shader import (
    create_flow_material,
    create_simple_material,
    create_uv_mapped_material,
    add_nodes_to_material,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def _create_instancer_mesh(positions: np.ndarray, name="mesh_points"):
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


def _create_instancer_obj(
    positions: np.ndarray, name_instancer_obj: str, name_mesh: str
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


def _create_color_image(colors_rgba: np.ndarray, name: str):
    assert colors_rgba.ndim == 2
    # dtype and alpha channel checks
    if colors_rgba.dtype == np.float32:
        pass
    elif colors_rgba.dtype == np.uint8:
        colors_rgba = colors_rgba.astype(np.float32) / 255.0
    else:
        raise NotImplementedError(
            "Cannot handle colors_rgba with dtype {}.".format(str(colors_rgba.dtype))
        )
    if colors_rgba.shape[1] == 3:
        colors_rgba = np.concatenate(
            (colors_rgba, np.ones_like(colors_rgba[:, :1])), axis=-1
        )
    elif colors_rgba.shape[1] == 4:
        pass
    else:
        raise NotImplementedError(
            "Cannot handle colors_rgba with shape {}.".format(colors_rgba.shape)
        )
    assert colors_rgba.shape[1] == 4

    if name in bpy.data.images:
        raise RuntimeError("Image '{}' already exists.".format(name))
    image = bpy.data.images.new(name, len(colors_rgba), 1, alpha=True)

    colors_rgba = colors_rgba.reshape((-1))
    image.pixels = [a for a in colors_rgba]
    # super important. Otherwise the pixel data will just vanish from memory and be
    # lost for certain after saving + loading the file.
    image.pack()
    return image


def _create_particle_instancer(
    name_prefix: str,
    positions: np.ndarray,
    obj_particle,
):
    # created entities
    name_mesh = "{}_mesh".format(name_prefix)
    name_obj = "{}_obj_instancer".format(name_prefix)

    obj_instancer = _create_instancer_obj(positions, name_obj, name_mesh)

    obj_particle.parent = obj_instancer
    # instancing from 'fake' faces is necessary for uv mapping to work.
    obj_instancer.instance_type = "FACES"
    obj_instancer.show_instancer_for_render = False
    return obj_instancer


def _add_material_to_particle(name_prefix, colors, obj_particle, material=None):
    """

    :param name_prefix:
    :param colors:
    :param obj_particle:
    :return:
    """

    name_image = "{}_colors".format(name_prefix)
    name_material = "{}_material".format(name_prefix)

    if colors is not None:
        if isinstance(colors, np.ndarray):
            colors = [colors]
            name_image = [name_image]
            name_material = [name_material]
        else:
            name_image = [f"{name_image}_{i}" for i in range(len(colors))]
            name_material = [f"{name_material}_{i}" for i in range(len(colors))]

        color_selector = []
        for color_arr, ni, nm in zip(colors, name_image, name_material):
            image = _create_color_image(color_arr, ni)
            if material is None:
                # the particle obj will use this material
                logger.info(f"Creating material {ni}.")
                _material, _cs = create_uv_mapped_material(image, nm)
            else:
                # Todo (risteon) does return color link, not color selector
                _cs = add_nodes_to_material(material, image)
                _material = material

            obj_particle.data.materials.append(_material)
            color_selector.append(_cs)
    else:
        material, color_selector = create_simple_material(
            base_color=(0.1, 0.1, 0.1, 1.0), name_material=name_material
        )
        obj_particle.data.materials.append(material)

    return color_selector


def create_cube(name_prefix: str, *, edge_length: float = 0.16):
    bm = bmesh.new()
    bmesh.ops.create_cube(
        bm,
        size=edge_length,
        calc_uvs=False,
    )

    me = bpy.data.meshes.new("{}_mesh".format(name_prefix))
    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new("{}_obj".format(name_prefix), me)
    return obj


def create_icosphere(
    name_prefix: str,
    *,
    subdivisions: int = 3,
    radius: float = 0.02,
    use_smooth: bool = True,
):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(
        bm,
        subdivisions=subdivisions,
        radius=radius,
        calc_uvs=False,
    )

    mesh = bpy.data.meshes.new("{}_mesh".format(name_prefix))
    bm.to_mesh(mesh)
    bm.free()

    mesh.polygons.foreach_set(
        "use_smooth",
        np.full(fill_value=use_smooth, shape=[len(mesh.polygons)], dtype=np.bool),
    )

    obj = bpy.data.objects.new("{}_obj".format(name_prefix), mesh)
    return obj


def create_voxel_particle_obj(
    coords: np.ndarray,
    colors: np.ndarray,
    name_prefix: str,
    scene,
    material=None,
):
    obj_particle = create_cube(name_prefix + "_cube")
    scene.collection.objects.link(obj_particle)

    obj_voxels, color_selector = _create_particle_instancer(
        name_prefix, coords, obj_particle
    )
    if scene is not None:
        scene.collection.objects.link(obj_voxels)

    color_selector = _add_material_to_particle(
        name_prefix, colors, obj_particle, material
    )
    return obj_voxels, color_selector


def add_voxels(
    scene,
    *,
    voxels: np.ndarray,
    colors: np.ndarray = None,
    name_prefix: str = "voxels",
    material=None,
):
    """

    :param voxels: boolean array marking occupancy
    :param colors:
    :param name_prefix:
    :param scene:
    :param material:
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
        coords, colors, name_prefix, scene, material
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
    """"""
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
    scene,
    *,
    points: np.ndarray,
    colors: np.ndarray = None,
    reflectivity: np.ndarray = None,
    row_splits: np.ndarray = None,
    name_prefix: str = "point_cloud",
    particle_radius: float = 0.02,
    material=None,
    particle_obj=None,
):
    """

    :param scene:
    :param points:
    :param colors:
    :param reflectivity:
    :param row_splits:
    :param name_prefix:
    :param particle_radius:
    :param material: If given, just add nodes to this material
    :param particle_obj: If given, use this object
    :return:
    """
    if particle_obj is None:
        # created entities
        obj_particle = create_icosphere(
            name_prefix + "_icosphere", radius=particle_radius
        )
        scene.collection.objects.link(obj_particle)
    else:
        obj_particle = particle_obj

    obj_point_cloud = _create_particle_instancer(name_prefix, points, obj_particle)
    scene.collection.objects.link(obj_point_cloud)
    color_selector = _add_material_to_particle(
        name_prefix, colors, obj_particle, material
    )

    return (
        obj_point_cloud,
        {"color_selector": color_selector, "obj_particle": obj_particle},
    )


def read_verts(mesh):
    mverts_co = np.zeros((len(mesh.vertices) * 3), dtype=np.float)
    mesh.vertices.foreach_get("co", mverts_co)
    return np.reshape(mverts_co, (len(mesh.vertices), 3))


def apply_trafo(points, trafo):
    return np.matmul(trafo, points.T).T


# adapted from https://blender.stackexchange.com/a/80592
def bmesh_join(list_of_bmeshes, list_of_matrices, *, normal_update=False, bmesh):
    """takes as input a list of bm references and outputs a single merged bmesh
    allows an additional 'normal_update=True' to force _normal_ calculations.
    """

    bm = bmesh.new()
    add_vert = bm.verts.new
    add_face = bm.faces.new
    add_edge = bm.edges.new

    for bm_to_add, matrix in zip(list_of_bmeshes, list_of_matrices):
        bm_to_add.transform(matrix)
        offset = len(bm.verts)

        for v in bm_to_add.verts:
            add_vert(v.co)

        bm.verts.index_update()
        bm.verts.ensure_lookup_table()

        if bm_to_add.faces:
            for face in bm_to_add.faces:
                add_face(tuple(bm.verts[i.index + offset] for i in face.verts))
            bm.faces.index_update()

        if bm_to_add.edges:
            for edge in bm_to_add.edges:
                edge_seq = tuple(bm.verts[i.index + offset] for i in edge.verts)
                try:
                    add_edge(edge_seq)
                except ValueError:
                    # edge exists!
                    pass
            bm.edges.index_update()

    if normal_update:
        bm.normal_update()

    return bm


def simple_scale_matrix(factor: np.array, direction: np.array):
    dir_len = np.sqrt(np.sum(direction**2))
    assert dir_len > 0.0, "direction vector of scale matrix may not have length zero"
    normalized_dir = direction / dir_len
    factor = 1.0 - factor
    scale_matrix = np.eye(4)
    scale_matrix[:3, :3] -= factor * np.einsum(
        "i,j->ij", normalized_dir.ravel(), normalized_dir.ravel()
    )
    return scale_matrix


def add_flow_mesh(
    *,
    point_cloud: np.ndarray,
    flow: np.ndarray,
    colors_rgba: np.ndarray = None,
    name_prefix: str = "flow",
    arrow_shaft_diameter: float = 0.05,
    arrow_shaft_length: float = 1.0,
    arrow_head_height: float = 0.2,
    arrow_head_diameter: float = 0.15,
    scene,
    mathutils,
):
    if point_cloud.dtype != np.float32:
        print(
            "Warning: dtype of point_cloud should be np.float32. Casting to np.float32"
        )
        point_cloud = point_cloud.astype(np.float32)

    if flow.dtype != np.float32:
        print("Warning: dtype of flow should be np.float32. Casting to np.float32")
        flow = flow.astype(np.float32)

    if colors_rgba.dtype != np.float32:
        print(
            "Warning: dtype of colors_rgba should be np.float32. Casting to np.float32"
        )
        colors_rgba = colors_rgba.astype(np.float32)

    # arrow shaft
    arrow_shaft = bmesh.new()
    bmesh.ops.create_cone(
        arrow_shaft,
        cap_ends=True,
        cap_tris=False,
        segments=10,
        diameter1=arrow_shaft_diameter,
        diameter2=arrow_shaft_diameter,
        depth=arrow_shaft_length,
        calc_uvs=False,
    )

    # arrow head
    arrow_head = bmesh.new()
    bmesh.ops.create_cone(
        arrow_head,
        cap_ends=True,
        cap_tris=False,
        segments=10,
        diameter1=arrow_head_diameter,
        diameter2=0.0,
        depth=arrow_head_height,
        calc_uvs=False,
    )

    arrow_mesh = bmesh_join(
        list_of_bmeshes=[arrow_shaft, arrow_head],
        list_of_matrices=[
            mathutils.Matrix.Translation((0.0, 0.0, 0.5)),
            mathutils.Matrix.Translation((0.0, 0.0, 1.0)),
        ],
        normal_update=False,
        bmesh=bmesh,
    )

    assert colors_rgba.shape[1] == 4
    assert colors_rgba.dtype == np.float32
    assert np.all(np.logical_and(0.0 <= colors_rgba, colors_rgba <= 1.0))

    me = bpy.data.meshes.new("mesh_{}".format(name_prefix))
    arrow_mesh.to_mesh(me)
    arrow_head.free()
    arrow_shaft.free()
    arrow_mesh.free()

    polygons = me.polygons
    npolygons = len(polygons)
    nloops = len(me.loops)

    startloop = np.empty(npolygons, dtype=np.int)
    loop_total = np.empty(npolygons, dtype=np.int)
    polygon_indices = np.empty(npolygons, dtype=np.int)

    polygons.foreach_get("index", polygon_indices)
    polygons.foreach_get("loop_start", startloop)
    polygons.foreach_get("loop_total", loop_total)

    vertex_index = np.empty(nloops, dtype=np.int)
    me.loops.foreach_get("vertex_index", vertex_index)
    assert sum(loop_total) == len(vertex_index)
    mesh_verts = read_verts(me)
    # dann gather mit vertex indices

    num_flow_vecs = flow.shape[0]
    flow_len = np.linalg.norm(flow, axis=-1)

    vertices_homog = np.concatenate(
        [mesh_verts, np.ones((mesh_verts.shape[0], 1))], axis=-1
    )

    full_vertices = []
    vertex_indices = []
    loop_start = []
    loop_total = np.tile(loop_total, num_flow_vecs)

    assert point_cloud.shape == flow.shape
    for flow_vec_idx in range(num_flow_vecs):
        arrow_head_unit = np.array([0.0, 0.0, 1.0])
        scale_mat = simple_scale_matrix(
            flow_len[flow_vec_idx], np.array([0.0, 0.0, 1.0])
        )
        vert_scaled = apply_trafo(np.copy(vertices_homog), scale_mat)

        flow_vec = flow[flow_vec_idx]

        flow_vec_unit = flow_vec / np.sqrt(np.sum(flow_vec**2))

        # rotation matrix R that rotates unit vector a onto unit vector b.
        v = np.cross(arrow_head_unit, flow_vec_unit)
        cosine = np.dot(arrow_head_unit, flow_vec_unit)

        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = np.eye(3) + vx + np.dot(vx, vx) * 1.0 / (1.0 + cosine)
        T_rot = np.eye(4)
        T_rot[0:3, 0:3] = R
        vert_rotated = apply_trafo(vert_scaled, T_rot)

        translation_matrix = np.eye(4)
        translation_matrix[:3, 3] = point_cloud[flow_vec_idx][:3]

        vert_translated = apply_trafo(vert_rotated, translation_matrix)

        vert_final = vert_translated[..., 0:3]

        full_vertices.append(vert_final)
        shifted_start = startloop + flow_vec_idx * nloops
        loop_start.append(shifted_start)
        shifted_vertex_indices = vertex_index + flow_vec_idx * len(mesh_verts)
        vertex_indices.append(shifted_vertex_indices)

    vertex_indices = np.concatenate(vertex_indices, axis=0)

    full_vertices = np.concatenate(full_vertices, axis=0)
    loop_start = np.concatenate(loop_start, axis=0)

    assert sum(loop_total) == len(vertex_indices)
    assert loop_total.shape == loop_start.shape

    assert npolygons * num_flow_vecs == len(loop_start)
    assert npolygons * num_flow_vecs == len(loop_total)

    assert np.all(np.diff(loop_start) == loop_total[:-1])

    mesh = bpy.data.meshes.new(name="flow_mesh")
    # vertices
    mesh.vertices.add(full_vertices.shape[0])
    mesh.vertices.foreach_set("co", full_vertices.astype(np.float32).reshape((-1)))

    # vertex indices
    mesh.loops.add(vertex_indices.shape[0])
    mesh.loops.foreach_set("vertex_index", vertex_indices)

    # triangles
    mesh.polygons.add(loop_start.shape[0])
    mesh.polygons.foreach_set("loop_start", loop_start)
    mesh.polygons.foreach_set("loop_total", loop_total)

    colors_per_vertex_index_colors_rgba = np.tile(
        colors_rgba[:, None, :], reps=[1, len(mesh_verts), 1]
    )
    colors_flattened = np.reshape(colors_per_vertex_index_colors_rgba, (-1, 4))

    colors_per_vertex_index = colors_flattened[vertex_indices]
    # Create vertex color layer and set values
    vcol_lay = mesh.vertex_colors.new(name="color_flow")
    color_verts = np.reshape(colors_per_vertex_index, (-1))
    vcol_lay.data.foreach_set("color", color_verts)

    vcol_grad = mesh.vertex_colors.new(name="color_grads")
    vcol_grad.data.foreach_set("color", color_verts)

    mesh.update()
    mesh.validate()

    obj = bpy.data.objects.new("obj_{}".format(name_prefix), mesh)
    material = create_flow_material("material_{}".format(name_prefix))
    obj.data.materials.append(material)

    # baurst: very unsure about this
    if scene is not None:
        scene.collection.objects.link(obj)

    return obj


def create_cube_with_wireframe(
    position: np.ndarray,
    scale: np.ndarray,
    rotation: np.ndarray,
    wireframe_scale: float,
    color: np.ndarray,
):
    # create a mesh cube
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cube_add(
        size=1, enter_editmode=False, align="WORLD", location=position
    )
    cube = bpy.context.object

    # set scale and rotation
    cube.scale = scale
    cube.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # add wireframe modifier
    bpy.ops.object.modifier_add(type="WIREFRAME")
    wireframe_modifier = cube.modifiers[-1]
    wireframe_modifier.thickness = wireframe_scale

    # create a new material with the given color
    material = bpy.data.materials.new(name="CubeMaterial")
    material.use_nodes = False
    material.diffuse_color = color

    # assign the material to the cube
    if len(cube.data.materials) > 0:
        cube.data.materials[0] = material
    else:
        cube.data.materials.append(material)

    return cube


def add_boxes(
    *,
    scene,
    boxes: typing.Dict[str, np.ndarray],
    box_colors_rgba_f64: np.ndarray,
    confidence_threshold: float = 0.0,
    bounding_box_wire_frame_scale: float = 0.2,
    verbose: bool = False,
):
    """
    supports only boxes with yaw rotation

    scene: blender py scene
    boxes: dictionairy with
        * 'pos': np.ndarray with shape [num_boxes, 3] (i.e. box positions in 3d)
        * 'rot': np.ndarray with shape [num_boxes, 1] (i.e. box yaw angles)
        * 'dims': np.ndarray with shape [num_boxes, 3] (i.e. box size length, width, height)
        * 'probs': np.ndarray with shape [num_boxes, 1] (i.e. box confidence)
    box_colors_rgba_f64: np.ndarray with shape [num_boxes, 4], i.e. a color for each box
    confidence_threshold: boxes below this threshold are discarded
    bounding_box_wire_frame_scale: this is the thickness of the box wireframe (in meters I think)
    """

    assert "pos" in boxes, "need box positions with key 'pos' to work!"
    assert "dims" in boxes, "need box dimensions with key 'dims' to work!"
    assert "rot" in boxes, "need box rotations (yaw angle) with key 'rot' to work!"

    assert (
        box_colors_rgba_f64 <= 1.0
    ).all(), "this code is only tested with f64 colors <= 1.0!"

    num_boxes = boxes["pos"].shape[0]
    for box_idx in range(num_boxes):
        box_confidence = np.squeeze(boxes["probs"][box_idx])
        if box_confidence < confidence_threshold:
            if verbose:
                print(f"Discarding box #{box_idx} with confidence {box_confidence}")
            continue
        if verbose:
            print(
                f"Add box #{box_idx} at position: ",
                boxes["pos"][box_idx],
                ", rotation: ",
                boxes["rot"][box_idx],
                f", confidence: {box_confidence}",
            )
        cube = create_cube_with_wireframe(
            position=boxes["pos"][box_idx],
            scale=boxes["dims"][box_idx],
            rotation=(
                0.0,
                0.0,
                boxes["rot"][box_idx],
            ),
            wireframe_scale=bounding_box_wire_frame_scale,
            color=box_colors_rgba_f64[box_idx],
        )
        scene.collection.objects.link(cube)
