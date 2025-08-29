from .setup import ROOT_PATH

controls = {
    "general_options": [
        {
            "type": "combo",
            "name": "log_level",
            "label": "Log Level",
            "items": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "default": "INFO",
        },
    ],
    "processing": [
        {
            "type": "combo",
            "name": "processing.chunk_size",
            "label": "Chunk size",
            "items": ["500", "1000", "5000", "10000", "20000"],
            "default": "20000",
        },
        {
            "type": "combo",
            "name": "processing.csv_delimiter",
            "label": "CSV Delimiter",
            "items": [",", "\t", ";"],
            "default": ",",
        },
        {
            "type": "checkbox",
            "name": "processing.strict_per_slot",
            "label": "Strict per slot (fail when any mapping slot's source columns are missing)",
            "default": False,
        },
        {
            "type": "checkbox",
            "name": "processing.strict",
            "label": "Strict mode (fail on missing columns)",
            "default": False,
        },
    ],
}
