import unicodedata

def normalize_name(name):
    """Removes accents and converts to lowercase for robust matching."""
    if not isinstance(name, str):
        return ""
    return "".join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()
