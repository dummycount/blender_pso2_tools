try:
    from enum import StrEnum
except ImportError:
    from .strenum import StrEnum

class Category(StrEnum):
    NgsOutfit = "NGS_OUTFIT"
    NgsCastPart = "NGS_CAST"
    NgsHeadPart = "NGS_HEAD"
    NgsBodyPaint = "NGS_PAINT"
    NgsMag = "NGS_MAG"
    NgsOther = "NGS_OTHER"

    ClassicOutfit = "CLASSIC_OUTFIT"
    ClassicCastPart = "CLASSIC_CAST"
    ClassicHeadPart = "CLASSIC_HEAD"
    ClassicBodyPaint = "CLASSIC_PAINT"
    ClassicMag = "CLASSIC_MAG"
    ClassicOther = "CLASSIC_OTHER"

    Accessory = "ACCESSORY"
    Sticker = "STICKER"
    Room = "ROOM"
    MySpace = "MY_SPACE"

    NgsEnemies = "NGS_ENEMY"
    ClassicEnemies = "CLASSIC_ENEMY"

    # TODO: add motions


ALL_CATEGORIES = set(str(value) for value in Category)

CATEGORY_INFO: dict[Category, tuple[str, str]] = {
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

def get_category_info(category: Category) -> tuple[str, str]:
    if info := CATEGORY_INFO.get(category):
        return info
    return ("", "NONE")


def get_category_enum(category: Category):
    text, icon = get_category_info(category)
    index = 1 << list(Category).index(category)

    return (category, text, "", icon, index)