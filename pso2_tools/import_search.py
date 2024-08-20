import sys
from contextlib import closing
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Iterable, Optional, Type

import bpy

from . import classes, import_model, objects
from .colors import COLOR_CHANNELS, ColorId
from .objects import ObjectType
from .preferences import get_preferences


@dataclass
class ModelMetadata:
    has_linked_inner: bool = False
    has_linked_outer: bool = False
    leg_length: Optional[float] = None

    @classmethod
    def from_object(cls, obj: objects.CmxObjectBase, data_path: Path):
        result = cls()

        if isinstance(obj, objects.CmxBodyObject):
            result.leg_length = obj.leg_length
            result.has_linked_inner = obj.linked_inner_file.exists(data_path)
            result.has_linked_outer = obj.linked_outer_file.exists(data_path)

        return result


@classes.register
class FloatItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    value: bpy.props.FloatProperty(name="Value")

    INVALID = float("inf")


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
    object_type: bpy.props.EnumProperty(
        name="Type",
        items=[
            (str(ObjectType.ACCESSORY), "Accessory", "Accessory"),
            (str(ObjectType.BASEWEAR), "Basewear", "Basewear"),
            (str(ObjectType.BODYPAINT), "Bodypaint", "Bodypaint"),
            (str(ObjectType.CAST_ARMS), "Cast Arms", "Cast Arms"),
            (str(ObjectType.CAST_BODY), "Cast Body", "Cast Body"),
            (str(ObjectType.CAST_LEGS), "Cast Legs", "Cast Legs"),
            (str(ObjectType.COSTUME), "Costume", "Costume"),
            (str(ObjectType.EAR), "Ears", "Ears"),
            (str(ObjectType.EYE), "Eyes", "Eyes"),
            (str(ObjectType.EYEBROW), "Eyebrows", "Eyebrows"),
            (str(ObjectType.EYELASH), "Eyelashes", "Eyelashes"),
            (str(ObjectType.FACE), "Face", "Face"),
            (str(ObjectType.FACE_TEXTURE), "Face Texture", "Face texture"),
            (str(ObjectType.FACEPAINT), "Facepaint", "Facepaint"),
            (str(ObjectType.HAIR), "Hair", "Hair"),
            (str(ObjectType.HORN), "Horns", "Horns"),
            (str(ObjectType.INNERWEAR), "Innerwear", "Innerwear"),
            (str(ObjectType.OUTERWEAR), "Outerwear", "Outerwear"),
            (str(ObjectType.SKIN), "Skin", "Skin"),
            (str(ObjectType.STICKER), "Sticker", "Sticker"),
            (str(ObjectType.TEETH), "Teeth", "Teeth"),
        ],
    )
    name: bpy.props.StringProperty(name="Name")
    name_en: bpy.props.StringProperty(name="English Name")
    name_jp: bpy.props.StringProperty(name="Japanese Name")
    object_id: bpy.props.IntProperty(name="ID")
    adjusted_id: bpy.props.IntProperty(name="Adjusted ID")

    files: bpy.props.CollectionProperty(type=FileNameItem)
    float_fields: bpy.props.CollectionProperty(type=FloatItem)
    int_fields: bpy.props.CollectionProperty(type=IntItem)
    string_fields: bpy.props.CollectionProperty(type=StringItem)
    color_map_fields: bpy.props.CollectionProperty(type=ColorMapItem)

    @property
    def is_ngs(self):
        return objects.is_ngs(self.object_id)

    @property
    def description(self):
        enum_items = self.bl_rna.properties["object_type"].enum_items
        desc = enum_items.get(self.object_type).description
        if self.is_ngs:
            desc += " (NGS)"

        return desc

    def populate(self, obj: objects.CmxObjectBase):
        self.object_type = str(obj.object_type)
        self.object_id = obj.id
        self.adjusted_id = obj.adjusted_id
        self.name = obj.name
        self.name_en = obj.name_en
        self.name_jp = obj.name_jp

        for field in fields(obj):
            if field.name in ("object_type", "id", "adjusted_id", "name_en", "name_jp"):
                continue

            name = field.name
            value = getattr(obj, name)

            if field.type in (float, Optional[float]):
                prop: FloatItem = self.float_fields.add()
                prop.name = name
                prop.value = FloatItem.INVALID if value is None else value

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
        object_type = ObjectType(self.object_type)
        cls = _get_object_class(object_type)
        obj = cls(
            object_type=object_type,
            id=self.object_id,
            adjusted_id=self.adjusted_id,
            name_en=self.name_en,
            name_jp=self.name_jp,
        )

        for prop in self.files:
            prop: FileNameItem
            setattr(obj, prop.name, prop.to_file_name())

        for prop in self.float_fields:
            prop: FloatItem
            setattr(
                obj, prop.name, None if prop.value == FloatItem.INVALID else prop.value
            )

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

        return obj


def _get_object_class(object_type: ObjectType) -> Type[objects.CmxObjectBase]:
    match object_type:
        case ObjectType.ACCESSORY:
            return objects.CmxAccessory
        case ObjectType.BASEWEAR | ObjectType.COSTUME | ObjectType.OUTERWEAR:
            return objects.CmxBodyObject
        case ObjectType.CAST_ARMS | ObjectType.CAST_BODY | ObjectType.CAST_LEGS:
            return objects.CmxBodyObject
        case ObjectType.BODYPAINT | ObjectType.INNERWEAR:
            return objects.CmxBodyPaint
        case ObjectType.EAR:
            return objects.CmxEarObject
        case ObjectType.EYE:
            return objects.CmxEyeObject
        case ObjectType.EYEBROW | ObjectType.EYELASH:
            return objects.CmxEyebrowObject
        case ObjectType.FACE:
            return objects.CmxFaceObject
        case ObjectType.FACE_TEXTURE | ObjectType.FACEPAINT:
            return objects.CmxFacePaint
        case ObjectType.HAIR:
            return objects.CmxHairObject
        case ObjectType.HORN:
            return objects.CmxHornObject
        case ObjectType.SKIN:
            return objects.CmxSkinObject
        case ObjectType.STICKER:
            return objects.CmxSticker
        case ObjectType.TEETH:
            return objects.CmxTeethObject
        case _:
            raise NotImplementedError(f"Unhandled item type {object_type}")


@classes.register
class PSO2_OT_ModelSearch(bpy.types.Operator):
    """Search for PSO2 models"""

    bl_label = "Import PSO2 Model"
    bl_idname = "pso2.model_search"
    bl_options = {"REGISTER", "UNDO"}

    def _get_selected_model_files(self, context: bpy.types.Context):
        try:
            selected: ListItem = self.models[self.models_index]
        except IndexError:
            return []

        data_path = get_preferences(context).get_pso2_data_path()
        return _get_file_items(selected.files, data_path)

    models: bpy.props.CollectionProperty(name="Models", type=ListItem)
    models_index: bpy.props.IntProperty(name="Selected Index")
    model_file: bpy.props.EnumProperty(name="File", items=_get_selected_model_files)

    def __init__(self):
        super().__init__()
        _populate_model_list(self.models, bpy.context)

    def draw(self, context):
        preferences = get_preferences(context)
        layout = self.layout
        split = layout.split(factor=0.75)

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
        col.use_property_split = True
        col.use_property_decorate = False
        col.context_pointer_set("parent", self)

        row = col.row(align=True)
        row.use_property_split = False
        row.props_enum(self, "model_file")

        if obj := self.get_selected_object():
            meta = ModelMetadata.from_object(obj, preferences.get_pso2_data_path())

            if meta.has_linked_inner:
                col.label(text="Has linked innerwear")

            if meta.has_linked_outer:
                col.label(text="Has linked outerwear")

            if meta.leg_length:
                col.label(text=f"Leg length: {meta.leg_length:.3f}")

            if colors := sorted(obj.get_colors()):
                col.label(text="Colors", icon="COLOR")
                for color in colors:
                    col.prop(preferences, COLOR_CHANNELS[color].prop)

        col.separator(factor=2, type="LINE")
        col.operator(PSO2_OT_UpdateModelList.bl_idname, text="Update Model List")

    def execute(self, context):
        if obj := self.get_selected_object():
            high_quality = self.model_file == "HQ"
            import_model.import_object(self, context, obj, high_quality=high_quality)
            return {"FINISHED"}

        return {"CANCELLED"}

    def invoke(self, context, event) -> set[str]:
        return context.window_manager.invoke_props_dialog(
            self, width=800, confirm_text="Import"
        )

    def get_selected_object(self) -> objects.CmxObjectBase:
        try:
            return self.models[self.models_index].to_object()
        except IndexError:
            return None


def _get_file_items(items: Iterable[FileNameItem], data_path: Path):
    item = next((item for item in items if item.name == "file"), None)
    if item is None:
        return []

    normal = item.to_file_name()
    high = normal.ex

    if high.exists(data_path):
        yield ("HQ", "High Quality", "Select high quality model")

    if normal.exists(data_path):
        yield ("NQ", "Normal Quality", "Select normal quality model")


def _populate_model_list(collection, context: bpy.types.Context):
    collection.clear()

    with closing(objects.ObjectDatabase(context)) as db:
        for obj in db.get_all():
            item: ListItem = collection.add()
            item.populate(obj)


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
                if str(item.object_type) not in show_types:
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
            icon = _get_icon(ObjectType(item.object_type))
            layout.label(text=item.name, icon=icon)
            layout.label(text=item.description)

            if get_preferences(context).debug:
                layout.label(text=str(item.object_id))

        elif self.layout_type == "GRID":
            pass


def _get_icon(object_type: ObjectType) -> str:
    match object_type:
        case ObjectType.ACCESSORY:
            return "MESH_TORUS"
        case ObjectType.BASEWEAR | ObjectType.COSTUME | ObjectType.OUTERWEAR:
            return "MATCLOTH"
        case ObjectType.CAST_ARMS | ObjectType.CAST_BODY | ObjectType.CAST_LEGS:
            return "MATCLOTH"
        case ObjectType.BODYPAINT | ObjectType.INNERWEAR:
            return "TEXTURE"
        case ObjectType.EAR:
            return "USER"
        case ObjectType.EYE:
            return "HIDE_OFF"
        case ObjectType.EYEBROW | ObjectType.EYELASH:
            return "HIDE_OFF"
        case ObjectType.FACE:
            return "USER"
        case ObjectType.FACE_TEXTURE | ObjectType.FACEPAINT:
            return "USER"
        case ObjectType.HAIR:
            return "USER"
        case ObjectType.HORN:
            return "USER"
        case ObjectType.SKIN:
            return "TEXTURE"
        case ObjectType.STICKER:
            return "TEXTURE"
        case ObjectType.TEETH:
            return "USER"
        case _:
            raise NotImplementedError(f"Unhandled item type {object_type}")


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
