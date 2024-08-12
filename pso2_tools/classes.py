import bpy

__classes = []


def register(cls):
    __classes.append(cls)
    return cls


def bpy_register():
    for cls in __classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            bpy.utils.unregister_class(cls)
            bpy.utils.register_class(cls)


def bpy_unregister():
    for cls in __classes:
        bpy.utils.unregister_class(cls)
