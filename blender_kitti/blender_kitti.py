# -*- coding: utf-8 -*-
""""""
import typing

try:
    import bpy
except ImportError:
    bpy = None
    print("bpy module not available.")
import numpy as np


def _create_mesh(positions: np.ndarray, name="mesh_points"):
    """Create mesh with where each point is a pseudo face (three vertices at the same position. """
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
    return mesh


def _create_instancer_obj(
    positions: np.ndarray, name_instancer_obj: str, name_mesh: str
):
    assert positions.ndim == 2 and positions.shape[1] == 3

    if name_instancer_obj in bpy.data.objects:
        raise RuntimeError("Object '{}' already exists.".format(name_instancer_obj))

    mesh = _create_mesh(positions, name_mesh)

    vert_uvs = np.repeat(np.arange(0, len(mesh.vertices)), 3, axis=0)
    # add y coordinate
    vert_uvs = np.stack((vert_uvs, np.zeros_like(vert_uvs)), axis=-1)
    mesh.uv_layers.new(name="per_vertex_dummy_uv")
    mesh.uv_layers[-1].data.foreach_set(
        "uv",
        [uv for pair in [vert_uvs[l.vertex_index] for l in mesh.loops] for uv in pair],
    )

    obj_instancer = bpy.data.objects.new(name_instancer_obj, mesh)
    return obj_instancer


def _create_simple_material(base_color, name_material: str):
    if name_material in bpy.data.materials:
        raise RuntimeError("Material '{}' already exists")
    mat = bpy.data.materials.new(name=name_material)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
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
    links = mat.node_tree.links
    links.new(node_bsdf.outputs[0], node_output.inputs[0])

    return mat


def _create_uv_mapped_material(
    color_image, name_material: str = "material_point_cloud"
):
    assert color_image.size[1] == 1

    if name_material in bpy.data.materials:
        raise RuntimeError("Material '{}' already exists")

    mat = bpy.data.materials.new(name=name_material)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
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

    return mat


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
    return image


def _create_entites(
    name_prefix: str,
    positions: np.ndarray,
    colors: typing.Union[None, np.ndarray],
    obj_particle,
):
    # created entities
    name_mesh = "mesh_{}".format(name_prefix)
    name_obj = "obj_instancer_{}".format(name_prefix)
    name_image = "colors_{}".format(name_prefix)
    name_material = "material_{}".format(name_prefix)

    obj_instancer = _create_instancer_obj(positions, name_obj, name_mesh)

    if colors is not None:
        image = _create_color_image(colors, name_image)
        # the particle obj will use this material
        material = _create_uv_mapped_material(image, name_material)
    else:
        material = _create_simple_material(
            base_color=(0.1, 0.1, 0.1, 1.0), name_material=name_material
        )

    obj_particle.parent = obj_instancer
    # instancing from 'fake' faces is necessary for uv mapping to work.
    obj_instancer.instance_type = "FACES"
    obj_instancer.show_instancer_for_render = False

    obj_particle.data.materials.append(material)
    return obj_instancer


def add_voxels(
    voxels: np.ndarray,
    colors: np.ndarray = None,
    name_prefix: str = "voxels",
    scene=None,
):
    assert voxels.ndim == 3
    assert voxels.dtype == np.bool

    dtype = np.float32
    deltas = np.asarray([0.2, 0.2, 0.2], dtype=dtype)

    coords = np.mgrid[[slice(x) for x in voxels.shape]].astype(dtype)
    coords = np.moveaxis(coords, 0, 3)
    coords *= deltas
    coords = coords[voxels]
    colors = colors[voxels]

    # Todo replace with non-ops calls to create object
    bpy.ops.mesh.primitive_cube_add(size=0.16, enter_editmode=False, location=(0, 0, 0))
    obj_particle = bpy.context.selected_objects[0]

    obj_instancer = _create_entites(name_prefix, coords, colors, obj_particle)
    if scene is not None:
        scene.collection.objects.link(obj_instancer)
    return obj_instancer


def add_point_cloud(
    points: np.ndarray,
    colors: np.ndarray = None,
    row_splits: np.ndarray = None,
    name_prefix: str = "point_cloud",
    scene=None,
):
    # created entities
    # Todo replace with non-ops calls to create object
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=3, radius=0.02, enter_editmode=False, location=(0, 0, 0)
    )
    obj_particle = bpy.context.selected_objects[0]

    obj_instancer = _create_entites(name_prefix, points, colors, obj_particle)

    if scene is not None:
        scene.collection.objects.link(obj_instancer)
    return obj_instancer


def execute_data_tasks(tasks: {str: typing.Any}):

    scene = bpy.context.scene

    for instance_name, (task_f, task_kwargs) in tasks.items():
        if "scene" not in task_kwargs:
            task_kwargs["scene"] = scene
        task_f(**task_kwargs)
