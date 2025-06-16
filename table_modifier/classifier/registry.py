from threading import RLock
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from table_modifier.classifier.detector import Detector


class DetectorRegistry:
    _registry: Dict[str, "Detector"] = {}
    _lock: RLock = RLock()

    @classmethod
    def register(cls, detector: "Detector") -> None:
        with cls._lock:
            cls._registry[detector.type_name] = detector

    @classmethod
    def get_detectors(cls) -> List["Detector"]:
        with cls._lock:
            return list(cls._registry.values())

