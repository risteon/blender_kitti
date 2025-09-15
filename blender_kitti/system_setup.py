# -*- coding: utf-8 -*-
""""""

import bpy


def enable_devices():
    ctx = bpy.context
    cprefs = ctx.preferences.addons["cycles"].preferences

    devices = cprefs.get_device_list("NONE")
    if not devices:
        raise RuntimeError("No compute devices found, not even a CPU?")

    device_types = [device_desc[1] for device_desc in devices]
    device_types = [t for t in device_types if t != "CPU"]
    if not device_types:
        raise RuntimeError(
            "No accelerator device found (CUDA, OPTIX, HIP, ONEAPI, ...)"
        )
    cprefs.compute_device_type = device_types[0]

    for device in cprefs.devices:
        device.use = True
