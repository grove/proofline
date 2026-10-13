def _nonempty_string(value):
    return isinstance(value, str) and bool(value)


def process(payload):
    """Resolve each key through requested locale parents, then exact default."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if not all(field in payload for field in ("catalog", "locales", "keys", "default")):
        raise ValueError("payload must contain catalog, locales, keys and default")

    catalog = payload["catalog"]
    locales = payload["locales"]
    keys = payload["keys"]
    default = payload["default"]
    if not isinstance(catalog, dict):
        raise ValueError("catalog must be an object")
    for locale, translations in catalog.items():
        if not _nonempty_string(locale) or not isinstance(translations, dict):
            raise ValueError("catalog locales must be nonempty strings mapped to objects")
        for key, translation in translations.items():
            if not _nonempty_string(key) or not isinstance(translation, str):
                raise ValueError("catalog keys must be nonempty strings mapped to strings")
    if not isinstance(locales, list) or not all(map(_nonempty_string, locales)):
        raise ValueError("locales must be a list of nonempty strings")
    if not isinstance(keys, list) or not all(map(_nonempty_string, keys)):
        raise ValueError("keys must be a list of nonempty strings")
    if not _nonempty_string(default):
        raise ValueError("default must be a nonempty string")

    # Build the ordered search path once; resolve each key independently.
    candidates = []
    for locale in locales:
        while True:
            candidates.append(locale)
            if "-" not in locale:
                break
            locale = locale.rsplit("-", 1)[0]
    candidates.append(default)

    texts = []
    for key in keys:
        for locale in candidates:
            translations = catalog.get(locale, {})
            if key in translations:
                texts.append(translations[key])
                break
        else:
            texts.append(None)
    return {"texts": texts}
