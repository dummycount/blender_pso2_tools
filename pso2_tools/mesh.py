from functools import reduce
from typing import Iterable

import bmesh
import bpy
import mathutils

from . import classes

DEFAULT_TOLERANCE = 1.0e-4


@classes.register
class PSO2_OT_WeldMeshEdges(bpy.types.Operator):
    bl_idname = "pso2.weld_mesh_edges"
    bl_label = "Weld Mesh Edges"
    bl_description = "Merge vertex positions and normals based on proximity"
    bl_options = {"REGISTER", "UNDO"}

    distance: bpy.props.FloatProperty(
        name="Merge Distance", subtype="DISTANCE", default=DEFAULT_TOLERANCE
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH"

    def execute(self, context):
        weld_mesh_edges(context, self.distance)
        return {"FINISHED"}


def weld_mesh_edges(context: bpy.types.Context, distance: float):
    objects = [obj for obj in context.selected_objects if obj.type == "MESH"]
    meshes = [bmesh.from_edit_mesh(obj.data) for obj in objects]

    verts = [v for m in meshes for v in m.verts if v.select]

    groups = group_vertices_by_distance(verts, distance=distance)
    for group in groups:
        n = len(group)
        if n < 2:
            continue

        group_verts = [verts[i] for i in group]
        center = average([v.co for v in group_verts])
        normal = average([v.normal for v in group_verts])
        normal.normalize()

        # TODO: this doesn't result in a seamless edge in game, even though it
        # looks fine in Blender. Why? Update edge and face normals too?
        # Also need to adjust bone weights so gaps don't appear when animating.
        for v in group_verts:
            v.co = center
            v.normal = normal

    for obj in objects:
        bmesh.update_edit_mesh(obj.data, loop_triangles=False, destructive=False)


def average(vectors: Iterable[mathutils.Vector]):
    return reduce(lambda x, y: x + y, vectors) / len(vectors)


def group_vertices_by_distance(verts: Iterable[bmesh.types.BMVert], distance: float):
    verts = list(verts)
    kd = mathutils.kdtree.KDTree(len(verts))

    for i, v in enumerate(verts):
        kd.insert(v.co, i)

    kd.balance()

    groups: list[list[int]] = []
    indices = list(range(len(verts)))

    try:
        while True:
            i = indices[0]
            group = []

            # pylint: disable=not-an-iterable
            for _, index, _ in kd.find_range(verts[i].co, distance):
                try:
                    indices.remove(index)
                    group.append(index)
                except ValueError:
                    pass

            groups.append(group)
    except IndexError:
        pass

    return groups
