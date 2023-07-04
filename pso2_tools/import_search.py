from typing import Any, Set

import bpy
from bpy.types import Context, UILayout

from .import_model import ImportProperties, PSO2_PT_import_textures

from .filelist import (
    ALL_CATEGORIES,
    VARIANT_HIGH_QUALITY,
    VARIANT_NORMAL_QUALITY,
    VARIANT_REPLACEMENT,
    Category,
    FileGroup,
    find_ice_file,
    get_file_groups,
    update_file_lists,
)

from . import classes


@classes.register_class
class IceFileGroup(bpy.types.PropertyGroup):
    variant: bpy.props.StringProperty(name="Variant")
    files: bpy.props.StringProperty(name="Files")


@classes.register_class
class ListItem(bpy.types.PropertyGroup):
    category: bpy.props.StringProperty(name="Category")
    name: bpy.props.StringProperty(name="Name")
    files: bpy.props.CollectionProperty(type=IceFileGroup)


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
        if selected := self.models[self.models_index]:
            return [
                (_get_variant(item), _get_variant(item), "") for item in selected.files
            ]

        return []

    variant: bpy.props.EnumProperty(name="Variant", items=_get_variant_items)

    def __init__(self):
        super().__init__()
        _populate_model_list(self.models)

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
        col.operator(PSO2_OT_RebuildFileList.bl_idname, text="Rebuild File List (slow)")

        col = split.column()
        col.prop(self, "variant")

        col.context_pointer_set("active_operator", self)

        col.label(text="Textures")
        box = col.box()
        self.draw_texture_props(context, box)

        col.label(text="Armature")
        box = col.box()
        self.draw_armature_props(context, box)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        selection: ListItem = self.models[self.models_index]
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
    for group in sorted(get_file_groups(), key=_file_group_key):
        item: ListItem = collection.add()
        item.category = group.category
        item.name = group.name

        for key, files in group.files.items():
            prop: IceFileGroup = item.files.add()
            prop.variant = key
            prop.files = ",".join(files)


_CATEGORY_ICONS = {
    Category.NgsOutfit: "MOD_CLOTH",
    Category.NgsCastPart: "MOD_CLOTH",
    Category.NgsFacePart: "USER",
    Category.NgsBodyPaint: "TEXTURE",
    Category.NgsMag: "GHOST_DISABLED",
    Category.NgsOther: "AUTO",
    Category.ClassicOutfit: "MOD_CLOTH",
    Category.ClassicCastPart: "MOD_CLOTH",
    Category.ClassicFacePart: "USER",
    Category.ClassicBodyPaint: "TEXTURE",
    Category.ClassicMag: "GHOST_DISABLED",
    Category.ClassicOther: "AUTO",
    Category.Accessory: "MESH_TORUS",
    Category.Room: "HOME",
    Category.MySpace: "WORLD",
    Category.NgsEnemies: "MONKEY",
    Category.ClassicEnemies: "MONKEY",
}


def _get_icon(category: Category):
    return _CATEGORY_ICONS.get(category, "NONE")


def _get_enum_item(category: Category, text: str):
    index = 1 << list(Category).index(category)
    return (category, text, "", _get_icon(category), index)


@classes.register_class
class PSO2_UL_ModelList(bpy.types.UIList):
    """PSO2 model list"""

    bl_idname = "PSO2_UL_ModelList"
    layout_type = "DEFAULT"

    categories: bpy.props.EnumProperty(
        name="Model Categories",
        options={"ENUM_FLAG"},
        items=(
            _get_enum_item(Category.NgsOutfit, "Outfits (NGS)"),
            _get_enum_item(Category.NgsCastPart, "Cast Parts (NGS)"),
            _get_enum_item(Category.NgsFacePart, "Face Parts (NGS)"),
            _get_enum_item(Category.NgsBodyPaint, "Body Paint (NGS)"),
            _get_enum_item(Category.MySpace, "My Space (NGS)"),
            _get_enum_item(Category.ClassicOutfit, "Outfits (Classic)"),
            _get_enum_item(Category.ClassicCastPart, "Cast Parts (Classic)"),
            _get_enum_item(Category.ClassicFacePart, "Face Parts (Classic)"),
            _get_enum_item(Category.ClassicBodyPaint, "Body Paint (Classic)"),
            _get_enum_item(Category.Room, "Room (Classic)"),
            _get_enum_item(Category.Accessory, "Accessories"),
            _get_enum_item(Category.NgsMag, "Mags (NGS)"),
            _get_enum_item(Category.ClassicMag, "Mags (Classic)"),
            _get_enum_item(Category.ClassicOther, "Other (Classic)"),
            _get_enum_item(Category.NgsOther, "Other (NGS)"),
            _get_enum_item(Category.NgsEnemies, "Enemies (NGS)"),
            _get_enum_item(Category.ClassicEnemies, "Enemies (Classic)"),
        ),
        description="Filter by object category",
        default=ALL_CATEGORIES,
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

        for idx, item in enumerate(items):
            if not item.category in self.categories:
                flt_flags[idx] &= ~self.bitflag_filter_item

        return flt_flags, []

    def draw_filter(self, context: Context, layout: UILayout) -> None:
        row = layout.row(align=True)
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
        item: Any,
        icon: int,
        active_data: Any,
        active_property: str,
        index: int = 0,
        flt_flag: int = 0,
    ) -> None:
        # Hack to keep the filter open
        self.use_filter_show = True

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.label(text=item.name, icon=_get_icon(item.category))

        elif self.layout_type == "GRID":
            pass


@classes.register_class
class PSO2_OT_AllCategories(bpy.types.Operator):
    """Select All Categories"""

    bl_label = "All Categories"
    bl_idname = "pso2tools.select_all_categories"

    def execute(self, context: Context) -> Set[str]:
        context.parent.categories = ALL_CATEGORIES

        return {"FINISHED"}
