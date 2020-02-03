# -*- coding: utf-8 -*-
""""""

try:
    import bpy
except ImportError:
    bpy = None
    print("bpy module not available.")


def clear_all():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    master_collection = bpy.context.scene.collection
    for c in master_collection.children:
        master_collection.children.unlink(c)

    for c in bpy.data.collections:
        for o in c.objects:
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(c)


def add_light_source():
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


def add_cameras():
    cam = bpy.data.cameras.new("CameraMain")
    cam_main = bpy.data.objects.new("ObjCameraMain", cam)
    cam_main.location = (-33.3056, 24.1123, 26.0909)
    cam_main.rotation_mode = "QUATERNION"
    cam_main.rotation_quaternion = (0.42119, 0.21272, -0.39741, -0.78703)
    cam_main.data.type = "PERSP"
    bpy.context.scene.collection.objects.link(cam_main)

    # make this the main scene camera
    bpy.context.scene.camera = cam_main

    # top view orthograpic. Vehicle (x-axis) faces to the right
    cam = bpy.data.cameras.new("CameraTopView")
    cam_top = bpy.data.objects.new("ObjCameraTopView", cam)
    cam_top.location = (0.0, 0.0, 45.0)
    cam_top.rotation_mode = "QUATERNION"
    cam_top.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    cam_top.data.type = "ORTHO"
    cam_top.data.ortho_scale = 50.0
    bpy.context.scene.collection.objects.link(cam_top)

    return cam_main, cam_top


def enable_cycles_render_devices():
    # setup render devices. Use all.
    cycles_prefs = bpy.context.preferences.addons["cycles"].preferences
    cycles_prefs.compute_device_type = "CUDA"
    cycles_prefs.get_devices()
    try:
        # blender2.81+
        for device_type in cycles_prefs.get_device_types(bpy.context):
            cycles_prefs.get_devices_for_type(device_type[0])
    except AttributeError:
        pass
    for device in cycles_prefs.devices:
        device.use = True


def setup_scene(name: str = "blender_kitti"):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.name = name

    clear_all()
    add_light_source()
    cameras = add_cameras()

    return scene, cameras
