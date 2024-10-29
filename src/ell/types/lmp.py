import enum


class LMPType(str, enum.Enum):
    LM = "LM"
    TOOL = "TOOL"
    MULTIMODAL = "MULTIMODAL"
    OTHER = "OTHER"
