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


def usage_count_label(count):
    return f"Usos: {count}" if count is not None else "Usos: não disponível"


def usage_entries(usages):
    """Format each ordered usage separately for a scrollable presentation."""
    return [format_usage_history([usage]) for usage in usages]
