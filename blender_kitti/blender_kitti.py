# -*- coding: utf-8 -*-
""""""

import bpy
import numpy as np


def _create_mesh(positions: np.ndarray, name='mesh_points'):
    assert positions.ndim == 2
    assert positions.shape[1] == 3

    num_vertices = len(positions)
    mesh = bpy.data.meshes.new(name=name)
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
    return mesh


def add_voxels(voxels: np.ndarray, colors_rgba: np.ndarray = None):
    assert voxels.ndim == 3

    dtype = np.float32
    deltas = np.asarray([.2, .2, .2], dtype=dtype)

    coords = np.mgrid[[slice(x) for x in voxels.shape]].astype(dtype)
    coords = np.moveaxis(coords, 0, 3)
    coords *= deltas
    coords = coords[voxels]

    mesh = _create_mesh(coords, 'voxel_centers')
    obj = bpy.data.objects.new('obj_voxels', mesh)
    scene = bpy.context.scene
    scene.collection.objects.link(obj)


def add_point_cloud(point_cloud: np.ndarray, colors_rgba: np.ndarray = None):
    assert point_cloud.shape[1] == 3

    mesh = _create_mesh(point_cloud, 'mesh_point_cloud')
    obj = bpy.data.objects.new('obj_point_cloud', mesh)

    # Add *Object* to the scene, not the mesh
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    image_name = 'point_cloud_colors'
    if image_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[image_name])

    image = bpy.data.images.new(image_name, len(point_cloud), 1, alpha=True)
    colors_rgba = colors_rgba.reshape((-1))
    image.pixels = [a for a in colors_rgba]

    # ##########
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.02, enter_editmode=False,
                                          location=(0, 0, 0))
    inst_obj = bpy.context.selected_objects[0]

    inst_obj.parent = obj
    # obj.instance_type = 'VERTS'
    obj.instance_type = 'FACES'
    obj.show_instancer_for_render = False

    # UV coords
    me = obj.data
    # Sample data
    # vert_uvs = [(0, i // 3) for i in range(len(me.vertices))]
    vert_uvs = np.repeat(np.arange(0, len(me.vertices)), 3, axis=0)
    # add y coordinate
    vert_uvs = np.stack((vert_uvs, np.zeros_like(vert_uvs)), axis=-1)
    # print(me.polygons)
    me.uv_layers.new(name='per_vertex_dummy_uv')
    # me.uv_textures.new("test")
    me.uv_layers[-1].data.foreach_set("uv",
                                      [uv for pair in [vert_uvs[l.vertex_index] for l in me.loops]
                                       for uv in pair])

    # uv = np.asarray([uv for pair in [vert_uvs[l.vertex_index] for l in me.loops] for uv in pair])

    # ### MATERIAL
    # Vertex color material
    mat = bpy.data.materials.new(name="PointColorMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    # create uv input node
    node_uv = nodes.new(type='ShaderNodeUVMap')
    node_uv.location = 0, 0
    node_uv.from_instancer = True
    node_uv.location = 0, 0
    node_sep = nodes.new(type='ShaderNodeSeparateXYZ')
    node_sep.location = 180, 0
    node_add_x = nodes.new(type='ShaderNodeMath')
    node_add_x.inputs[1].default_value = 0.5
    node_add_x.operation = 'ADD'
    node_add_x.location = 360, 0
    node_add_y = nodes.new(type='ShaderNodeMath')
    node_add_y.inputs[1].default_value = 0.5
    node_add_y.operation = 'ADD'
    node_add_y.location = 450, -200
    node_div_x = nodes.new(type='ShaderNodeMath')
    node_div_x.inputs[1].default_value = float(len(point_cloud))
    node_div_x.operation = 'DIVIDE'
    node_div_x.location = 520, 0
    node_comb = nodes.new(type='ShaderNodeCombineXYZ')
    node_comb.inputs[2].default_value = 0.0
    node_comb.location = 700, 0

    node_text = nodes.new(type='ShaderNodeTexImage')
    node_text.interpolation = 'Closest'
    node_text.extension = 'CLIP'
    node_text.image = image
    node_text.location = 900, 0

    # mix point colors with simple black material
    node_mix_rgb = nodes.new(type='ShaderNodeMixRGB')
    node_mix_rgb.location = 1200, 0
    node_mix_rgb.inputs[0].default_value = 0.0  # all on vertex color
    node_mix_rgb.inputs[2].default_value = (0.01, 0.01, 0.01, 1.0)

    # create shader node
    node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_bsdf.inputs[7].default_value = 0.65  # roughness
    node_bsdf.inputs[12].default_value = 0.0  # clearcoat
    node_bsdf.inputs[13].default_value = 0.25  # clearcoat roughness
    node_bsdf.location = 1500, 0

    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = 1800, 0

    # link nodes
    links = mat.node_tree.links
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

    # function to set color mix factor
    def set_color_factor(f: float):
        node_mix_rgb.inputs[0].default_value = f

    # add material to object
    inst_obj.data.materials.append(mat)

    return obj, set_color_factor
