"""Strict, read-only interpretation of source years."""


class YearRangeError(ValueError):
    def __init__(self, code, field):
        self.code = code
        self.field = field
        super().__init__(code)


def parse_stored_year(value):
    if value is None:
        return None
    text = str(value).strip()
    if not text or any(ch < '0' or ch > '9' for ch in text):
        return None
    significant = text.lstrip('0')
    if not significant or len(significant) > 4:
        return None
    return int(significant)


def validate_year_range(lower, upper):
    values = []
    for text, field in ((lower, 'from'), (upper, 'to')):
        if not text.strip():
            values.append(None)
            continue
        parsed = parse_stored_year(text)
        if parsed is None:
            raise YearRangeError('invalid', field)
        values.append(parsed)
    if values[0] is not None and values[1] is not None and values[0] > values[1]:
        raise YearRangeError('inverted', 'from')
    return tuple(values)
