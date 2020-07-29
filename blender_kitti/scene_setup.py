# -*- coding: utf-8 -*-
""""""

import pathlib
from .bpy_helper import needs_bpy_bmesh


@needs_bpy_bmesh()
def clear_all(*, bpy):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    master_collection = bpy.context.scene.collection
    for c in master_collection.children:
        master_collection.children.unlink(c)

    for c in bpy.data.collections:
        for o in c.objects:
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(c)


@needs_bpy_bmesh()
def add_light_source(*, bpy):
    bpy.ops.mesh.primitive_plane_add()
    scene_light = bpy.context.selected_objects[0]
    scene_light.name = "SceneLight"
    # Location above and somewhat behind scene center
    scene_light.location = (-20.0, 0.0, 50.0)
    scene_light.scale = (20.0, 30.0, 1.0)

    mat = bpy.data.materials.new(name="LightEmission")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    # create emission node
    node_emission = nodes.new(type="ShaderNodeEmission")
    node_emission.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)  # RGBA
    node_emission.inputs[1].default_value = 5.0  # strength
    node_emission.location = 0, 0
    # create output node
    node_output = nodes.new(type="ShaderNodeOutputMaterial")
    node_output.location = 200, 0
    # link nodes
    links = mat.node_tree.links
    _ = links.new(node_emission.outputs[0], node_output.inputs[0])

    scene_light.data.materials.append(mat)
    # not visible in camera
    scene_light.cycles_visibility.camera = False

    # enable ambient occlusion
    world = bpy.context.scene.world
    world.light_settings.use_ambient_occlusion = True


@needs_bpy_bmesh()
def add_hdr_background(*, bpy):
    hdr_filepath = (
        pathlib.Path(__file__).parent.parent / "assets" / "ruckenkreuz_2k.hdr"
    )
    if not hdr_filepath.is_file():
        raise FileNotFoundError(
            "Cannot find HDR background file {}".format(str(hdr_filepath))
        )
    background_image = bpy.data.images.load(str(hdr_filepath), check_existing=False)

    world = bpy.data.worlds["World"]
    nodes = world.node_tree.nodes
    nodes.clear()

    node_tex_env = nodes.new(type="ShaderNodeTexEnvironment")
    node_tex_env.location = 0, 0
    node_tex_env.image = background_image

    node_background = nodes.new(type="ShaderNodeBackground")
    node_background.location = 300, 0

    node_output = nodes.new(type="ShaderNodeOutputWorld")
    node_output.location = 600, 0

    # link nodes
    links = world.node_tree.links
    links.new(node_tex_env.outputs[0], node_background.inputs[0])
    links.new(node_background.outputs[0], node_output.inputs[0])


@needs_bpy_bmesh()
def create_camera_top_view_ortho(
    name: str = "CameraTopViewOrtho", center=(0.0, 0.0), scale: float = 20.0, *, bpy
):
    """top view orthographic. """
    cam = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new("Obj" + name, cam)
    cam.location = center + (45.0,)
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = scale
    return cam


@needs_bpy_bmesh()
def create_camera_perspective(
    location,
    rotation_quat,
    name: str = "CameraPerspective",
    focal_length: float = 50.0,
    *,
    bpy
):
    cam = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new("Obj" + name, cam)
    cam.location = location
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = rotation_quat
    cam.data.type = "PERSP"
    cam.data.lens = focal_length
    return cam


def add_cameras_default(scene):
    """ Make two camera (main/top) default setup for demo images."""
    cam_main = create_camera_perspective(
        location=(-33.3056, 24.1123, 26.0909),
        rotation_quat=(0.42119, 0.21272, -0.39741, -0.78703),
    )
    scene.collection.objects.link(cam_main)

    cam_top = create_camera_top_view_ortho()
    scene.collection.objects.link(cam_top)

    # make this the main scene camera
    scene.camera = cam_main
    return cam_main, cam_top


@needs_bpy_bmesh(default_return=None)
def setup_scene(name: str = "blender_kitti", use_background_image: bool = True, *, bpy):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.name = name
    scene.render.film_transparent = True

    clear_all()

    if use_background_image:
        add_hdr_background()
    else:
        add_light_source()
    return scene
