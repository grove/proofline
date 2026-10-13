def _require_name(value, description):
    if not isinstance(value, str) or not value:
        raise ValueError(description + " must be a nonempty string")


def process(payload):
    """Resolve each key through requested locale chains, then the exact default."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    for field in ("catalog", "locales", "keys", "default"):
        if field not in payload:
            raise ValueError("missing field: " + field)

    catalog = payload["catalog"]
    if not isinstance(catalog, dict):
        raise ValueError("catalog must be an object")
    for locale, translations in catalog.items():
        _require_name(locale, "catalog locale")
        if not isinstance(translations, dict):
            raise ValueError("locale translations must be an object")
        for key, translation in translations.items():
            _require_name(key, "translation key")
            if not isinstance(translation, str):
                raise ValueError("translation must be a string")

    for field in ("locales", "keys"):
        if not isinstance(payload[field], list):
            raise ValueError(field + " must be a list")
        for name in payload[field]:
            _require_name(name, field + " entry")
    _require_name(payload["default"], "default")

    candidates = []
    for locale in payload["locales"]:
        candidates.append(locale)
        while "-" in locale:
            locale = locale.rsplit("-", 1)[0]
            candidates.append(locale)
    candidates.append(payload["default"])

    texts = []
    for key in payload["keys"]:
        for locale in candidates:
            translations = catalog.get(locale, {})
            if key in translations:
                texts.append(translations[key])
                break
        else:
            texts.append(None)
    return {"texts": texts}
