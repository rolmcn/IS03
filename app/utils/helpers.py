import re
from pathlib import Path

def read_text_from_file(filename: str) -> str:
    file_path = Path(__file__).resolve().parent.parent.parent / "texts" / filename # leidžia pasiekti texts/ aplanką iš utils/, nes __file__ yra app/utils/helpers.py
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path.read_text(encoding="utf-8")

def convert_to_paragraphs(text: str, contact: dict) -> str:
    text = replace_placeholders(text, contact)

    blocks = text.strip().split("\n\n")
    html_parts = []
    for block in blocks:
        lines = block.strip().split("\n")
        content = "<br>".join(line.strip() for line in lines)
        if re.match(r"^\d+\.\s", lines[0].strip()):
            html_parts.append(f'<p class="section-title">{content}</p>')
        else:
            html_parts.append(f"<p>{content}</p>")
    return ''.join(html_parts)

def replace_placeholders(text: str, contact: dict) -> str:
    replacements = {
        "[piktograma]": (
            '<a href="/accessibility-settings" '
            'class="icon-1" '
            'aria-label="Prieinamumo nustatymai">'
            '<img src="/static/img/settings_accessibility_40dp_1A69B1_FILL0_wght500_GRAD0_opsz40.svg" '
            'title="Prieinamumo nustatymai" />'
            '</a>'
        ),
        "[email]": (
            f'<a href="mailto:{contact["email"]}" class="contact-link">{contact["email"]}</a>'
        ),
        "[company_name]": contact["company_name"],
        "[company_code]": contact["company_code"]
    }

    for placeholder, html in replacements.items():
        text = text.replace(placeholder, html)

    return text

