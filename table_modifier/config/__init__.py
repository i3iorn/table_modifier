from PyQt6.QtWidgets import QComboBox

controls = {
    "general_options":{
        "log_level": {
            "class": QComboBox,
            "label": "Log Level",
            "items": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        },
    },
    "process_options":
    {
        "kund_id_1": {
            "class": QComboBox,
            "label": "Kund ID 1",
            "items": ["ReferenceNumber", "category"],
        },
        "kund_id_2": {
            "class": QComboBox,
            "label": "Kund ID 2",
            "items": ["ReferenceNumber", "category"],
        },
    },
}
