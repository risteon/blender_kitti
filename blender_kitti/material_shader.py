# -*- coding: utf-8 -*-
""""""
import typing

from .bpy_helper import needs_bpy_bmesh


class NodeRGBColorSelect:

    COLOR_BLACK = (0.0, 0.0, 0.0, 1.0)
    VALUES = {
        "input": 0.0,
        "default": 1.0,
        "mix": 0.5,
    }

    def __init__(
        self,
        nodes,
        *,
        default_color=COLOR_BLACK,
        input_color=COLOR_BLACK,
        location=(1200, 0),
    ):
        self.node = nodes.new(type="ShaderNodeMixRGB")
        self.node.location = location
        self.node.inputs[1].default_value = input_color
        self.node.inputs[2].default_value = default_color

        self.set("input")

    @property
    def color_input(self):
        return self.node.inputs[1]

    @property
    def color_output(self):
        return self.node.outputs[0]

    def set(self, value: typing.Union[float, str]):
        if isinstance(value, str):
            self.node.inputs[0].default_value = NodeRGBColorSelect.VALUES[value]
        else:
            self.node.inputs[0].default_value = value


class NodeOutput:
    """ Build a default shader/material node tree

    * Select between input color (some particle mapping) and unified default color
    * Select between principled shader output and dummy 'true'-color output
    """

    MODES = {"shader": 1.0, "truecolor": 0.0}

    def __init__(
        self,
        node_tree,
        *,
        default_color=NodeRGBColorSelect.COLOR_BLACK,
        input_color=NodeRGBColorSelect.COLOR_BLACK,
        location=(0, 0),
        input_color_link=None,
    ):
        self.base_location_x = location[0]
        self.base_location_y = location[1]

        self.node_rgb_color_select = NodeRGBColorSelect(
            node_tree.nodes,
            default_color=default_color,
            input_color=input_color,
            location=(self.base_location_x, self.base_location_y),
        )

        self.node_bsdf = node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
        self.node_bsdf.inputs[7].default_value = 0.65  # roughness
        self.node_bsdf.inputs[12].default_value = 0.0  # clearcoat
        self.node_bsdf.inputs[13].default_value = 0.25  # clearcoat roughness
        self.node_bsdf.location = self.base_location_x + 200, self.base_location_y

        self.node_mix_shader = node_tree.nodes.new(type="ShaderNodeMixShader")
        self.node_mix_shader.location = (
            self.base_location_x + 480,
            self.base_location_y + 70,
        )
        self.node_mix_shader.inputs[0].default_value = self.MODES["shader"]

        self.node_output = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
        self.node_output.location = self.base_location_x + 650, self.base_location_y

        # link nodes
        links = node_tree.links
        links.new(self.node_rgb_color_select.color_output, self.node_bsdf.inputs[0])
        links.new(
            self.node_rgb_color_select.color_output, self.node_mix_shader.inputs[1]
        )
        links.new(self.node_bsdf.outputs[0], self.node_mix_shader.inputs[2])
        links.new(self.node_mix_shader.outputs[0], self.node_output.inputs[0])

        if input_color_link is not None:
            links.new(input_color_link, self.node_rgb_color_select.color_input)

    def set(self, value: typing.Union[float, str]):
        return self.node_rgb_color_select.set(value)

    def mode(self, value: str):
        self.node_mix_shader.inputs[0].default_value = self.MODES[value]

    @property
    def color_input(self):
        return self.node_rgb_color_select.color_input


def make_nodes_simple_material(material, base_color):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    default_output_node = NodeOutput(
        material.node_tree, input_color=base_color, location=(0, 0)
    )

    return default_output_node


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

    # link nodes
    links = material.node_tree.links
    links.new(node_uv.outputs[0], node_sep.inputs[0])
    links.new(node_sep.outputs[0], node_add_x.inputs[0])
    links.new(node_sep.outputs[1], node_add_y.inputs[0])
    links.new(node_add_x.outputs[0], node_div_x.inputs[0])
    links.new(node_div_x.outputs[0], node_comb.inputs[0])
    links.new(node_add_y.outputs[0], node_comb.inputs[1])
    links.new(node_comb.outputs[0], node_text.inputs[0])

    default_output_node = NodeOutput(
        material.node_tree, input_color_link=node_text.outputs[0], location=(1200, 0)
    )
    return default_output_node


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

        def selector(desc: typing.Union[int, str]):
            if isinstance(desc, int):
                if desc < 0:
                    # set to default color
                    node_color.inputs[0].default_value = 1.0
                    return
                else:
                    node_color.inputs[0].default_value = 0.0
                    node_vertex_color.attribute_name = vertex_color_layer_names[desc]
            else:
                if desc not in vertex_color_layer_names:
                    raise ValueError("Vertex color names not found.")
                node_color.inputs[0].default_value = 0.0
                node_vertex_color.attribute_name = desc

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
    color_selector = make_nodes_simple_material(mat, base_color)
    return mat, color_selector


def create_uv_mapped_material(color_image, name_material: str = "material_point_cloud"):
    mat = create_or_get_material(name_material)
    color_selector = make_nodes_uv_mapped_material(mat, color_image)
    return mat, color_selector


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
