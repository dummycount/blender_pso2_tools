import math
import sys
import time
from collections.abc import Iterable, Sequence
from contextlib import closing
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, cast

import bpy

from . import ccl, classes, import_model, import_props, objects
from .colors import COLOR_CHANNELS, Color, ColorId
from .debug import debug_print
from .preferences import (
    Pso2ToolsPreferences,
    color_property,
    get_preferences,
)
from .util import BlenderIcon, OperatorResult


@dataclass
class ModelMetadata:
    has_linked_inner: bool = False
    has_linked_outer: bool = False
    leg_length: float | None = None

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


_GENDERED_OBJECT_TYPES = [
    str(objects.ObjectType.BASEWEAR),
    str(objects.ObjectType.BODYPAINT),
    str(objects.ObjectType.CAST_ARMS),
    str(objects.ObjectType.CAST_BODY),
    str(objects.ObjectType.CAST_LEGS),
    str(objects.ObjectType.COSTUME),
    str(objects.ObjectType.FACE),
    str(objects.ObjectType.FACE_TEXTURE),
    str(objects.ObjectType.INNERWEAR),
    str(objects.ObjectType.OUTERWEAR),
    str(objects.ObjectType.SKIN),
]

_VERSIONLESS_OBJECT_TYPES = [
    str(objects.ObjectType.STICKER),
]


@classes.register
class ListItem(bpy.types.PropertyGroup):
    object_type: bpy.props.EnumProperty(
        name="Type",
        items=[
            (str(objects.ObjectType.ACCESSORY), "Accessory", "Accessory"),
            (str(objects.ObjectType.BASEWEAR), "Basewear", "Basewear"),
            (str(objects.ObjectType.BODYPAINT), "Bodypaint", "Bodypaint"),
            (str(objects.ObjectType.CAST_ARMS), "Cast Arms", "Cast Arms"),
            (str(objects.ObjectType.CAST_BODY), "Cast Body", "Cast Body"),
            (str(objects.ObjectType.CAST_LEGS), "Cast Legs", "Cast Legs"),
            (str(objects.ObjectType.COSTUME), "Costume", "Costume"),
            (str(objects.ObjectType.EAR), "Ears", "Ears"),
            (str(objects.ObjectType.EYE), "Eyes", "Eyes"),
            (str(objects.ObjectType.EYEBROW), "Eyebrows", "Eyebrows"),
            (str(objects.ObjectType.EYELASH), "Eyelashes", "Eyelashes"),
            (str(objects.ObjectType.FACE), "Face", "Face"),
            (str(objects.ObjectType.FACE_TEXTURE), "Face Texture", "Face texture"),
            (str(objects.ObjectType.FACEPAINT), "Facepaint", "Facepaint"),
            (str(objects.ObjectType.HAIR), "Hair", "Hair"),
            (str(objects.ObjectType.HORN), "Horns", "Horns"),
            (str(objects.ObjectType.INNERWEAR), "Innerwear", "Innerwear"),
            (str(objects.ObjectType.OUTERWEAR), "Outerwear", "Outerwear"),
            (str(objects.ObjectType.SKIN), "Skin", "Skin"),
            (str(objects.ObjectType.STICKER), "Sticker", "Sticker"),
            (str(objects.ObjectType.TEETH), "Teeth", "Teeth"),
        ],
    )
    name_en: bpy.props.StringProperty(name="English Name")
    name_jp: bpy.props.StringProperty(name="Japanese Name")
    object_id: bpy.props.IntProperty(name="ID")
    adjusted_id: bpy.props.IntProperty(name="Adjusted ID")

    files: bpy.props.CollectionProperty(type=FileNameItem)
    float_fields: bpy.props.CollectionProperty(type=FloatItem)
    int_fields: bpy.props.CollectionProperty(type=IntItem)
    string_fields: bpy.props.CollectionProperty(type=StringItem)
    color_map_fields: bpy.props.CollectionProperty(type=ColorMapItem)

    # Extra metadata for sort
    leg_length: bpy.props.FloatProperty(name="Leg Length")

    @property
    def item_name(self) -> str:
        return self.name_en or self.name_jp or f"Unnamed {self.object_id}"

    @property
    def sort_name(self) -> str:
        return self.name_en or self.name_jp or f"\uffff {self.object_id}"

    @property
    def description(self):
        enum_items = self.bl_rna.properties["object_type"].enum_items  # type: ignore
        desc = enum_items.get(self.object_type).description
        if _is_ngs(self):
            desc += " (NGS)"

        return desc

    def populate(self, obj: objects.CmxObjectBase):
        self.object_type = str(obj.object_type)
        self.object_id = obj.id
        self.adjusted_id = obj.adjusted_id
        self.name_en = obj.name_en
        self.name_jp = obj.name_jp

        if isinstance(obj, objects.CmxBodyObject) and obj.leg_length is not None:
            self.leg_length = obj.leg_length
        else:
            self.leg_length = 0

        for field in fields(obj):
            if field.name in ("object_type", "id", "adjusted_id", "name_en", "name_jp"):
                continue

            name = field.name
            value = getattr(obj, name)

            if field.type in (float, float | None):
                prop = cast("FloatItem", self.float_fields.add())
                prop.name = name
                prop.value = math.nan if value is None else value

            elif field.type in (int, int | None):
                prop = cast("IntItem", self.float_fields.add())
                prop.name = name
                prop.value = IntItem.INVALID if value is None else value

            elif field.type is str:
                prop = cast("StringItem", self.string_fields.add())
                prop.name = name
                prop.value = value

            elif field.type == objects.CmxFileName:
                prop = cast("FileNameItem", self.files.add())
                prop.name = name
                prop.value = value.name

            elif field.type == objects.CmxColorMapping:
                prop = cast("ColorMapItem", self.color_map_fields.add())
                prop.name = name
                prop.red = int(value.red)
                prop.green = int(value.green)
                prop.blue = int(value.blue)
                prop.alpha = int(value.alpha)

            else:
                raise NotImplementedError(f"Unhandled field type {field.type}")

    def to_object(self):
        object_type = objects.ObjectType(self.object_type)
        cls = _get_object_class(object_type)
        obj = cls(
            object_type=object_type,
            id=self.object_id,
            adjusted_id=self.adjusted_id,
            name_en=self.name_en,
            name_jp=self.name_jp,
        )

        for file_item in self.files:
            setattr(obj, file_item.name, file_item.to_file_name())

        for float_item in self.float_fields:
            setattr(
                obj,
                float_item.name,
                None if math.isnan(float_item.value) else float_item.value,
            )

        for int_item in self.int_fields:
            setattr(
                obj,
                int_item.name,
                None if int_item.value == IntItem.INVALID else int_item.value,
            )

        for str_item in self.string_fields:
            setattr(obj, str_item.name, str_item.value)

        for color_item in self.color_map_fields:
            setattr(obj, color_item.name, color_item.to_color_map())

        return obj


def _get_object_class(object_type: objects.ObjectType) -> type[objects.CmxObjectBase]:
    match object_type:
        case objects.ObjectType.ACCESSORY:
            return objects.CmxAccessory
        case (
            objects.ObjectType.BASEWEAR
            | objects.ObjectType.COSTUME
            | objects.ObjectType.OUTERWEAR
        ):
            return objects.CmxBodyObject
        case (
            objects.ObjectType.CAST_ARMS
            | objects.ObjectType.CAST_BODY
            | objects.ObjectType.CAST_LEGS
        ):
            return objects.CmxBodyObject
        case objects.ObjectType.BODYPAINT | objects.ObjectType.INNERWEAR:
            return objects.CmxBodyPaint
        case objects.ObjectType.EAR:
            return objects.CmxEarObject
        case objects.ObjectType.EYE:
            return objects.CmxEyeObject
        case objects.ObjectType.EYEBROW | objects.ObjectType.EYELASH:
            return objects.CmxEyebrowObject
        case objects.ObjectType.FACE:
            return objects.CmxFaceObject
        case objects.ObjectType.FACE_TEXTURE | objects.ObjectType.FACEPAINT:
            return objects.CmxFacePaint
        case objects.ObjectType.HAIR:
            return objects.CmxHairObject
        case objects.ObjectType.HORN:
            return objects.CmxHornObject
        case objects.ObjectType.SKIN:
            return objects.CmxSkinObject
        case objects.ObjectType.STICKER:
            return objects.CmxSticker
        case objects.ObjectType.TEETH:
            return objects.CmxTeethObject
        case _:
            raise NotImplementedError(f"Unhandled item type {object_type}")


@classes.register
class PSO2_OT_ModelSearch(bpy.types.Operator, import_props.CommonImportProps):
    """Search for PSO2 character models"""

    bl_label = "Import PSO2 Character Model"
    bl_idname = "pso2.model_search"
    bl_options = {"REGISTER", "UNDO"}

    # Workaround for a bug: Python must keep a reference to any dynamic enum item
    # strings or Blender will show garbage. These strings need to not be garbage
    # collected as _get_selected_model_colors() gets called repeatedly, so keep
    # the enum items alive so long as the selected item doesn't change.
    _color_set_item_cache: ListItem | None = None
    _color_set_enum_cache: list[tuple[str, str, str, int]] = []

    def _get_selected_model_files(
        self,
        context: bpy.types.Context | None,
    ) -> Iterable[tuple[str, str, str]]:
        try:
            selected: ListItem = self.models[self.models_index]
        except IndexError:
            return []

        data_path = get_preferences(context).get_pso2_data_path()
        return _get_file_items(selected.files, data_path)

    def _get_selected_model_colors(
        self,
        context: bpy.types.Context | None,
    ) -> Iterable[tuple[str, str, str, int]]:
        if context is None:
            return []

        try:
            selected: ListItem = self.models[self.models_index]
        except IndexError:
            return []

        if selected == PSO2_OT_ModelSearch._color_set_item_cache:
            return PSO2_OT_ModelSearch._color_set_enum_cache

        items = _get_color_sets_enum(selected, context)

        PSO2_OT_ModelSearch._color_set_item_cache = selected
        PSO2_OT_ModelSearch._color_set_enum_cache = items

        return items

    def _update_color_set_colors(self, context: bpy.types.Context):
        try:
            item: ListItem = self.models[self.models_index]
        except IndexError:
            return

        if (
            color_set := _get_selected_color_set(item, int(self.color_set), context)
        ) and (
            channels := color_set.get_channels(objects.ObjectType(item.object_type))
        ):
            prop1 = COLOR_CHANNELS[channels[0]].prop
            prop2 = COLOR_CHANNELS[channels[1]].prop

            self.color_set_channel_1 = prop1
            self.color_set_channel_2 = prop2

            setattr(self, prop1, ccl.int_to_color(color_set.color1))
            setattr(self, prop2, ccl.int_to_color(color_set.color2))
        else:
            self.color_set_channel_1 = ""
            self.color_set_channel_2 = ""

    models: bpy.props.CollectionProperty(name="Models", type=ListItem)
    models_index: bpy.props.IntProperty(
        name="Selected Index", default=-1, update=_update_color_set_colors
    )
    model_file: bpy.props.EnumProperty(name="File", items=_get_selected_model_files)

    color_set: bpy.props.EnumProperty(
        name="Color Set",
        items=_get_selected_model_colors,
        update=_update_color_set_colors,
    )
    outer_color_1: color_property(ColorId.OUTER1, "Primary outerwear color")
    outer_color_2: color_property(ColorId.OUTER2, "Secondary outerwear color")
    base_color_1: color_property(ColorId.BASE1, "Primary basewear color")
    base_color_2: color_property(ColorId.BASE2, "Secondary basewear color")
    inner_color_1: color_property(ColorId.INNER1, "Primary innerwear color")
    inner_color_2: color_property(ColorId.INNER2, "Secondary innerwear color")

    color_set_channel_1: bpy.props.StringProperty()
    color_set_channel_2: bpy.props.StringProperty()

    def _handle_database_update(self, context: bpy.types.Context):
        _populate_model_list(self.models, context)

    handle_database_update: bpy.props.BoolProperty(update=_handle_database_update)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _populate_model_list(self.models, bpy.context)

    def __del__(self):
        PSO2_OT_ModelSearch._color_set_item_cache = None
        PSO2_OT_ModelSearch._color_set_enum_cache = []

    def draw(self, context):
        assert self.layout is not None

        preferences = get_preferences(context)
        layout = self.layout
        layout.context_pointer_set("parent", self)

        split = layout.split(factor=0.65)

        col = split.column()
        col.template_list(
            PSO2_UL_ModelList.bl_idname,
            "",
            self,
            "models",
            self,
            "models_index",
            rows=16,
        )

        col = split.column()
        col.use_property_split = True
        col.use_property_decorate = False

        if obj := self.get_selected_object():
            meta = ModelMetadata.from_object(obj, preferences.get_pso2_data_path())

            row = col.row()
            row.use_property_split = False
            row.prop(self, "model_file", expand=True)
            col.separator()

            # Colors
            if colors := sorted(obj.get_colors()):
                col.label(text="Colors", icon="COLOR")

                if _object_has_color_sets(obj, context):
                    flow = col.grid_flow(columns=1, align=True)
                    flow.use_property_split = False
                    flow.prop(self, "color_set", expand=True)

                    col.separator()

                flow = col.grid_flow(columns=2, row_major=True)
                flow.use_property_split = False

                for color in colors:
                    color_data, color_prop, color_enabled = self._get_color_prop(
                        context, color, preferences
                    )

                    color_row = flow.row()
                    color_row.enabled = color_enabled
                    color_row.prop(color_data, color_prop)

                col.separator()

            # Metadata
            if meta.leg_length or meta.has_linked_inner or meta.has_linked_outer:
                col.label(text="Metadata", icon="OBJECT_DATA")

                if meta.leg_length:
                    col.label(text=f"Leg length: {meta.leg_length:.3g}")

                grid = col.grid_flow(columns=2)

                if meta.has_linked_inner:
                    grid.label(text="Linked innerwear")

                if meta.has_linked_outer:
                    grid.label(text="Linked outerwear")

                col.separator()

            self.draw_import_props_column(col, preferences)
            col.separator(factor=4, type="LINE")

        col.operator(objects.PSO2_OT_UpdateCharacterDatabase.bl_idname)

    def execute(self, context) -> OperatorResult:
        if obj := self.get_selected_object():
            high_quality = self.model_file == "HQ"
            import_model.import_object(
                self,
                context,
                obj,
                high_quality=high_quality,
                options=self.get_object_options(obj),
            )
            return {"FINISHED"}

        return {"CANCELLED"}

    def invoke(self, context, event):
        assert context.window_manager is not None

        return context.window_manager.invoke_props_dialog(
            self, width=840, confirm_text="Import"
        )

    def get_selected_object(self):
        return _get_selected_object(self)

    def get_object_options(self, obj: objects.CmxObjectBase):
        options = super().get_options(
            ignore=(
                "models",
                "models_index",
                "model_file",
                "color_set",
                "color_set_channel_1",
                "color_set_channel_2",
                "outer_color_1",
                "outer_color_2",
                "base_color_1",
                "base_color_2",
                "inner_color_1",
                "inner_color_2",
            )
        )
        options["colors"] = self._get_color_set_dict(obj)
        return options

    def _get_color_set_dict(self, obj: objects.CmxObjectBase) -> dict[str, Color]:
        result = {}

        for color in obj.get_colors():
            channel = COLOR_CHANNELS[color]

            if channel.prop in (self.color_set_channel_1, self.color_set_channel_2):
                result[channel.custom_property_name] = getattr(self, channel.prop)

        return result

    def _get_color_prop(
        self,
        context: bpy.types.Context,
        color: ColorId,
        preferences: Pso2ToolsPreferences,
    ) -> tuple[Any, str, bool]:
        """Get (data, prop, enabled) for a color channel"""
        channel = COLOR_CHANNELS[color]

        # If this object has a color set, use the selected color set's colors (read-only)
        if channel.prop in (self.color_set_channel_1, self.color_set_channel_2):
            return self, channel.prop, False

        # If we've imported a model before, use the scene properties
        if hasattr(context.scene, channel.custom_property_name):
            return context.scene, channel.custom_property_name, True

        # Otherwise use the defaults from preferences
        return preferences, channel.prop, True


def _get_selected_object(self: PSO2_OT_ModelSearch) -> objects.CmxObjectBase | None:
    if self.models_index < 0:
        return None

    try:
        return self.models[self.models_index].to_object()
    except IndexError:
        return None


def _get_file_items(items: Iterable[FileNameItem], data_path: Path):
    item = next((item for item in items if item.name == "file"), None)
    if item is None:
        return

    normal = item.to_file_name()
    high = normal.ex

    if high.exists(data_path):
        yield ("HQ", "High Quality", "Select high quality model")

    if normal.exists(data_path):
        yield ("NQ", "Normal Quality", "Select normal quality model")


def _get_color_sets(item: ListItem, context: bpy.types.Context):
    with closing(objects.ObjectDatabase(context)) as db:
        return db.get_color_sets(item.object_type, item.adjusted_id)


def _color_set_enum_tuple(index: int, name: str) -> tuple[str, str, str, int]:
    return (str(index), name, f"Color variant: {name}", index)


def _get_color_sets_enum(item: ListItem, context: bpy.types.Context):
    color_sets = _get_color_sets(item, context)

    items = [_color_set_enum_tuple(i, s.name) for i, s in enumerate(color_sets.sets)]
    items.append(_color_set_enum_tuple(len(items), "Custom colors"))

    return items


def _get_selected_color_set(item: ListItem, index: int, context: bpy.types.Context):
    color_sets = _get_color_sets(item, context)

    try:
        return color_sets.sets[index]
    except IndexError:
        return None


def _object_has_color_sets(obj: objects.CmxObjectBase, context: bpy.types.Context):
    with closing(objects.ObjectDatabase(context)) as db:
        result = db.get_color_sets(obj.object_type, obj.adjusted_id)
        return bool(result.sets)


def _populate_model_list(collection, context: bpy.types.Context):
    start = time.monotonic()

    collection.clear()

    with closing(objects.ObjectDatabase(context)) as db:
        for obj in db.get_all():
            item: ListItem = collection.add()
            item.populate(obj)

    end = time.monotonic()
    debug_print(f"PSO2 items loaded in {end - start:0.1f}s")


def _false(item):
    return False


def _is_ngs(item: ListItem):
    if item.object_type in _VERSIONLESS_OBJECT_TYPES:
        return False

    return objects.is_ngs(item.object_id)


def _is_classic(item: ListItem):
    if item.object_type in _VERSIONLESS_OBJECT_TYPES:
        return False

    return not objects.is_ngs(item.object_id)


def _is_t1(item: ListItem):
    return objects.is_t1(item.object_id)


def _is_t2(item: ListItem):
    return objects.is_t2(item.object_id)


def _is_genderless(item: ListItem):
    return objects.is_genderless(item.object_id)


@classes.register
class PSO2_UL_ModelList(bpy.types.UIList):
    """PSO2 model list"""

    bl_idname = "PSO2_UL_ModelList"
    layout_type = "DEFAULT"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.use_filter_show = True

    def filter_items(self, context, data, property):  # noqa: A002 # type: ignore
        if property is None:
            raise TypeError()

        preferences = get_preferences(context)
        items: Sequence[ListItem] = getattr(data, property)

        if self.filter_name:
            # https://github.com/nutti/fake-bpy-module/issues/376
            flt_flags = cast(
                "list[int]",
                bpy.types.UI_UL_list.filter_items_by_name(
                    self.filter_name,
                    self.bitflag_filter_item,
                    items,
                    propname="item_name",
                ),
            )
        else:
            flt_flags = [self.bitflag_filter_item] * len(items)

        def hide_item(idx):
            flt_flags[idx] &= ~self.bitflag_filter_item

        if preferences.model_search_versions:
            should_hide_ngs = (
                _is_ngs if "NGS" not in preferences.model_search_versions else _false
            )
            should_hide_classic = (
                _is_classic
                if "CLASSIC" not in preferences.model_search_versions
                else _false
            )

            for idx, item in enumerate(items):
                if should_hide_ngs(item) or should_hide_classic(item):
                    hide_item(idx)

        if preferences.model_search_body_types:
            should_hide_t1 = (
                _is_t1 if "T1" not in preferences.model_search_body_types else _false
            )
            should_hide_t2 = (
                _is_t2 if "T2" not in preferences.model_search_body_types else _false
            )
            should_hide_genderless = (
                _is_genderless
                if "NONE" not in preferences.model_search_body_types
                else _false
            )

            for idx, item in enumerate(items):
                if item.object_type not in _GENDERED_OBJECT_TYPES:
                    continue

                if (
                    should_hide_t1(item)
                    or should_hide_t2(item)
                    or should_hide_genderless(item)
                ):
                    hide_item(idx)

        if preferences.model_search_categories:
            show_types = {
                x.strip()
                for enum in preferences.model_search_categories
                for x in enum.split("|")
            }
            for idx, item in enumerate(items):
                if str(item.object_type) not in show_types:
                    hide_item(idx)

        match preferences.model_search_sort:
            case "ALPHA":
                flt_neworder = bpy.types.UI_UL_list.sort_items_by_name(
                    items, "sort_name"
                )

            case "LEG_LENGTH":
                _sort = [
                    (idx, (item.leg_length, item.sort_name))
                    for idx, item in enumerate(items)
                ]
                flt_neworder = bpy.types.UI_UL_list.sort_items_helper(
                    _sort, lambda e: e[1]
                )

            case _:
                _sort = [(idx, item.object_id) for idx, item in enumerate(items)]
                flt_neworder = bpy.types.UI_UL_list.sort_items_helper(
                    _sort, lambda e: e[1]
                )

        return flt_flags, flt_neworder

    def draw_filter(self, context, layout):
        if layout is None:
            raise TypeError()

        preferences = get_preferences(context)

        row = layout.row(align=True)
        row.activate_init = True
        row.prop(self, "filter_name", text="", icon="VIEWZOOM")
        row.prop(preferences, "model_search_sort", expand=True, icon_only=True)

        row = layout.row(align=True)
        row.label(text="Filters")

        flow = layout.column_flow(columns=3)
        subrow = flow.row(align=True)
        subrow.prop(preferences, "model_search_versions", expand=True)

        subrow = flow.row(align=True)
        subrow.prop(preferences, "model_search_body_types", expand=True)
        flow.operator(PSO2_OT_SelectAllCategories.bl_idname)

        flow = layout.grid_flow(columns=4, align=True)
        flow.prop(preferences, "model_search_categories", expand=True)

    def draw_item(  # type: ignore
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
        if layout is None:
            raise TypeError()

        # Hack to keep the filter open
        self.use_filter_show = True

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            preferences = get_preferences(context)

            icon = _get_icon(objects.ObjectType(item.object_type))

            row = layout.split(factor=0.5)

            row.label(text=item.item_name, icon=icon)
            row.label(text=item.description)

            match preferences.model_search_sort:
                case "LEG_LENGTH":
                    row.label(text=f"{item.leg_length:.3g}", icon="MOD_LENGTH")

                case _:
                    row.label(text=str(item.object_id))

        elif self.layout_type == "GRID":
            pass


def _get_icon(object_type: objects.ObjectType) -> BlenderIcon:
    match object_type:
        case objects.ObjectType.ACCESSORY:
            return "MESH_TORUS"
        case (
            objects.ObjectType.BASEWEAR
            | objects.ObjectType.COSTUME
            | objects.ObjectType.OUTERWEAR
        ):
            return "MATCLOTH"
        case (
            objects.ObjectType.CAST_ARMS
            | objects.ObjectType.CAST_BODY
            | objects.ObjectType.CAST_LEGS
        ):
            return "MATCLOTH"
        case objects.ObjectType.BODYPAINT | objects.ObjectType.INNERWEAR:
            return "TEXTURE"
        case objects.ObjectType.EAR:
            return "USER"
        case objects.ObjectType.EYE:
            return "HIDE_OFF"
        case objects.ObjectType.EYEBROW | objects.ObjectType.EYELASH:
            return "HIDE_OFF"
        case objects.ObjectType.FACE:
            return "USER"
        case objects.ObjectType.FACE_TEXTURE | objects.ObjectType.FACEPAINT:
            return "USER"
        case objects.ObjectType.HAIR:
            return "USER"
        case objects.ObjectType.HORN:
            return "USER"
        case objects.ObjectType.SKIN:
            return "TEXTURE"
        case objects.ObjectType.STICKER:
            return "TEXTURE"
        case objects.ObjectType.TEETH:
            return "USER"
        case _:
            raise NotImplementedError(f"Unhandled item type {object_type}")


@classes.register
class PSO2_OT_SelectAllCategories(bpy.types.Operator):
    """Select All Categories"""

    bl_label = "Select All"
    bl_idname = "pso2.select_all_categories"
    bl_options = {"INTERNAL"}

    def execute(self, context) -> OperatorResult:
        preferences = get_preferences(context)

        preferences.model_search_versions = _get_all_enum_items(
            preferences, "model_search_versions"
        )

        preferences.model_search_categories = _get_all_enum_items(
            preferences, "model_search_categories"
        )

        preferences.model_search_body_types = _get_all_enum_items(
            preferences, "model_search_body_types"
        )

        return {"FINISHED"}


def _get_all_enum_items(obj: bpy.types.bpy_struct, prop: str) -> set[str]:
    return {enum.identifier for enum in obj.bl_rna.properties[prop].enum_items.values()}  # type: ignore
