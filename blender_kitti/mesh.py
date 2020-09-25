# -*- coding: utf-8 -*-
""""""
import numpy as np

from .bpy_helper import needs_bpy_bmesh
from .material_shader import create_vertex_color_material


@needs_bpy_bmesh(run_anyway=True)
def create_mesh(
    vertices: np.ndarray,
    triangles: np.ndarray,
    vertex_colors: {str: np.ndarray} = None,
    face_colors: {str: np.ndarray} = None,
    use_smooth: bool = True,
    *,
    name: str,
    bpy,
):
    assert vertices.ndim == 2 and vertices.shape[1] == 3
    assert triangles.ndim == 2 and triangles.shape[1] == 3
    assert triangles.dtype in [np.int32, np.int64] and vertices.dtype in [
        np.float32,
        np.float64,
    ]

    # Vertices and edges (straightforward)
    num_vertices = vertices.shape[0]
    vertices = vertices.reshape((-1))
    vertex_index = triangles.reshape((-1))
    num_vertex_indices = vertex_index.shape[0]
    loop_start = np.arange(0, num_vertex_indices, 3, np.int32)
    loop_total = np.full(fill_value=3, shape=(num_vertex_indices // 3,), dtype=np.int32)
    num_loops = loop_start.shape[0]

    # Create mesh object based on the arrays above
    if name in bpy.data.meshes:
        raise RuntimeError("Mesh '{}' already exists.".format(name))
    mesh = bpy.data.meshes.new(name=name)

    mesh.vertices.add(num_vertices)
    mesh.vertices.foreach_set("co", vertices)

    mesh.loops.add(num_vertex_indices)
    mesh.loops.foreach_set("vertex_index", vertex_index)

    mesh.polygons.add(num_loops)
    mesh.polygons.foreach_set("loop_start", loop_start)
    mesh.polygons.foreach_set("loop_total", loop_total)
    mesh.polygons.foreach_set(
        "use_smooth",
        np.full(fill_value=use_smooth, shape=[len(mesh.polygons)], dtype=np.bool),
    )

    # Create vertex color layers and set values
    if vertex_colors is not None:
        add_vertex_color_layers(mesh, vertex_index, vertex_colors)

    if face_colors is not None:
        add_vertex_color_layers_from_face_colors(mesh, vertex_index, face_colors)

    mesh.update()
    mesh.validate()
    return mesh


def add_vertex_color_layers_from_face_colors(
    mesh, vertex_indices, face_colors: {str: np.ndarray}
):

    for fcolor_name, fcolors in face_colors.items():
        if (
            fcolors.dtype != np.uint8
            or fcolors.ndim != 2
            or fcolors.shape[-1] not in [3, 4]
        ):
            raise ValueError("Need vertex colors in RGB (0-255) uint8 format.")

        fcolors = fcolors.astype(np.float32) / 255.0
        if fcolors.shape[-1] == 3:
            fcolors = np.concatenate((fcolors, np.ones_like(fcolors[:, :1])), axis=-1)

        # repeat face colors 3 times (for each vertex)
        fcolors = np.repeat(fcolors, 3, axis=0)
        fcolors = np.reshape(fcolors, [-1])
        assert fcolors.shape[0] == 4 * vertex_indices.shape[0]

        vcol_lay = mesh.vertex_colors.new(name="fcolor_{}".format(fcolor_name))
        vcol_lay.data.foreach_set("color", fcolors)


def add_vertex_color_layers(mesh, vertex_indices, vertex_colors: {str: np.ndarray}):

    for vcolor_name, vcolors in vertex_colors.items():
        if (
            vcolors.dtype != np.uint8
            or vcolors.ndim != 2
            or vcolors.shape[-1] not in [3, 4]
        ):
            raise ValueError("Need vertex colors in RGB (0-255) uint8 format.")

        vcolors = vcolors.astype(np.float32) / 255.0
        if vcolors.shape[-1] == 3:
            vcolors = np.concatenate((vcolors, np.ones_like(vcolors[:, :1])), axis=-1)

        # replicate vertex colors for each triangle at a vertex
        vcolors = vcolors[vertex_indices]
        vcolors = vcolors.reshape([-1])
        assert vcolors.shape[0] == 4 * vertex_indices.shape[0]

        vcol_lay = mesh.vertex_colors.new(name="vcolor_{}".format(vcolor_name))
        vcol_lay.data.foreach_set("color", vcolors)


@needs_bpy_bmesh(run_anyway=True)
def create_obj_from_mesh(
    vertices: np.ndarray,
    triangles: np.ndarray,
    vertex_colors: {str: np.ndarray} = None,
    face_colors: {str: np.ndarray} = None,
    *,
    name_prefix: str,
    bpy,
):

    obj_name = "{}_obj".format(name_prefix)
    if obj_name in bpy.data.objects:
        raise RuntimeError("Obj '{}' already exists.".format(obj_name))

    mesh = create_mesh(
        vertices,
        triangles,
        vertex_colors,
        face_colors,
        name="{}_mesh".format(name_prefix),
    )
    obj = bpy.data.objects.new(obj_name, mesh)

    default_color = 0.0, 0.0, 0.0, 1.0  # black
    mat, select_vertex_color = create_vertex_color_material(
        list(mesh.vertex_colors.keys()),
        default_color,
        mode="select",
        name_material="{}_material".format(name_prefix),
    )

    # Todo: handle multiple vertex color layers
    if vertex_colors is None:
        select_vertex_color(-1)
    else:
        select_vertex_color(0)

    obj.data.materials.append(mat)
    return obj, select_vertex_color


def add_object_from_mesh(
    vertices: np.ndarray,
    triangles: np.ndarray,
    vertex_colors: {str: np.ndarray} = None,
    face_colors: {str: np.ndarray} = None,
    *,
    scene,
    name_prefix: str,
):
    obj, select_vertex_color = create_obj_from_mesh(
        vertices, triangles, vertex_colors, face_colors, name_prefix=name_prefix
    )

    scene.collection.objects.link(obj)
    return obj, {"vertex_color_selector": select_vertex_color}
