import html
import re


def format_equation_html(text, equation_type="Matemática"):
    text = text.replace("<->", "↔").replace("<=>", "⇔").replace("->", "→")
    escaped = html.escape(text).replace("\n", "<br>")
    escaped = re.sub(r"\^(\{([^}]+)\}|(\S))", lambda m: f"<sup>{m.group(2) or m.group(3)}</sup>", escaped)
    escaped = re.sub(r"_(\{([^}]+)\}|(\S))", lambda m: f"<sub>{m.group(2) or m.group(3)}</sub>", escaped)
    if equation_type == "Química":
        escaped = re.sub(r"([A-Za-z\)])([0-9]+)", r"\1<sub>\2</sub>", escaped)
    return f'<span style="font-family: \"Times New Roman\", serif; font-size: 13pt;">{escaped}</span>'


def html_fragment(value):
    content = str(value or "")
    body_match = re.search(r"<body\b[^>]*>(.*?)</body\s*>", content, re.IGNORECASE | re.DOTALL)
    if body_match:
        content = body_match.group(1)
    else:
        content = re.sub(r"</?(?:html|head)\b[^>]*>", "", content, flags=re.IGNORECASE)

    def clean_style(style_match):
        quote, declarations = style_match.groups()
        kept = []
        for declaration in declarations.split(";"):
            property_name = declaration.partition(":")[0].strip().lower()
            if property_name not in {"background", "background-color", "color", "font-family"}:
                kept.append(declaration)
        cleaned = ";".join(kept).strip("; ")
        return f' style={quote}{cleaned}{quote}' if cleaned else ""

    content = re.sub(r'\s+style=("|\')(.*?)\1', clean_style, content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'(?i)\s+bgcolor\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)', '', content)
    content = re.sub(r'(?i)\s+face\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)', '', content)
    if not re.search(r"<(?:!doctype|/?(?:html|head|body|p|div|span|br|img|b|strong|i|em|u|sup|sub|table|thead|tbody|tfoot|tr|td|th|ul|ol|li|blockquote|hr|a|font|pre|code|h[1-6]))\b", content, re.IGNORECASE):
        content = html.escape(content).replace("\n", "<br>")
    return content
