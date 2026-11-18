from pathlib import Path
import pytest
from docx import Document
from prometheus.export.files import output_paths, publish_documents, PublicationError


def test_portuguese_filenames_and_separate_keys(tmp_path):
    assert output_paths(tmp_path/'Prova.docx', 2, 'separate') == [
        (tmp_path/'Prova_Versao_1.docx', tmp_path/'Prova_Versao_1_Gabarito.docx'),
        (tmp_path/'Prova_Versao_2.docx', tmp_path/'Prova_Versao_2_Gabarito.docx')]
    assert output_paths(tmp_path/'Prova', 1, 'end') == [(tmp_path/'Prova.docx', None)]
    with pytest.raises(ValueError): output_paths(tmp_path/'bad.pdf', 1, 'end')


def test_existing_file_never_overwritten_without_confirmation(tmp_path):
    path = tmp_path/'exam.docx'; path.write_bytes(b'keep')
    doc = Document(); doc.add_paragraph('new')
    with pytest.raises(PublicationError): publish_documents([(path, doc)])
    assert path.read_bytes() == b'keep'
    publish_documents([(path, doc)], confirmed={path})
    assert Document(path).paragraphs[0].text == 'new'


def test_reports_partial_publication_and_preserves_unwritten_existing(tmp_path, monkeypatch):
    import prometheus.export.files as files
    first, second = tmp_path/'one.docx', tmp_path/'two.docx'
    second.write_bytes(b'previous')
    doc = Document(); doc.add_paragraph('new')
    monkeypatch.setattr(files.os, 'replace', lambda *args: (_ for _ in ()).throw(OSError('failure')))
    with pytest.raises(PublicationError) as error:
        publish_documents([(first, doc), (second, doc)], confirmed={second})
    assert error.value.published == (first,)
    assert first.exists() and second.read_bytes() == b'previous'
    assert sorted(p.name for p in tmp_path.iterdir()) == ['one.docx', 'two.docx']


def test_suggested_exam_filename_is_safe_and_preserves_names():
    from prometheus.export.files import suggested_exam_filename
    assert suggested_exam_filename('Prova de Biologia') == 'Prova de Biologia.docx'
    assert suggested_exam_filename('  3ª Série: Biologia / A  ') == '3ª Série_ Biologia _ A.docx'
    assert suggested_exam_filename('Prova.docx') == 'Prova.docx'
    assert suggested_exam_filename('CON') == '_CON.docx'
    assert suggested_exam_filename('...') == 'Prova.docx'
