import logging
from threading import RLock
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.table_modifier.classifier.detectors.base import Detector


class DetectorRegistry:
    _registry: Dict[str, "Detector"] = {}
    _lock: RLock = RLock()
    _logger = logging.getLogger(__name__)

    @classmethod
    def register(cls, detector: "Detector") -> None:
        with cls._lock:
            cls._logger.debug(f"Registering detector: {detector.type_name}")
            cls._registry[detector.type_name()] = detector

    @classmethod
    def get_detectors(cls) -> List["Detector"]:
        with cls._lock:
            return list(cls._registry.values())

