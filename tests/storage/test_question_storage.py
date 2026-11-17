import sqlite3
from prometheus.domain.questions import RichContent, QuestionDraft
from prometheus.storage.migrations import MIGRATIONS
from prometheus.storage.questions import insert_question


def test_insert_retains_html_and_existing_source_spelling():
    conn = sqlite3.connect(':memory:')
    conn.create_function('CASEFOLD', 1, lambda v: str(v or '').casefold())
    for migration in MIGRATIONS: migration(conn)
    html = '<p>formatted <b>text</b><img src="data:image/png;base64,abc"></p>'
    content = RichContent(html, True)
    draft = QuestionDraft(('Bio',), 'Fácil', 'Dissertativa', content, ('1ª Série',), 'Ensino Médio', (), '', content, 'ENEM', '2024')
    first = insert_question(conn, draft)
    from dataclasses import replace
    second = insert_question(conn, replace(draft, source='enem'))
    assert conn.execute('SELECT enunciado, gabarito, fonte_questao FROM questoes WHERE id=?', (second,)).fetchone() == (html, html, 'ENEM')
    assert second != first
    conn.close()


def test_update_preserves_identity_and_sets_timestamp():
    from dataclasses import replace
    from prometheus.storage.questions import get_question, update_question
    conn = sqlite3.connect(':memory:')
    conn.create_function('CASEFOLD', 1, lambda v: str(v or '').casefold())
    for migration in MIGRATIONS: migration(conn)
    content = RichContent('<p>before</p>', True)
    draft = QuestionDraft(('Bio',), 'Fácil', 'Dissertativa', content, ('1ª Série',), 'Ensino Médio', (), '', RichContent('', False), '', '')
    question_id = insert_question(conn, draft)
    assert get_question(conn, question_id)['last_modified']
    update_question(conn, question_id, replace(draft, statement=RichContent('<p>after</p>', True)))
    result = get_question(conn, question_id)
    assert result['id'] == question_id and result['enunciado'] == '<p>after</p>' and result['last_modified']
    conn.close()


def test_edit_preserves_existing_source_spelling_when_unchanged():
    from prometheus.storage.questions import update_question, get_question
    conn = sqlite3.connect(':memory:')
    conn.create_function('CASEFOLD', 1, lambda v: str(v or '').casefold())
    for migration in MIGRATIONS: migration(conn)
    content = RichContent('<p>text</p>', True)
    draft = QuestionDraft(('Bio',), 'Fácil', 'Dissertativa', content, ('1ª Série',), 'Ensino Médio', (), '', content, 'ENEM', '')
    insert_question(conn, draft)
    conn.execute("INSERT INTO questoes (id, fonte_questao) VALUES (20, 'enem')"); conn.commit()
    from dataclasses import replace
    update_question(conn, 20, replace(draft, source='enem'))
    assert get_question(conn, 20)['fonte_questao'] == 'enem'
    conn.close()
