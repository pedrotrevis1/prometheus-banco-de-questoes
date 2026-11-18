from prometheus.domain.usage_history import usage_count_label, usage_entries


def test_usage_presentation():
    assert [usage_count_label(n) for n in (0, 1, 2, 1000, None)] == [
        'Usos: 0', 'Usos: 1', 'Usos: 2', 'Usos: 1000', 'Usos: não disponível']
    assert usage_entries([('Prova <A>', '', '2026-11-18T12:00'), ('Outra', 'B', 'bad')]) == [
        'Prova <A> — Sem turma — 18/11/2026', 'Outra — B — bad']
