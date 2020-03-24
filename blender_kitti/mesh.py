# -*- coding: utf-8 -*-
""""""
import numpy as np

from .bpy_helper import needs_bpy_bmesh
from .material_shader import create_vertex_color_material


@needs_bpy_bmesh()
def create_mesh(
    vertices: np.ndarray,
    triangles: np.ndarray,
    vertex_colors: [np.ndarray] = (),
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

    # Create vertex color layer and set values
    # Todo
    # vcol_lay = mesh.vertex_colors.new(name="color_sem")
    # vcol_lay.data.foreach_set("color", vertex_colors)
    #
    # vcol_grad = mesh.vertex_colors.new(name="color_grads")
    # vcol_grad.data.foreach_set("color", mesh_vertex_color)

    mesh.update()
    mesh.validate()
    return mesh


@needs_bpy_bmesh(run_anyway=True)
def create_obj_from_mesh(
    vertices: np.ndarray,
    triangles: np.ndarray,
    vertex_colors: {str: np.ndarray} = None,
    *,
    name_prefix: str,
    bpy,
):

    mesh = create_mesh(
        vertices, triangles, vertex_colors, name="{}_mesh".format(name_prefix)
    )

    obj_name = "{}_obj".format(name_prefix)
    if obj_name in bpy.data.objects:
        raise RuntimeError("Obj '{}' already exists.".format(obj_name))
    obj = bpy.data.objects.new(obj_name, mesh)

    if vertex_colors is None:
        vertex_color_layer_names = []
    else:
        vertex_color_layer_names = list(vertex_colors.keys())

    default_color = 0.0, 0.0, 0.0, 1.0  # black
    mat, selector = create_vertex_color_material(
        vertex_color_layer_names,
        default_color,
        mode='select',
        name_material="{}_material".format(name_prefix),
    )

    # Todo: handle multiple vertex color layers
    if vertex_colors is None:
        selector(-1)
    else:
        selector(0)

    obj.data.materials.append(mat)
    return obj


def add_object_from_mesh(
    vertices: np.ndarray,
    triangles: np.ndarray,
    vertex_colors: {str: np.ndarray} = None,
    *,
    scene,
    name_prefix: str,
):
    obj = create_obj_from_mesh(
        vertices, triangles, vertex_colors, name_prefix=name_prefix
    )
    scene.collection.objects.link(obj)
