def _nonempty_string(value):
    return isinstance(value, str) and bool(value)


def process(payload):
    """Resolve each key through requested locale chains, then exact default."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if not all(name in payload for name in ("catalog", "locales", "keys", "default")):
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

    # Validate every translation table, including those lookup will not reach.
    for locale, translations in catalog.items():
        if not _nonempty_string(locale) or not isinstance(translations, dict):
            raise ValueError("catalog must map nonempty locale strings to objects")
        for key, text in translations.items():
            if not _nonempty_string(key) or not isinstance(text, str):
                raise ValueError("translations must map nonempty keys to strings")

    tables = []
    for locale in locales:
        while locale:
            if locale in catalog:
                tables.append(catalog[locale])
            if "-" not in locale:
                break
            locale = locale.rsplit("-", 1)[0]
    if default in catalog:
        tables.append(catalog[default])

    texts = []
    for key in keys:
        for translations in tables:
            if key in translations:
                texts.append(translations[key])
                break
        else:
            texts.append(None)
    return {"texts": texts}
