from typing import Any, Optional, Set

import bpy
from bpy.types import Context, UILayout

from . import classes
from .preferences import get_preferences
from .object_info import ModelPart, ObjectCategory, ObjectInfo, ObjectType
from .import_model import ImportProperties
from .filelist import (
    VARIANT_HIGH_QUALITY,
    VARIANT_NORMAL_QUALITY,
    VARIANT_REPLACEMENT,
    Category,
    FileGroup,
    find_ice_file,
    get_file_groups,
    update_file_lists,
)


@classes.register_class
class IceFileGroup(bpy.types.PropertyGroup):
    variant: bpy.props.StringProperty(name="Variant")
    files: bpy.props.StringProperty(name="Files")


@classes.register_class
class ListItem(bpy.types.PropertyGroup):
    category: bpy.props.StringProperty(name="Category")
    name: bpy.props.StringProperty(name="Name")
    object_type: bpy.props.StringProperty(name="Object Type")
    object_id: bpy.props.IntProperty(name="ID")
    part: bpy.props.StringProperty(name="Model Part")
    files: bpy.props.CollectionProperty(type=IceFileGroup)

    def get_object_info(self):
        return ObjectInfo(
            name=self.name,
            category=ObjectCategory.PLAYER,  # TODO
            object_type=ObjectType(self.object_type) if self.object_type else None,
            object_id=self.object_id,
            part=ModelPart(self.part) if self.part else None,
        )

    @property
    def description(self):
        return (
            self.get_object_info().description or _get_category_info(self.category)[0]
        )


def _get_variant(group: IceFileGroup):
    variants = [VARIANT_HIGH_QUALITY, VARIANT_NORMAL_QUALITY, VARIANT_REPLACEMENT]
    return variants[variants.index(group.variant)]


@classes.register_class
class PSO2_OT_ModelSearch(bpy.types.Operator, ImportProperties):
    """Search for PSO2 models"""

    bl_label = "Import PSO2 Item"
    bl_idname = "pso2tools.model_search"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    models: bpy.props.CollectionProperty(name="Items", type=ListItem)
    models_index: bpy.props.IntProperty(name="Selected Index")

    def _get_variant_items(self, context: bpy.types.Context):
        try:
            selected = self.models[self.models_index]
            return [
                (_get_variant(item), _get_variant(item), "") for item in selected.files
            ]
        except IndexError:
            return []

    variant: bpy.props.EnumProperty(name="Variant", items=_get_variant_items)

    def __init__(self):
        super().__init__()
        _populate_model_list(self.models)

    def get_selected_model(self) -> Optional[ListItem]:
        try:
            return self.models[self.models_index]
        except IndexError:
            return None

    def get_filepath(self):
        raise RuntimeError("Item search does not use filepath")

    def get_object_info(self):
        if selected := self.get_selected_model():
            return selected.get_object_info()

        return ObjectInfo()

    def draw(self, context: bpy.types.Context) -> None:
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
            rows=10,
        )

        col = split.column()
        col.prop(self, "variant")

        col.context_pointer_set("active_operator", self)

        col.label(text="Textures")
        box = col.box()
        self.draw_texture_props(context, box)

        col.label(text="Armature")
        box = col.box()
        self.draw_armature_props(context, box)

        col.separator()
        col.operator(PSO2_OT_RebuildFileList.bl_idname, text="Update File List (slow)")

    def execute(self, context: bpy.types.Context) -> Set[str]:
        if selection := self.get_selected_model():
            variant = next(
                (item for item in selection.files if item.variant == self.variant),
                selection.files[0],
            )

            for filehash in variant.files.split(","):
                if path := find_ice_file(context, filehash):
                    self.import_ice(self, context, path)
                else:
                    self.report({"ERROR"}, f"Could not find file {filehash}")

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        return context.window_manager.invoke_props_dialog(self, width=800)


@classes.register_class
class PSO2_OT_RebuildFileList(bpy.types.Operator):
    """Update cached model list"""

    bl_label = "Update File List"
    bl_idname = "pso2tools.rebuild_file_list"

    def execute(self, context: Context) -> Set[str]:
        result = update_file_lists(self, context)

        _populate_model_list(context.parent.models)

        return result


def _file_group_key(group: FileGroup):
    key = group.name.lower()

    if key and not key[0].isalnum():
        key = "zzzz " + key

    return key


def _populate_model_list(collection):
    collection.clear()

    for group in sorted(get_file_groups(), key=_file_group_key):
        item: ListItem = collection.add()
        item.category = group.category
        item.name = group.name
        item.object_type = group.object_type or ""
        item.object_id = group.object_id
        item.part = group.part or ""

        for key, files in group.files.items():
            prop: IceFileGroup = item.files.add()
            prop.variant = key
            prop.files = ",".join(files)


_CATEGORY_INFO: dict[Category, tuple[str, str]] = {
    Category.NgsOutfit: ("Outfit (NGS)", "MOD_CLOTH"),
    Category.NgsCastPart: ("Cast Part (NGS)", "MOD_CLOTH"),
    Category.NgsHeadPart: ("Head Part (NGS)", "USER"),
    Category.NgsBodyPaint: ("Body Paint (NGS)", "TEXTURE"),
    Category.NgsMag: ("Mag (NGS)", "GHOST_DISABLED"),
    Category.NgsOther: ("Other (NGS)", "AUTO"),
    Category.ClassicOutfit: ("Outfit (Classic)", "MOD_CLOTH"),
    Category.ClassicCastPart: ("Cast Part (Classic)", "MOD_CLOTH"),
    Category.ClassicHeadPart: ("Head Part (Classic)", "USER"),
    Category.ClassicBodyPaint: ("Body Paint (Classic)", "TEXTURE"),
    Category.ClassicMag: ("Mag (Classic)", "GHOST_DISABLED"),
    Category.ClassicOther: ("Other (Classic)", "AUTO"),
    Category.Accessory: ("Accessory", "MESH_TORUS"),
    Category.Sticker: ("Sticker", "TEXTURE"),
    Category.Room: ("Room (Classic)", "HOME"),
    Category.MySpace: ("My Space (NGS)", "WORLD"),
    Category.NgsEnemies: ("Enemy (NGS)", "MONKEY"),
    Category.ClassicEnemies: ("Enemy (Classic)", "MONKEY"),
}


def _get_category_info(category: Category) -> tuple[str, str]:
    if info := _CATEGORY_INFO.get(category):
        return info
    return ("", "NONE")


def _get_enum_item(category: Category):
    text, icon = _get_category_info(category)
    index = 1 << list(Category).index(category)

    return (category, text, "", icon, index)


@classes.register_class
class PSO2_UL_ModelList(bpy.types.UIList):
    """PSO2 model list"""

    bl_idname = "PSO2_UL_ModelList"
    layout_type = "DEFAULT"

    categories: bpy.props.EnumProperty(
        name="Model Categories",
        options={"ENUM_FLAG"},
        items=(
            _get_enum_item(Category.NgsOutfit),
            _get_enum_item(Category.NgsCastPart),
            _get_enum_item(Category.NgsHeadPart),
            _get_enum_item(Category.NgsBodyPaint),
            _get_enum_item(Category.Accessory),
            _get_enum_item(Category.ClassicOutfit),
            _get_enum_item(Category.ClassicCastPart),
            _get_enum_item(Category.ClassicHeadPart),
            _get_enum_item(Category.ClassicBodyPaint),
            _get_enum_item(Category.Sticker),
            _get_enum_item(Category.MySpace),
            _get_enum_item(Category.Room),
            _get_enum_item(Category.NgsMag),
            _get_enum_item(Category.ClassicMag),
            _get_enum_item(Category.ClassicOther),
            _get_enum_item(Category.NgsOther),
            _get_enum_item(Category.NgsEnemies),
            _get_enum_item(Category.ClassicEnemies),
        ),
        description="Filter by object category",
        default=set(),
    )

    def filter_items(self, context: Context, data: Any, prop: str) -> None:
        items = getattr(data, prop)

        if not items:
            return [], []

        if self.filter_name:
            flt_flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item, items, propname="name"
            )
        else:
            flt_flags = [self.bitflag_filter_item] * len(items)

        if self.categories:
            for idx, item in enumerate(items):
                if not item.category in self.categories:
                    flt_flags[idx] &= ~self.bitflag_filter_item

        return flt_flags, []

    def draw_filter(self, context: Context, layout: UILayout) -> None:
        row = layout.row(align=True)
        # This does activate the text field, but then it doesn't work correctly
        # https://projects.blender.org/blender/blender/issues/109710
        # row.activate_init = True
        row.prop(self, "filter_name", text="", icon="VIEWZOOM")

        row = layout.row(align=True)
        row.label(text="Item Categories:")

        flow = layout.grid_flow(columns=4, align=True)
        flow.context_pointer_set("parent", self)
        flow.prop(self, "categories", expand=True)
        flow.operator(PSO2_OT_AllCategories.bl_idname)

    def draw_item(
        self,
        context: Context,
        layout: UILayout,
        data: Any,
        item: ListItem,
        icon: int,
        active_data: Any,
        active_property: str,
        index: int = 0,
        flt_flag: int = 0,
    ) -> None:
        # Hack to keep the filter open
        self.use_filter_show = True

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            category, icon = _get_category_info(item.category)
            layout.label(text=item.name, icon=icon)
            layout.label(text=item.description)

            if get_preferences(context).debug:
                debug_text = f"{item.object_type}_{item.object_id}_{item.part}"
                debug_text = debug_text.removesuffix("_")
                layout.label(text=debug_text)

        elif self.layout_type == "GRID":
            pass


@classes.register_class
class PSO2_OT_AllCategories(bpy.types.Operator):
    """Unselect All Categories"""

    bl_label = "Clear"
    bl_idname = "pso2tools.select_all_categories"

    def execute(self, context: Context) -> Set[str]:
        context.parent.categories = set()

        return {"FINISHED"}
