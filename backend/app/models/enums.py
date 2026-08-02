import enum


class BorrowerType(str, enum.Enum):
    INTERNAL = "Internal"
    EXTERNAL = "External"