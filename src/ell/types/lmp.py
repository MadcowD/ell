import enum


class LMPType(str, enum.Enum):
    LM = "LM"
    TOOL = "TOOL"
    LABELER = "LABELER"
    FUNCTION = "FUNCTION"
    OTHER = "OTHER"