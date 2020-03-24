# -*- coding: utf-8 -*-
import logging
import inspect
from decorator import decorate

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


try:
    import bpy
except ImportError:
    bpy = None

try:
    import bmesh
except ImportError:
    bmesh = None


def needs_bpy_bmesh(
    default_return=None, alternative_func=None, run_anyway: bool = False
):
    """ Decorator to facilitate developing and debugging when blender python (bpy)
    is not actually available.
    """

    # list modules to look for in kw-only args
    m = {"bpy": bpy, "bmesh": bmesh}

    def inner(func):
        argspec = inspect.getfullargspec(func)
        kwonly = set(argspec.kwonlyargs)
        defaults = argspec.kwonlydefaults

        n = {k: v for k, v in m.items() if k in kwonly}

        if not n:
            logger.warning(
                "Neither bpy nor bmesh in kwonly function args of '{}'.".format(
                    func.__name__
                )
            )

        if defaults is not None:
            if any(k in defaults for k in n):
                raise RuntimeError("Default value is not allowed.")

        def caller(f, *args, **kw):
            return f(*args, **kw)

        # True if all requested modules are available
        valid = all(v is not None for v in n.values())

        if valid or run_anyway:
            decorated = decorate(func, caller)

        else:

            def replacement(_f, *args, **kw):
                if alternative_func is not None:
                    return alternative_func(*args, **kw)
                elif default_return is not None:
                    return default_return
                else:
                    raise ImportError(
                        "Cannot call '{}' which requires bpy/bmesh.".format(
                            func.__name__
                        )
                    )

            decorated = decorate(func, replacement)

        # make decorated callable without specifying bpy
        if decorated.__kwdefaults__ is None:
            decorated.__kwdefaults__ = {}
        decorated.__kwdefaults__.update(n)
        return decorated

    return inner
