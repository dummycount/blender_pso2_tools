import clr
from AquaModelLibrary.Data.PSO2.Aqua import CharacterMakingIndex, PSO2Text

class ReferenceGenerator:
    partColumns: str
    haircolumns: str
    acceColumns: str

    @staticmethod
    def ExtractCMX(
        pso2_binDir: str, aquaCMX: CharacterMakingIndex | None = None
    ) -> CharacterMakingIndex: ...
    @staticmethod
    def ReadCMXText(
        pso2_binDir: str,
        partsText: clr.Reference[PSO2Text],
        acceText: clr.Reference[PSO2Text],
        commonText: clr.Reference[PSO2Text],
        commonTextReboot: clr.Reference[PSO2Text],
    ) -> tuple[PSO2Text, PSO2Text, PSO2Text, PSO2Text]: ...
