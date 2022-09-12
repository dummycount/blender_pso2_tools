import bpy

__classes = []


def register_class(cls):
    __classes.append(cls)
    return cls


def register():
    for cls in __classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in __classes:
        bpy.utils.unregister_class(cls)
