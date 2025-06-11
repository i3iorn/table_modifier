import json
import os

class Localizer:
    def __init__(self, locale_dir: str, default_language='en'):
        self.translations = {}
        self.default_language = default_language
        self.current_language = default_language
        self._load_translations(locale_dir)

    def _load_translations(self, locale_dir):
        for filename in os.listdir(locale_dir):
            if filename.endswith('.json'):
                lang_code = filename[:-5]  # remove '.json'
                with open(os.path.join(locale_dir, filename), 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)

    def set_language(self, lang_code):
        if lang_code in self.translations:
            self.current_language = lang_code
        else:
            raise ValueError(f"Language '{lang_code}' not found in translations.")

    def translate(self, key, **kwargs):
        text = self.translations.get(self.current_language, {}).get(key)
        if text is None:
            text = self.translations.get(self.default_language, {}).get(key, key)
        try:
            return text.format(**kwargs)
        except KeyError as e:
            return f"{{Missing var: {e}}}"

    def __getitem__(self, key):
        return self.translate(key)

    def __call__(self, key, default=None) -> str:
        """Get translation for a key, returning default if not found."""
        return self.translate(key) if key in self.translations.get(self.current_language, {}) else default or key


String = Localizer(locale_dir='localization', default_language='en')