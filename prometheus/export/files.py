"""Plan and publish exam files without unconfirmed replacement."""
import os
from pathlib import Path
import tempfile


class PublicationError(Exception):
    def __init__(self, message, published=()):
        self.published = tuple(published)
        super().__init__(message)


def output_paths(path, count, answer_placement):
    path = Path(path)
    if path.suffix and path.suffix.lower() != '.docx':
        raise ValueError('A geração de provas suporta somente arquivos .docx.')
    if count < 1 or answer_placement not in ('end', 'separate', 'none'):
        raise ValueError('Opções de geração inválidas.')
    base = path.with_suffix('') if path.suffix else path
    result = []
    for number in range(1, count + 1):
        name = str(base) + (f'_Versao_{number}' if count > 1 else '')
        exam = path if count == 1 and path.suffix else Path(name + '.docx')
        result.append((exam, Path(name + '_Gabarito.docx') if answer_placement == 'separate' else None))
    return result


def publish_documents(documents, *, confirmed=()):
    confirmed = {Path(path).resolve() for path in confirmed}
    staged, published, destinations = [], [], set()
    failure = None
    try:
        for path, document in documents:
            path = Path(path)
            key = path.resolve()
            if key in destinations:
                raise ValueError('O mesmo arquivo foi solicitado mais de uma vez.')
            destinations.add(key)
            if path.exists() and key not in confirmed:
                raise FileExistsError(f'Arquivo existente não confirmado: {path}')
            fd, temp = tempfile.mkstemp(prefix='.exam_', suffix='.docx', dir=path.parent)
            os.close(fd)
            staged.append((Path(temp), path))
            document.save(temp)
        for temp, path in staged:
            if path.resolve() in confirmed:
                os.replace(temp, path)
                published.append(path)
            else:
                os.link(temp, path)
                published.append(path)
                temp.unlink()
    except Exception as exc:
        failure = exc
    cleanup_errors = []
    for temp, _ in staged:
        try:
            if temp.exists():
                temp.unlink()
        except OSError as exc:
            cleanup_errors.append(f'{temp}: {exc}')
    if failure or cleanup_errors:
        message = str(failure) if failure else 'Falha ao limpar arquivos temporários.'
        if cleanup_errors:
            message += ' Arquivos temporários não removidos: ' + '; '.join(cleanup_errors)
        raise PublicationError(message, published) from failure
    return tuple(published)
