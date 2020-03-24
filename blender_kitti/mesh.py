# -*- coding: utf-8 -*-
""""""
import numpy as np

from .bpy_helper import needs_bpy_bmesh


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
    vertex_colors: [np.ndarray] = (),
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

    # ### MATERIAL
    # Vertex color material
    mat = bpy.data.materials.new(name="VertexColorMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    # create attribute input node
    node_input = nodes.new(type="ShaderNodeAttribute")
    node_input.location = 0, 0
    node_input.attribute_name = "color_sem"

    # create attribute input node
    node_input_grads = nodes.new(type="ShaderNodeAttribute")
    node_input_grads.location = 0, -200
    node_input_grads.attribute_name = "color_grads"

    # mix vertex colors with simple reconstruction material
    node_mix_rgb = nodes.new(type="ShaderNodeMixRGB")
    node_mix_rgb.location = 200, 0
    node_mix_rgb.inputs[0].default_value = 0.0  # all on vertex color
    node_mix_rgb.inputs[2].default_value = (0.1, 0.1, 0.1, 1.0)

    # hue saturation value node
    node_color = nodes.new(type="ShaderNodeHueSaturation")
    node_color.inputs[0].default_value = 0.5
    node_color.inputs[1].default_value = 1.0
    node_color.inputs[4].default_value = (1.0, 1.0, 1.0, 1.0)

    node_rgb_sep = nodes.new(type="ShaderNodeSeparateRGB")

    node_grad_value_mult = nodes.new(type="ShaderNodeMath")
    node_grad_value_mult.inputs[1].default_value = 1.2
    node_grad_value_mult.operation = "MULTIPLY"

    # mix between sem colors and grad colors
    node_mix_semgrad = nodes.new(type="ShaderNodeMixRGB")
    node_mix_semgrad.location = 400, -150
    node_mix_semgrad.inputs[0].default_value = 0.0  # all on sem vertex color

    # create shader node
    node_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    node_bsdf.inputs[7].default_value = 0.65  # roughness
    node_bsdf.inputs[12].default_value = 1.0  # clearcoat
    node_bsdf.inputs[13].default_value = 0.50  # clearcoat roughness
    node_bsdf.location = 620, 0
    # create output node
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_output.location = 900, 0
    # link nodes
    links = mat.node_tree.links
    links.new(node_input.outputs[0], node_mix_rgb.inputs[1])
    links.new(node_mix_rgb.outputs[0], node_mix_semgrad.inputs[1])

    # old grad color
    # links.new(node_input_grads.outputs[0], node_mix_semgrad.inputs[2])
    # new grad color
    links.new(node_input_grads.outputs[0], node_rgb_sep.inputs[0])
    links.new(node_rgb_sep.outputs[0], node_grad_value_mult.inputs[0])
    links.new(node_grad_value_mult.outputs[0], node_color.inputs[2])
    links.new(node_color.outputs[0], node_mix_semgrad.inputs[2])

    links.new(node_mix_semgrad.outputs[0], node_bsdf.inputs[0])
    links.new(node_bsdf.outputs[0], node_output.inputs[0])

    # add material to object
    obj.data.materials.append(mat)

    return obj


def add_object_from_mesh(
    vertices: np.ndarray,
    triangles: np.ndarray,
    vertex_colors: [np.ndarray] = (),
    *,
    scene,
    name_prefix: str,
):
    obj = create_obj_from_mesh(
        vertices, triangles, vertex_colors, name_prefix=name_prefix
    )
    scene.colletions.objects.link(obj)
