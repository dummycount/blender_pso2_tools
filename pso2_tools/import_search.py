import sys
import time
from contextlib import closing
from dataclasses import fields
from pathlib import Path
from typing import Iterable, Optional, Type

import bpy

from . import classes, objects
from .colors import ColorId
from .preferences import get_preferences


@classes.register
class FloatItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    value: bpy.props.FloatProperty(name="Value")


@classes.register
class IntItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    value: bpy.props.IntProperty(name="Value")

    INVALID = sys.maxsize


@classes.register
class StringItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    value: bpy.props.StringProperty(name="Value")


@classes.register
class FileNameItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    value: bpy.props.StringProperty(name="File Name")

    def to_file_name(self):
        return objects.CmxFileName(self.value)


@classes.register
class ColorMapItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    red: bpy.props.IntProperty(name="Red Channel")
    green: bpy.props.IntProperty(name="Green Channel")
    blue: bpy.props.IntProperty(name="Blue Channel")
    alpha: bpy.props.IntProperty(name="Alpha Channel")

    def to_color_map(self):
        return objects.CmxColorMapping(
            red=ColorId(self.red),
            green=ColorId(self.green),
            blue=ColorId(self.blue),
            alpha=ColorId(self.alpha),
        )


@classes.register
class ListItem(bpy.types.PropertyGroup):
    item_type: bpy.props.EnumProperty(
        name="Type",
        items=[
            ("ACCESSORY", "Accessory", "Accessory"),
            ("BASEWEAR", "Basewear", "Basewear"),
            ("BODYPAINT", "Bodypaint", "Bodypaint"),
            ("CAST_ARMS", "Cast Arms", "Cast Arms"),
            ("CAST_BODY", "Cast Body", "Cast Body"),
            ("CAST_LEGS", "Cast Legs", "Cast Legs"),
            ("COSTUME", "Costume", "Costume"),
            ("EARS", "Ears", "Ears"),
            ("EYES", "Eyes", "Eyes"),
            ("EYEBROWS", "Eyebrows", "Eyebrows"),
            ("EYELASHES", "Eyelashes", "Eyelashes"),
            ("FACE", "Face", "Face"),
            ("FACE_TEXTURE", "Face Texture", "Face texture"),
            ("FACEPAINT", "Facepaint", "Facepaint"),
            ("HAIR", "Hair", "Hair"),
            ("HORNS", "Horns", "Horns"),
            ("INNERWEAR", "Innerwear", "Innerwear"),
            ("OUTERWEAR", "Outerwear", "Outerwear"),
            ("SKIN", "Skin", "Skin"),
            ("STICKER", "Sticker", "Sticker"),
            ("TEETH", "Teeth", "Teeth"),
        ],
    )
    name: bpy.props.StringProperty(name="Name")
    name_en: bpy.props.StringProperty(name="English Name")
    name_jp: bpy.props.StringProperty(name="Japanese Name")
    item_id: bpy.props.IntProperty(name="ID")
    adjusted_id: bpy.props.IntProperty(name="Adjusted ID")

    files: bpy.props.CollectionProperty(type=FileNameItem)
    float_fields: bpy.props.CollectionProperty(type=FloatItem)
    int_fields: bpy.props.CollectionProperty(type=IntItem)
    string_fields: bpy.props.CollectionProperty(type=StringItem)
    color_map_fields: bpy.props.CollectionProperty(type=ColorMapItem)

    @property
    def is_ngs(self):
        return objects.is_ngs(self.item_id)

    @property
    def description(self):
        enum_items = self.bl_rna.properties["item_type"].enum_items
        desc = enum_items.get(self.item_type).description
        if self.is_ngs:
            desc += " (NGS)"

        return desc

    def populate(self, item_type: str, obj: objects.CmxObjectBase):
        self.item_type = item_type
        self.item_id = obj.id
        self.adjusted_id = obj.adjusted_id
        self.name = obj.name
        self.name_en = obj.name_en
        self.name_jp = obj.name_jp

        for field in fields(obj):
            if field.name in ("id", "adjusted_id", "name_en", "name_jp"):
                continue

            name = field.name
            value = getattr(obj, name)

            if field.type == float:
                prop: FloatItem = self.float_fields.add()
                prop.name = name
                prop.value = value

            elif field.type in (int, Optional[int]):
                prop: IntItem = self.float_fields.add()
                prop.name = name
                prop.value = IntItem.INVALID if value is None else value

            elif field.type == str:
                prop: StringItem = self.string_fields.add()
                prop.name = name
                prop.value = value

            elif field.type == objects.CmxFileName:
                prop: FileNameItem = self.files.add()
                prop.name = name
                prop.value = value.name

            elif field.type == objects.CmxColorMapping:
                prop: ColorMapItem = self.color_map_fields.add()
                prop.name = name
                prop.red = int(value.red)
                prop.green = int(value.green)
                prop.blue = int(value.blue)
                prop.alpha = int(value.alpha)

            else:
                raise NotImplementedError(f"Unhandled field type {field.type}")

    def to_object(self):
        cls = _get_object_class(self.item_type)
        obj = cls(
            id=self.item_id,
            adjusted_id=self.adjusted_id,
            name_en=self.name_en,
            name_jp=self.name_jp,
        )

        for prop in self.files:
            prop: FileNameItem
            setattr(obj, prop.name, prop.to_file_name())

        for prop in self.float_fields:
            prop: FloatItem
            setattr(obj, prop.name, prop.value)

        for prop in self.int_fields:
            prop: IntItem
            setattr(
                obj, prop.name, None if prop.value == IntItem.INVALID else prop.value
            )

        for prop in self.string_fields:
            prop: StringItem
            setattr(obj, prop.name, prop.value)

        for prop in self.color_map_fields:
            prop: ColorMapItem
            setattr(obj, prop.name, prop.to_color_map())


def _get_object_class(item_type: str) -> Type[objects.CmxObjectBase]:
    match item_type:
        case "ACCESSORY":
            return objects.CmxAccessory
        case "BASEWEAR" | "COSTUME" | "OUTERWEAR":
            return objects.CmxBodyObject
        case "CAST_ARMS" | "CAST_BODY" | "CAST_LEGS":
            return objects.CmxBodyObject
        case "BODYPAINT" | "INNERWEAR":
            return objects.CmxBodyPaint
        case "EARS":
            return objects.CmxEarObject
        case "EYES":
            return objects.CmxEyeObject
        case "EYEBROWS" | "EYELASHES":
            return objects.CmxEyebrowObject
        case "FACE":
            return objects.CmxFaceObject
        case "FACE_TEXTURE" | "FACEPAINT":
            return objects.CmxFacePaint
        case "HAIR":
            return objects.CmxHairObject
        case "HORNS":
            return objects.CmxHornObject
        case "SKIN":
            return objects.CmxSkinObject
        case "STICKER":
            return objects.CmxSticker
        case "TEETH":
            return objects.CmxTeethObject
        case _:
            raise NotImplementedError(f"Unhandled item type {item_type}")


@classes.register
class PSO2_OT_ModelSearch(bpy.types.Operator):
    """Search for PSO2 models"""

    bl_label = "Import PSO2 Model"
    bl_idname = "pso2.model_search"
    bl_options = {"REGISTER", "UNDO"}

    models: bpy.props.CollectionProperty(name="Models", type=ListItem)
    models_index: bpy.props.IntProperty(name="Selected Index")

    def _get_selected_model_files(self, context: bpy.types.Context):
        try:
            selected: ListItem = self.models[self.models_index]
        except IndexError:
            return []

        data_path = get_preferences(context).get_pso2_data_path()

        return [v for item in selected.files for v in _get_file_items(item, data_path)]

    model_file: bpy.props.EnumProperty(name="File", items=_get_selected_model_files)

    def __init__(self):
        super().__init__()
        _populate_model_list(self.models, bpy.context)

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.7)

        col = split.column()
        col.context_pointer_set("parent", self)
        col.template_list(
            PSO2_UL_ModelList.bl_idname,
            "",
            self,
            "models",
            self,
            "models_index",
            rows=15,
        )

        col = split.column()
        col.context_pointer_set("parent", self)
        col.prop(self, "model_file")

        col.separator_spacer()
        col.operator(PSO2_OT_UpdateModelList.bl_idname, text="Update Model List")

    def execute(self, context):
        # TODO
        return super().execute(context)

    def invoke(self, context, event) -> set[str]:
        return context.window_manager.invoke_props_dialog(
            self, width=800, confirm_text="Import"
        )


def _get_file_display_name(filename: str):
    match filename:
        case "file":
            return "Normal Quality"
        case "file_ex":
            return "High Quality"
        case "file_rp":
            return "Replacement"
        case "linked_inner_file":
            return "Linked Innerwear"
        case "linked_inner_file_ex":
            return "Linked Innerwear (HQ)"
        case "linked_outer_file":
            return "Linked Outerwear"
        case "linked_outer_file_ex":
            return "Linked Outerwear (HQ)"
        case _:
            return filename


def _get_file_items(item: FileNameItem, data_path: Path):
    if item.name in ("sound_file", "cast_sound_file"):
        return

    base = item.to_file_name()
    ex = base.ex

    if path := ex.path(data_path):
        yield (str(path), _get_file_display_name(item.name + "_ex"), "")

    if path := base.path(data_path):
        yield (str(path), _get_file_display_name(item.name), "")


def _populate_model_list(collection, context: bpy.types.Context):
    collection.clear()

    with closing(objects.ObjectDatabase(context)) as db:
        for item_type, obj in _get_items(db):
            item: ListItem = collection.add()
            item.populate(item_type, obj)


def _get_items(db: objects.ObjectDatabase):
    categories = [
        ("ACCESSORY", db.get_accessories),
        ("BASEWEAR", db.get_basewear),
        ("BODYPAINT", db.get_bodypaint),
        ("CAST_ARMS", db.get_cast_arms),
        ("CAST_BODY", db.get_cast_bodies),
        ("CAST_LEGS", db.get_cast_legs),
        ("COSTUME", db.get_costumes),
        ("EARS", db.get_ears),
        ("EYES", db.get_eyes),
        ("EYEBROWS", db.get_eyebrows),
        ("EYELASHES", db.get_eyelashes),
        ("FACE", db.get_faces),
        ("FACE_TEXTURE", db.get_face_textures),
        ("FACEPAINT", db.get_facepaint),
        ("HAIR", db.get_hair),
        ("HORNS", db.get_horns),
        ("INNERWEAR", db.get_innerwear),
        ("OUTERWEAR", db.get_outerwear),
        ("SKIN", db.get_skins),
        ("STICKER", db.get_stickers),
        ("TEETH", db.get_teeth),
    ]

    return (
        (item_type, item) for item_type, get_items in categories for item in get_items()
    )


@classes.register
class PSO2_OT_UpdateModelList(bpy.types.Operator):
    """Update PSO2 model list"""

    bl_label = "Update Model List"
    bl_idname = "pso2.update_model_list"

    def execute(self, context) -> set[str]:
        with closing(objects.ObjectDatabase(context)) as db:
            db.update_database()

        _populate_model_list(context.parent.models, context)

        return {"FINISHED"}


@classes.register
class PSO2_UL_ModelList(bpy.types.UIList):
    """PSO2 model list"""

    bl_idname = "PSO2_UL_ModelList"
    layout_type = "DEFAULT"

    # pylint: disable-next=arguments-renamed
    def filter_items(self, context, data, prop):
        preferences = get_preferences(context)
        items: Iterable[ListItem] = getattr(data, prop)

        if not items:
            return [], []

        if self.filter_name:
            flt_flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item, items, propname="name"
            )
        else:
            flt_flags = [self.bitflag_filter_item] * len(items)

        if preferences.model_search_versions:
            show_ngs = "NGS" in preferences.model_search_versions
            show_cls = "CLASSIC" in preferences.model_search_versions

            for idx, item in enumerate(items):
                if (not show_ngs and item.is_ngs) or (not show_cls and not item.is_ngs):
                    flt_flags[idx] &= ~self.bitflag_filter_item

        if preferences.model_search_categories:
            show_types = {
                x.strip()
                for enum in preferences.model_search_categories
                for x in enum.split("|")
            }
            for idx, item in enumerate(items):
                if item.item_type not in show_types:
                    flt_flags[idx] &= ~self.bitflag_filter_item

        flt_neworder = bpy.types.UI_UL_list.sort_items_by_name(items, "name")

        return flt_flags, flt_neworder

    def draw_filter(self, context, layout):
        preferences = get_preferences(context)

        row = layout.row(align=True)
        row.activate_init = True
        row.prop(self, "filter_name", text="", icon="VIEWZOOM")

        row = layout.row(align=True)
        row.label(text="Filters")

        flow = layout.column_flow(columns=2)
        subrow = flow.row(align=True)
        subrow.prop(preferences, "model_search_versions", expand=True)
        flow.operator(PSO2_OT_SelectAllCategories.bl_idname)

        flow = layout.grid_flow(columns=4, align=True)
        flow.prop(preferences, "model_search_categories", expand=True)

    def draw_item(
        self,
        context,
        layout,
        data,
        item: ListItem,
        icon,
        active_data,
        active_property,
        index=0,
        flt_flag=0,
    ):
        # Hack to keep the filter open
        self.use_filter_show = True

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            icon = _get_icon(item.item_type)
            layout.label(text=item.name, icon=icon)
            layout.label(text=item.description)

            if get_preferences(context).debug:
                layout.label(text=str(item.item_id))

        elif self.layout_type == "GRID":
            pass


def _get_icon(item_type: str) -> str:
    match item_type:
        case "ACCESSORY":
            return "MESH_TORUS"
        case "BASEWEAR" | "COSTUME" | "OUTERWEAR":
            return "MATCLOTH"
        case "CAST_ARMS" | "CAST_BODY" | "CAST_LEGS":
            return "MATCLOTH"
        case "BODYPAINT" | "INNERWEAR":
            return "TEXTURE"
        case "EARS":
            return "USER"
        case "EYES":
            return "HIDE_OFF"
        case "EYEBROWS" | "EYELASHES":
            return "HIDE_OFF"
        case "FACE":
            return "USER"
        case "FACE_TEXTURE" | "FACEPAINT":
            return "USER"
        case "HAIR":
            return "USER"
        case "HORNS":
            return "USER"
        case "SKIN":
            return "TEXTURE"
        case "STICKER":
            return "TEXTURE"
        case "TEETH":
            return "USER"
        case _:
            raise NotImplementedError(f"Unhandled item type {item_type}")


@classes.register
class PSO2_OT_SelectAllCategories(bpy.types.Operator):
    """Select All Categories"""

    bl_label = "Select All"
    bl_idname = "pso2.select_all_categories"

    def execute(self, context):
        preferences = get_preferences(context)

        preferences.model_search_categories = _get_all_enum_items(
            preferences, "model_search_categories"
        )

        return {"FINISHED"}


def _get_all_enum_items(obj: bpy.types.bpy_struct, prop: str) -> set[str]:
    return {enum.identifier for enum in obj.bl_rna.properties[prop].enum_items.values()}
