import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from src.table_modifier.config import ROOT_PATH


class Localizer:
    """
    JSON-backed localization helper.

    - Loads all JSON files in a locales directory keyed by their stem (e.g., 'en.json' -> 'en').
    - Provides dictionary-style and call-style access to translations.
    - Falls back to the default language, then to the key itself if missing.
    """

    def __init__(self, locale_dir: str, default_language: str = "en") -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self.translations: Dict[str, Dict[str, str]] = {}
        self.default_language: str = default_language
        self.current_language: str = default_language
        self._load_translations(locale_dir)

    def _load_translations(self, locale_dir: str) -> None:
        locale_path = Path(locale_dir)
        locale_path.mkdir(parents=True, exist_ok=True)
        for json_file in locale_path.glob("*.json"):
            lang_code = json_file.stem
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    # Only keep key->string entries
                    self.translations[lang_code] = {
                        k: str(v) for k, v in data.items()
                    }
                else:
                    self._logger.warning(
                        "Skipping %s: expected object at top-level, got %s",
                        json_file.name,
                        type(data).__name__,
                    )
            except json.JSONDecodeError as e:
                self._logger.warning("Skipping %s: invalid JSON (%s)", json_file.name, e)

    def set_language(self, lang_code: str) -> None:
        if lang_code in self.translations:
            self.current_language = lang_code
        else:
            raise ValueError(f"Language '{lang_code}' not found in translations.")

    def translate(self, key: str, **kwargs: Any) -> str:
        """
        Translate a key using current language, with fallback to default.

        Keyword args are used for str.format interpolation; missing keys are reported.
        """
        text: Optional[str] = self.translations.get(self.current_language, {}).get(key)
        if text is None:
            text = self.translations.get(self.default_language, {}).get(key, key)
        try:
            return text.format(**kwargs)
        except KeyError as e:
            # Return a helpful marker if a variable is missing
            return f"{text} (Missing var: {e.args[0]})"
        except Exception:
            # If formatting fails for any reason, return the raw text
            return text

    def get(self, key: str, default: Optional[str] = None) -> str:
        if not default:
            default = key
        return self.translations.get(self.current_language, {}).get(key, default)

    def __getitem__(self, key: str) -> str:
        return self.translate(key)

    def __call__(self, key: str, default: Optional[str] = None) -> str:
        """Get translation for a key, returning default if not found."""
        lang_map = self.translations.get(self.current_language, {})
        return lang_map.get(key) or self.translations.get(self.default_language, {}).get(key) or default or key


String = Localizer(
    locale_dir=ROOT_PATH.joinpath("locales").as_posix(),
    default_language="en",
)
