# -*- coding: utf-8 -*-
"""

"""

try:
    import bpy
    import bmesh
except ImportError:
    bpy = None
    print("bpy module not available.")


def _create_ground_material(name: str = "ground_material"):
    if name in bpy.data.materials:
        raise RuntimeError("Material '{}' already exists".format(name))

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    node_tex_coord = nodes.new(type="ShaderNodeTexCoord")
    node_tex_coord.location = 0, 0

    node_vector_math = nodes.new(type="ShaderNodeVectorMath")
    node_vector_math.location = 200, 0
    node_vector_math.operation = "DISTANCE"
    node_vector_math.inputs[1].default_value = (0.5, 0.5, 1.0)

    node_scale_distance = nodes.new(type="ShaderNodeMath")
    node_scale_distance.inputs[1].default_value = 1.5
    node_scale_distance.operation = "MULTIPLY"
    node_scale_distance.location = 400, 0

    node_color_ramp = nodes.new(type="ShaderNodeValToRGB")
    node_color_ramp.location = 600, 0
    color_ramp = node_color_ramp.color_ramp
    color_ramp.color_mode = "RGB"
    color_ramp.interpolation = "EASE"
    assert len(color_ramp.elements) == 2
    color_ramp.elements[0].position = 0.27
    color_ramp.elements[0].alpha = 0.0
    color_ramp.elements[0].color = 0.0, 0.0, 0.0, 0.0
    color_ramp.elements[1].position = 0.69
    color_ramp.elements[1].alpha = 1.0
    color_ramp.elements[1].color = 1.0, 1.0, 1.0, 1.0

    node_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    node_bsdf.inputs[7].default_value = 0.92  # roughness
    node_bsdf.inputs[12].default_value = 0.0  # clearcoat
    node_bsdf.inputs[13].default_value = 0.25  # clearcoat roughness
    node_bsdf.location = 900, -100

    node_transparent = nodes.new(type="ShaderNodeBsdfTransparent")
    node_transparent.location = 1200, -200

    node_mix = nodes.new(type="ShaderNodeMixShader")
    node_mix.location = 1500, 0

    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_output.location = 1800, 0

    links = mat.node_tree.links
    links.new(node_tex_coord.outputs[0], node_vector_math.inputs[0])
    # for some reason it is outputs[1] for the vector math node (bug?)
    links.new(node_vector_math.outputs[1], node_scale_distance.inputs[0])
    links.new(node_scale_distance.outputs[0], node_color_ramp.inputs[0])
    links.new(node_color_ramp.outputs[1], node_mix.inputs[0])
    links.new(node_bsdf.outputs[0], node_mix.inputs[1])
    links.new(node_transparent.outputs[0], node_mix.inputs[2])
    links.new(node_mix.outputs[0], node_output.inputs[0])

    return mat


def create_ground(name_prefix: str = "ground"):
    diameter: float = 10.0
    height: float = 0.1
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=256,
        diameter1=diameter,
        diameter2=diameter,
        depth=height,
        calc_uvs=False,
    )

    me = bpy.data.meshes.new("mesh_{}".format(name_prefix))
    bm.to_mesh(me)
    bm.free()

    obj = bpy.data.objects.new("obj_{}".format(name_prefix), me)
    material = _create_ground_material("material_{}".format(name_prefix))
    obj.data.materials.append(material)
    return obj


def add_ground_and_lighting(scene=None, name_prefix: str = "spotlight"):
    if scene is None:
        scene = bpy.context.scene

    obj_ground = create_ground(name_prefix="{}_ground".format(name_prefix))

    scene.collection.objects.link(obj_ground)
