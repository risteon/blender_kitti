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
    scalar_values: {str: np.ndarray} = None,
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
    try:
        if name in bpy.data.meshes:
            raise RuntimeError("Mesh '{}' already exists.".format(name))
    except AttributeError:
        pass

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

    attr_keys_rgb = set()
    attr_keys_scalar = set()
    # Create vertex color layers and set values
    if vertex_colors is not None:
        attr_keys_rgb.update(add_vertex_color_layers(mesh, vertex_index, vertex_colors))

    if face_colors is not None:
        attr_keys_rgb.update(
            add_vertex_color_layers_from_face_colors(mesh, vertex_index, face_colors)
        )

    if scalar_values is not None:
        attr_keys_scalar.update(
            add_vertex_colors_from_scalar(mesh, vertex_index, scalar_values)
        )

    mesh.update()
    mesh.validate()
    return mesh, attr_keys_rgb, attr_keys_scalar


def add_vertex_color_layers_from_face_colors(
    mesh, vertex_indices, face_colors: {str: np.ndarray}
) -> {str}:
    vertex_attr_keys = set()
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

        attr_key = "fcolor_{}".format(fcolor_name)
        vcol_lay = mesh.vertex_colors.new(name=attr_key)
        vcol_lay.data.foreach_set("color", fcolors)
        vertex_attr_keys.add(attr_key)
    return vertex_attr_keys


def add_vertex_color_layers(
    mesh, vertex_indices, vertex_colors: {str: np.ndarray}
) -> {str}:

    vertex_attr_keys = set()
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

        attr_key = "vcolor_{}".format(vcolor_name)
        vertex_attr_keys.add(attr_key)
        vcol_lay = mesh.vertex_colors.new(name="vcolor_{}".format(vcolor_name))
        vcol_lay.data.foreach_set("color", vcolors)

    return vertex_attr_keys


def add_vertex_colors_from_scalar(
    mesh, vertex_indices, scalar_values: {str: np.ndarray}
) -> {str}:
    def add_values(v, name):
        colors = np.tile(v[:, None], reps=[1, 3])
        # add alpha
        colors = np.concatenate((colors, np.ones_like(colors[:, :1])), axis=-1)

        # replicate vertex colors for each triangle at a vertex
        colors = colors[vertex_indices]
        colors = colors.reshape([-1])
        assert colors.shape[0] == 4 * vertex_indices.shape[0]

        attr_key = "vcolor_{}".format(name)
        vcol_lay = mesh.vertex_colors.new(name=attr_key)
        vcol_lay.data.foreach_set("color", colors)
        return attr_key

    vertex_attr_keys = set()
    for scolor_name, s_values in scalar_values.items():
        if s_values.dtype != np.float32 or s_values.ndim != 1:
            raise ValueError("Need scalar values in [N] float32 format.")

        # Todo: learn how blender handles value ranges.
        # Todo: use something that is less random.
        value_ranges = [
            (0.0, 3.5),
        ]

        for r in value_ranges:
            values = (s_values - r[0]) / (r[1] - r[0])
            values = np.clip(values, 0.0, 1.0)
            vertex_attr_keys.add(
                add_values(values, "{}_{:.2f}_{:.2f}".format(scolor_name, r[0], r[1]))
            )

    return vertex_attr_keys


@needs_bpy_bmesh(run_anyway=True)
def create_obj_from_mesh(
    vertices: np.ndarray,
    triangles: np.ndarray,
    vertex_colors: {str: np.ndarray} = None,
    face_colors: {str: np.ndarray} = None,
    scalar_values: {str: np.ndarray} = None,
    *,
    name_prefix: str,
    bpy,
):

    obj_name = "{}_obj".format(name_prefix)
    try:
        if obj_name in bpy.data.objects:
            raise RuntimeError("Obj '{}' already exists.".format(obj_name))
    except AttributeError:
        pass

    mesh, attr_keys_rgb, attr_keys_scalar = create_mesh(
        vertices,
        triangles,
        vertex_colors,
        face_colors,
        scalar_values,
        name="{}_mesh".format(name_prefix),
    )
    obj = bpy.data.objects.new(obj_name, mesh)

    default_color = 0.0, 0.0, 0.0, 1.0  # black
    mat, select_vertex_color = create_vertex_color_material(
        list(attr_keys_rgb),
        list(attr_keys_scalar),
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
    scalar_values: {str: np.ndarray} = None,
    *,
    scene,
    name_prefix: str,
):
    obj, select_vertex_color = create_obj_from_mesh(
        vertices,
        triangles,
        vertex_colors,
        face_colors,
        scalar_values,
        name_prefix=name_prefix,
    )

    scene.collection.objects.link(obj)
    return obj, {"vertex_color_selector": select_vertex_color}
