# -*- coding: utf-8 -*-

import inspect
from decorator import decorate

try:
    import bpy
except ImportError:
    bpy = None


def needs_bpy(default_return=None, alternative_func=None):
    """ Decorator to facilitate developing and debugging when blender python (bpy)
    is not actually available.
    """

    def inner(func):
        argspec = inspect.getfullargspec(func)
        kwonly = set(argspec.kwonlyargs)
        defaults = argspec.kwonlydefaults

        if "bpy" not in kwonly:
            raise RuntimeError(
                "'bpy' missing in kw-only args of function signature of '{}'.".format(
                    func.__name__
                )
            )

        if defaults is not None and "bpy" in defaults:
            raise RuntimeError("Default value for 'bpy' is not allowed.")

        def caller(f, *args, **kw):
            return f(*args, **kw)

        if bpy is not None:
            decorated = decorate(func, caller)

        else:

            def replacement(f, *args, **kw):
                if alternative_func is not None:
                    return alternative_func(*args, **kw)
                elif default_return is not None:
                    return default_return
                else:
                    raise RuntimeError(
                        "Cannot call '{}' which requires bpy.".format(func.__name__)
                    )

            decorated = decorate(func, replacement)

        # make decorated callable without specifying bpy
        if decorated.__kwdefaults__ is None:
            decorated.__kwdefaults__ = {"bpy": bpy}
        else:
            decorated.__kwdefaults__["bpy"] = bpy

        return decorated

    return inner
