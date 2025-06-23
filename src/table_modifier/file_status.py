from dataclasses import dataclass
from enum import IntEnum, auto, Enum, Flag


class FileStage(IntEnum):
    """
    The order of the stages reflect the lifecycle. As such they order
    may change in the future and so should not be relied upon other than to
    check if a status is greater than or less than another status.
    """
    NEW = auto()
    PROCESSING = auto()
    PROCESSED = auto()
    ARCHIVED = auto()

    def __lt__(self, other: "FileStage") -> bool:
        if isinstance(other, FileStage):
            return self.value < other.value
        else:
            return NotImplemented

    def __str__(self):
        return self.name.lower()


class FileFlag(Flag):
    """
    Represents the status of a file in the system.

    Flags can be combined using bitwise operations to represent multiple states.
    """
    UNKNOWN = auto()
    VALID = auto()
    EXPORTED = auto()
    PENDING = auto()
    ERROR = auto()
    DELETED = auto()

    def __str__(self) -> str:
        if self == FileFlag.UNKNOWN:
            return "unknown"
        return "|".join(flag.name.lower() for flag in FileFlag if flag in self and flag != FileFlag.UNKNOWN)

@dataclass
class FileStatus:
    """
    Represents the status of a file with its stage and flags.

    Attributes:
        stage (FileStage): The current stage of the file.
        flags (FileFlag): The flags representing the status of the file.
    """
    stage: FileStage = FileStage.NEW
    flags: FileFlag = FileFlag.UNKNOWN

    def __repr__(self):
        return f"FileStatus(stage={self.stage!r}, flags={self.flags!r})"
