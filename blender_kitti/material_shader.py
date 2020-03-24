# -*- coding: utf-8 -*-
""""""
from .bpy_helper import needs_bpy_bmesh


def make_nodes_simple_material(material, base_color):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    node_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    node_bsdf.inputs[0].default_value = base_color
    node_bsdf.inputs[7].default_value = 0.65  # roughness
    node_bsdf.inputs[12].default_value = 0.0  # clearcoat
    node_bsdf.inputs[13].default_value = 0.25  # clearcoat roughness
    node_bsdf.location = 0, 0

    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_output.location = 400, 0

    # link nodes
    links = material.node_tree.links
    links.new(node_bsdf.outputs[0], node_output.inputs[0])


def make_nodes_uv_mapped_material(material, color_image):
    assert color_image.size[1] == 1

    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    # create uv input node
    node_uv = nodes.new(type="ShaderNodeUVMap")
    node_uv.location = 0, 0
    node_uv.from_instancer = True
    node_uv.location = 0, 0
    node_sep = nodes.new(type="ShaderNodeSeparateXYZ")
    node_sep.location = 180, 0
    node_add_x = nodes.new(type="ShaderNodeMath")
    node_add_x.inputs[1].default_value = 0.5
    node_add_x.operation = "ADD"
    node_add_x.location = 360, 0
    node_add_y = nodes.new(type="ShaderNodeMath")
    node_add_y.inputs[1].default_value = 0.5
    node_add_y.operation = "ADD"
    node_add_y.location = 450, -200
    node_div_x = nodes.new(type="ShaderNodeMath")
    node_div_x.inputs[1].default_value = float(color_image.size[0])
    node_div_x.operation = "DIVIDE"
    node_div_x.location = 520, 0
    node_comb = nodes.new(type="ShaderNodeCombineXYZ")
    node_comb.inputs[2].default_value = 0.0
    node_comb.location = 700, 0

    node_text = nodes.new(type="ShaderNodeTexImage")
    node_text.interpolation = "Closest"
    node_text.extension = "CLIP"
    node_text.image = color_image
    node_text.location = 900, 0

    # mix point colors with simple black material
    node_mix_rgb = nodes.new(type="ShaderNodeMixRGB")
    node_mix_rgb.location = 1200, 0
    node_mix_rgb.inputs[0].default_value = 0.0  # all on vertex color
    node_mix_rgb.inputs[2].default_value = (0.01, 0.01, 0.01, 1.0)

    # create shader node
    node_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    node_bsdf.inputs[7].default_value = 0.65  # roughness
    node_bsdf.inputs[12].default_value = 0.0  # clearcoat
    node_bsdf.inputs[13].default_value = 0.25  # clearcoat roughness
    node_bsdf.location = 1500, 0

    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_output.location = 1800, 0

    # link nodes
    links = material.node_tree.links
    links.new(node_uv.outputs[0], node_sep.inputs[0])
    links.new(node_sep.outputs[0], node_add_x.inputs[0])
    links.new(node_sep.outputs[1], node_add_y.inputs[0])
    links.new(node_add_x.outputs[0], node_div_x.inputs[0])
    links.new(node_div_x.outputs[0], node_comb.inputs[0])
    links.new(node_add_y.outputs[0], node_comb.inputs[1])
    links.new(node_comb.outputs[0], node_text.inputs[0])
    links.new(node_text.outputs[0], node_mix_rgb.inputs[1])
    links.new(node_mix_rgb.outputs[0], node_bsdf.inputs[0])
    links.new(node_bsdf.outputs[0], node_output.inputs[0])


def make_nodes_vertex_color_material(
    material, vertex_color_layer_names: [str], default_color, mode: str = "select"
):

    if mode not in ["select", "mix"]:
        raise ValueError("Unknown vertex color mode '{}'.".format(mode))

    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    links = material.node_tree.links

    def create_attr_input_node(attribute_name: str):
        attr_node = nodes.new(type="ShaderNodeAttribute")
        attr_node.location = 0, 0
        attr_node.attribute_name = attribute_name
        return attr_node

    selector = None
    node_color = nodes.new(type="ShaderNodeMixRGB")

    if mode == "mix":

        # default color input node, if no vertex colors are given
        node_default_color = nodes.new(type="ShaderNodeRGB")
        node_default_color.outputs[0].default_value = default_color
        nodes_input_attrs = list(map(create_attr_input_node, vertex_color_layer_names))
        raise NotImplementedError()

    elif mode == "select":

        node_vertex_color = create_attr_input_node("dummy")

        # mix vertex colors with default color
        node_color.location = 200, 0
        node_color.inputs[0].default_value = 0.0  # vertex color
        node_color.inputs[1].default_value = 1.0, 1.0, 1.0, 1.0
        node_color.inputs[2].default_value = default_color

        links.new(node_vertex_color.outputs[0], node_color.inputs[1])

        def selector(index: int):
            if index < 0:
                # set to default color
                node_color.inputs[0].default_value = 1.0
                return
            else:
                node_color.inputs[0].default_value = 0.0
                node_vertex_color.attribute_name = vertex_color_layer_names[index]

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
    links.new(node_color.outputs[0], node_bsdf.inputs[0])
    links.new(node_bsdf.outputs[0], node_output.inputs[0])

    return selector


@needs_bpy_bmesh()
def create_or_get_material(name_material: str, *, bpy):
    try:
        return bpy.data.materials[name_material]
    except KeyError:
        return bpy.data.materials.new(name=name_material)


def create_simple_material(base_color, name_material: str):
    mat = create_or_get_material(name_material)
    make_nodes_simple_material(mat, base_color)
    return mat


def create_uv_mapped_material(color_image, name_material: str = "material_point_cloud"):
    mat = create_or_get_material(name_material)
    make_nodes_uv_mapped_material(mat, color_image)
    return mat


def create_vertex_color_material(
    vertex_color_layer_names: [str],
    default_color,
    mode: str = "select",
    name_material: str = "material_vertex_color",
):
    mat = create_or_get_material(name_material)
    selector = make_nodes_vertex_color_material(
        mat, vertex_color_layer_names, default_color, mode
    )
    return mat, selector
