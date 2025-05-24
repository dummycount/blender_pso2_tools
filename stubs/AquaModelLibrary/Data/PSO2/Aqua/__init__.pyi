import typing

from AquaModelLibrary.Data.PSO2.Aqua.CharacterMakingIndexData import (
    ACCEObject,
    BBLYObject,
    BCLNObject,
    BODYObject,
    CMXTable,
    EYEBObject,
    EYEObject,
    FACEObject,
    FaceTextureObject,
    FCMNObject,
    FCPObject,
    HAIRObject,
    NGS_EarObject,
    NGS_HornObject,
    NGS_SKINObject,
    NGS_TeethObject,
    NIFL_COLObject,
    Part6_7_22Obj,
    StickerObject,
    Unk_IntField,
    VTBF_COLObject,
)
from AquaModelLibrary.Helpers.Readers import BufferedStreamReaderBE_1
from System import Array_1
from System.Collections.Generic import Dictionary_2, List_1
from System.IO import MemoryStream

class CharacterMakingIndex(AquaCommon):
    pcDirectory: bool
    dataDir: str
    dataNADir: str
    dataReboot: str
    dataRebootNA: str

    dataDirPC: str
    dataDirConsole: str
    dataNADirPC: str
    dataNADirConsole: str
    dataRebootPC: str
    dataRebootConsole: str
    dataRebootNAPC: str
    dataRebootNAConsole: str

    costumeDict: Dictionary_2[int, BODYObject]
    carmDict: Dictionary_2[int, BODYObject]
    clegDict: Dictionary_2[int, BODYObject]
    outerDict: Dictionary_2[int, BODYObject]

    baseWearDict: Dictionary_2[int, BODYObject]
    innerWearDict: Dictionary_2[int, BBLYObject]
    bodyPaintDict: Dictionary_2[int, BBLYObject]
    stickerDict: Dictionary_2[int, StickerObject]

    faceDict: Dictionary_2[int, FACEObject]
    fcmnDict: Dictionary_2[int, FCMNObject]
    faceTextureDict: Dictionary_2[int, FaceTextureObject]
    fcpDict: Dictionary_2[int, FCPObject]

    accessoryDict: Dictionary_2[int, ACCEObject]
    eyeDict: Dictionary_2[int, EYEObject]
    ngsEarDict: Dictionary_2[int, NGS_EarObject]
    ngsTeethDict: Dictionary_2[int, NGS_TeethObject]

    ngsHornDict: Dictionary_2[int, NGS_HornObject]
    ngsSkinDict: Dictionary_2[int, NGS_SKINObject]
    eyebrowDict: Dictionary_2[int, EYEBObject]
    eyelashDict: Dictionary_2[int, EYEBObject]

    hairDict: Dictionary_2[int, HAIRObject]
    colDict: Dictionary_2[int, NIFL_COLObject]
    legacyColDict: Dictionary_2[int, VTBF_COLObject]

    unkList: List_1[Unk_IntField]
    costumeIdLink: Dictionary_2[int, BCLNObject]

    castArmIdLink: Dictionary_2[int, BCLNObject]
    clegIdLink: Dictionary_2[int, BCLNObject]
    outerWearIdLink: Dictionary_2[int, BCLNObject]
    baseWearIdLink: Dictionary_2[int, BCLNObject]

    innerWearIdLink: Dictionary_2[int, BCLNObject]
    castHeadIdLink: Dictionary_2[int, BCLNObject]
    accessoryIdLink: Dictionary_2[int, BCLNObject]

    part6_7_22Dict: Dictionary_2[int, Part6_7_22Obj]

    cmxTable: CMXTable

    @typing.overload
    def __init__(self): ...
    @typing.overload
    def __init__(self, file: Array_1[int], _ext: str): ...
    @typing.overload
    def __init__(self, streamReader: BufferedStreamReaderBE_1[MemoryStream]): ...

class PSO2Text(AquaCommon):
    class TextPair:
        name: str
        str: str

    categoryNames: List_1[str]
    text: List_1[List_1[List_1[TextPair]]]  # Category, subCategory, id

    @typing.overload
    def __init__(self): ...
    @typing.overload
    def __init__(self, file: Array_1[int]): ...
    @typing.overload
    def __init__(self, sr: BufferedStreamReaderBE_1[MemoryStream]): ...
    @typing.overload
    def __init__(self, filename: str): ...
    def ToString(self) -> str: ...
