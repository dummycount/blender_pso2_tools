import typing
from typing import Any

from System.Collections.Generic import List

class BaseCMXObject:
    num: int
    originalOffset: int

class ACCE:
    pass  # TODO

class ACCE_Feb8_22:
    pass  # TODO

class ACCE_B:
    pass  # TODO

class ACCE2A:
    unkFloatNeg1: float
    unkFloat0: float
    unkFloat1: float

    unkFloat2: float
    shoeAcceHeight: float
    unkFloat4: float
    unkFloat5: float

class ACCE2B:
    pass  # TODO

class ACCEV2:
    pass  # TODO

class ACCE12_4_24:
    pass  # TODO

class ACCE_12Object:
    pass  # TODO

class ACCEObject(BaseCMXObject):
    acce: ACCE
    acceB: ACCE_B
    acceFeb8_22: ACCE_Feb8_22
    acce2a: ACCE2A
    flt_54: float
    acce2b: ACCE2B
    acce12List: List[ACCE_12Object]
    accev2: ACCEV2
    acce12_4_24: ACCE12_4_24
    effectNamePtr: int
    flt_90: float

    dataString: str
    nodeAttach1: str
    nodeAttach2: str
    nodeAttach3: str
    nodeAttach4: str
    nodeAttach5: str
    nodeAttach6: str
    nodeAttach7: str
    nodeAttach8: str
    nodeAttach9: str
    nodeAttach10: str
    nodeAttach11: str
    nodeAttach12: str
    nodeAttach13: str
    nodeAttach14: str
    nodeAttach15: str
    nodeAttach16: str
    nodeAttach17: str
    nodeAttach18: str
    effectName: str

class BBLY:
    pass  # TODO

class BBLYObject(BaseCMXObject):
    bbly: BBLY
    texString1: str
    texString2: str
    texString3: str
    texString4: str
    texString5: str

class BCLN:
    id: int
    fileId: int
    unkInt: int

class BCLNRitem:
    int_00: int
    int_04: int
    int_08: int
    int_0C: int

class BCLNRitem2:
    int_00: int
    int_04: int

class BCLNObject(BaseCMXObject):
    bcln: BCLN
    bclnRitem: BCLNRitem
    bclnRitem2: BCLNRitem2

class BODY:
    id: int
    dataStringPtr: int
    texString1Ptr: int
    texString2Ptr: int
    texString3Ptr: int
    texString4Ptr: int
    texString5Ptr: int
    texString6Ptr: int
    string7Ptr: int

class BODY2:
    int_24_0x9_0x9: int
    int_28: int
    int_2C: int
    costumeSoundId: int
    headId: int
    int_38: int
    linkedOuterId: int
    linkedInnerId: int
    int_44: int
    legLength: float
    float_4C_0xB: float
    float_50: float
    float_54: float
    float_58: float
    float_5C: float
    float_60: float
    int_64: int

class BODY40Cap:
    float_78: float
    float_7C: float

class BODY2023_1:
    nodeStrPtr_0: int
    nodeStrPtr_1: int

class BODYVer2:
    nodeStrPtr_2: int
    flt_8C: float
    flt_90: float
    flt_94: float
    flt_98: float

class BODY12_4_24:
    unkInt0: int
    unkInt1: int
    unkInt2: int

class CharColorMapping(typing.SupportsInt):
    @typing.overload
    def __init__(self, value: int) -> None: ...
    @typing.overload
    def __init__(self, value: int, force_if_true: bool) -> None: ...
    def __int__(self) -> int: ...

    PrimaryOuterWear: "CharColorMapping"  # 1
    SecondaryOuterWear: "CharColorMapping"  # 2
    PrimaryBaseWear: "CharColorMapping"  # 3
    SecondaryBaseWear: "CharColorMapping"  # 4
    PrimaryInnerWear: "CharColorMapping"  # 5
    SecondaryInnerWear: "CharColorMapping"  # 6
    CastColor1: "CharColorMapping"  # 7
    CastColor2: "CharColorMapping"  # 8
    CastColor3: "CharColorMapping"  # 9
    CastColor4: "CharColorMapping"  # 10
    MainSkin: "CharColorMapping"  # 11
    SubSkin: "CharColorMapping"  # 12
    RightEye: "CharColorMapping"  # 13
    LeftEye: "CharColorMapping"  # 14
    EyebrowColor: "CharColorMapping"  # 15
    EyelashColor: "CharColorMapping"  # 16
    HairColor: "CharColorMapping"  # 17

class BODYMaskColorMapping:
    redIndex: CharColorMapping
    greenIndex: CharColorMapping
    blueIndex: CharColorMapping
    alphaIndex: CharColorMapping

class BODYObject(BaseCMXObject):
    body: BODY
    byteId_0: int
    byteId_1: int
    byteId_2: int
    byteId_3: int
    bodyMaskColorMapping: BODYMaskColorMapping
    body2: BODY2
    body40cap: BODY40Cap
    body2023_1: BODY2023_1
    bodyVer2: BODYVer2
    body12_4_24: BODY12_4_24
    body2_5_25: int

    dataString: str
    texString1: str
    texString2: str
    texString3: str
    texString4: str
    texString5: str
    texString6: str
    string7: str
    nodeString0: str
    nodeString1: str
    nodeString2: str

class CMXTable:
    bodyAddress: int
    carmAddress: int
    clegAddress: int
    bodyOuterAddress: int
    baseWearAddress: int
    innerWearAddress: int
    bodyPaintAddress: int
    stickerAddress: int
    faceAddress: int
    faceMotionAddress: int
    faceTextureAddress: int
    faceTexturesAddress: int
    accessoryAddress: int
    eyeTextureAddress: int
    earAddress: int
    teethAddress: int
    hornAddress: int
    skinAddress: int
    eyebrowAddress: int
    eyelashAddress: int
    hairAddress: int
    colAddress: int
    unkAddress: int
    costumeIdLinkAddress: int
    castArmIdLinkAddress: int
    castLegIdLinkAddress: int
    outerIdLinkAddress: int
    baseWearIdLinkAddress: int
    innerWearIdLinkAddress: int
    oct21UnkAddress: int
    jun7_22Address: int
    feb8_22UnkAddress: int

    bodyCount: int
    carmCount: int
    clegCount: int
    bodyOuterCount: int
    baseWearCount: int
    innerWearCount: int
    bodyPaintCount: int
    stickerCount: int
    faceCount: int
    faceMotionCount: int
    faceTextureCount: int
    faceTexturesCount: int
    accessoryCount: int
    eyeTextureCount: int
    earCount: int
    teethCount: int
    hornCount: int
    skinCount: int
    eyebrowCount: int
    eyelashCount: int
    hairCount: int
    colCount: int
    unkCount: int
    costumeIdLinkCount: int
    castArmIdLinkCount: int
    castLegIdLinkCount: int
    outerIdLinkCount: int
    baseWearIdLinkCount: int
    innerWearIdLinkCount: int
    oct21UnkCount: int
    jun7_22Count: int
    feb8_22UnkCount: int

class EYE:
    id: int
    texString1Ptr: int
    texString2Ptr: int
    texString3Ptr: int
    texString4Ptr: int
    texString5Ptr: int
    unkFloat0: float
    unkFloat1: float

class EYEObject(BaseCMXObject):
    eye: EYE
    texString1: str
    texString2: str
    texString3: str
    texString4: str
    texString5: str

class EYEB:
    pass  # TODO

class EYEBObject(BaseCMXObject):
    eyeb: EYEB
    texString1: str
    texString2: str
    texString3: str
    texString4: str

class FACE:
    pass  # TODO

class FACERitem:
    pass  # TODO

class FACE2:
    pass  # TODO

class FACE2Split:
    pass  # TODO

class FACE3:
    pass  # TODO

class FACEObject(BaseCMXObject):
    face: FACE
    faceRitem: FACERitem
    face2: FACE2
    unkOct12024Int: int
    face2Split: FACE2Split
    unkFloatRitem: float
    unkVer2Int: int
    face3: FACE3

    dataString: str
    texString1: str
    texString2: str
    texString3: str
    texString4: str
    texString5: str
    texString6: str
    dataString2: str

class FaceTextures:
    pass  # TODO

class FaceTextureObject(BaseCMXObject):
    ngsFace: FaceTextures
    texString1: str
    texString2: str
    texString3: str
    texString4: str

class HAIR:
    id: int
    dataStringPtr: int
    texString1Ptr: int
    texString2Ptr: int
    texString3Ptr: int
    texString4Ptr: int
    texString5Ptr: int
    texString6Ptr: int
    texString7Ptr: int
    unkIntB1: int
    unkInt1: int
    unkInt2: int
    unkFloat0: float
    unkFloat1: float
    unkFloat2: float
    unkFloat3: float
    unkInt3: int
    unkInt4: int
    unkInt5: int
    unkInt6: int
    unkInt7: int
    unkInt8: int
    unkFloat4: float
    unkFloat5: float
    unkFloat6: float
    unkInt9: int
    unkInt10: int
    unkInt11: int
    unkInt12: int
    unkInt13: int
    unkInt14: int
    unkFloat7: float
    unkFloat8: float
    unkFloat9: float
    unkInt15: int
    unkInt16: int
    unkInt17: int
    unkInt18: int
    unkInt19: int
    unkInt20: int
    unkShortB1: int
    unkShortB2: int
    unkShortB3: int
    unkShort0: int

class HAIRObject(BaseCMXObject):
    hair: HAIR
    dataString: str
    texString1: str
    texString2: str
    texString3: str
    texString4: str
    texString5: str
    texString6: str
    texString7: str

class FCMN:
    pass  # TODO

class FCMNObject(BaseCMXObject):
    fcmn: FCMN
    proportionAnim: str
    faceAnim1: str
    faceAnim2: str
    faceAnim3: str
    faceAnim4: str
    faceAnim5: str
    faceAnim6: str
    faceAnim7: str
    faceAnim8: str
    faceAnim9: str
    faceAnim10: str

class FCP:
    pass  # TODO

class FCPObject(BaseCMXObject):
    fcp: FCP
    texString1: str
    texString2: str
    texString3: str
    texString4: str

class NGS_Ear:
    id: int
    dataStringPtr: int
    texString1Ptr: int
    texString2Ptr: int
    texString3Ptr: int
    texString4Ptr: int
    texString5Ptr: int
    unkInt0: int
    unkInt1: int
    unkInt2: int
    unkInt3: int
    unkInt4: int

class NGS_EarObject(BaseCMXObject):
    ngsEar: NGS_Ear
    texString1: str
    texString2: str
    texString3: str
    texString4: str
    texString5: str

class NGS_Horn:
    id: int
    dataStringPtr: int
    reserve0: int

class NGS_HornObject(BaseCMXObject):
    ngsHorn: NGS_Horn
    dataString: str

class NGS_Skin:
    pass  # TODO

class Skin_12_4_24:
    pass  # TODO

class NGS_SKINObject(BaseCMXObject):
    ngsSkin: NGS_Skin
    skin12_4_24: Skin_12_4_24
    texString1: str
    texString2: str
    texString3: str
    texString4: str
    texString5: str
    texString6: str
    texString7: str
    texString8: str
    texString9: str
    texString10: str
    texString11: str
    texString12: str
    texString13: str
    texString14: str

class NGS_Teeth:
    pass  # TODO

class NGS_TeethObject(BaseCMXObject):
    ngsTeeth: NGS_Teeth
    texString1: str
    texString2: str
    texString3: str
    texString4: str

class NIFL_COL:
    id: int
    textStringPtr: int
    colorData: bytes

class NIFL_COLObject(BaseCMXObject):
    niflCol: NIFL_COL
    textString: str

class Part6_7_22:
    pass  # TODO

class Part6_7_22Obj:
    partStruct: Part6_7_22

class Sticker:
    id: int
    texStringPtr: int
    reserve0: int

class StickerObject(BaseCMXObject):
    sticker: Sticker
    texString: str

class Unk_IntField:
    unkIntField: Any

    def GetBytes(self) -> bytes: ...

class VTBF_COL:
    pass  # TODO

class VTBF_COLObject(BaseCMXObject):
    vtbfCol: VTBF_COL
    utf8Name: str
    utf16Name: str
