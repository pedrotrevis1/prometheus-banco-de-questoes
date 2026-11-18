"""Presentation-neutral formatting for recorded exam usage."""
from datetime import date


def format_usage_history(usages):
    result = []
    for name, class_name, used_at in usages:
        try:
            display_date = date.fromisoformat(used_at[:10]).strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            display_date = str(used_at)
        result.append(f"{name} — {class_name or 'Sem turma'} — {display_date}")
    return '; '.join(result)
