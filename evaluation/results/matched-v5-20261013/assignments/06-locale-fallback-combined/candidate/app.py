def _nonempty_string(value):
    return isinstance(value, str) and bool(value)


def process(payload):
    """Resolve each key using requested locale chains, then the exact default."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if not all(field in payload for field in ("catalog", "locales", "keys", "default")):
        raise ValueError("payload requires catalog, locales, keys and default")

    catalog = payload["catalog"]
    locales = payload["locales"]
    keys = payload["keys"]
    default = payload["default"]
    if not isinstance(catalog, dict):
        raise ValueError("catalog must be an object")
    if not isinstance(locales, list) or not all(map(_nonempty_string, locales)):
        raise ValueError("locales must be a list of nonempty strings")
    if not isinstance(keys, list) or not all(map(_nonempty_string, keys)):
        raise ValueError("keys must be a list of nonempty strings")
    if not _nonempty_string(default):
        raise ValueError("default must be a nonempty string")
    for locale, translations in catalog.items():
        if not _nonempty_string(locale) or not isinstance(translations, dict):
            raise ValueError("catalog must map nonempty locale strings to objects")
        for key, text in translations.items():
            if not _nonempty_string(key) or not isinstance(text, str):
                raise ValueError("translations must map nonempty keys to strings")

    candidates = []
    for locale in locales:
        while locale:
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
