# Prometheus — Banco de Questões

Aplicativo para organizar bancos de questões e montar provas em formato Word, com interface em português brasileiro.

Desenvolvido por **Pedro Trevisan** em Python, utilizando PySide6, SQLite e python-docx.

## Funcionalidades

- Organização de bancos de questões por disciplina e categorias.
- Cadastro de questões de múltipla escolha e dissertativas.
- Classificação por dificuldade, segmento e ano/série escolar.
- Registro da fonte da questão e do ano de origem.
- Editor de enunciados com formatação de texto, imagens e equações.
- Busca com filtros por categoria, texto, dificuldade, tipo, ano/série, fonte e ano de origem.
- Seleção de questões para composição de provas.
- Exportação de provas para Word, com opção de incluir gabarito.
- Geração de múltiplas versões, com embaralhamento de questões e alternativas.
- Interface com temas claro e escuro.

## Novidades da versão 1.1

- Campos opcionais de **fonte da questão** e **ano de origem**.
- Novos filtros de busca por fonte e ano de origem.
- Exibição dessas informações nos cartões das questões.
- Ajustes na interface para Windows, incluindo tipografia, espaçamento, ícones e aparência dos controles.
- Atualização automática da estrutura dos bancos existentes para incluir os novos campos.

O ano de origem identifica quando a questão foi publicada ou aplicada. Ele é independente do ano/série escolar ao qual a questão se destina.

## Como usar no Windows

1. Baixe o arquivo `Prometheus1.1.exe` disponibilizado na seção **Releases** deste repositório.
2. Salve o executável em uma pasta de sua preferência.
3. Abra o arquivo para iniciar o aplicativo.

A versão executável inclui as dependências necessárias. Não é preciso instalar Python nem executar um instalador.

### Fluxo de trabalho

1. **Escolha a disciplina:** crie um banco de questões ou abra um banco existente.
2. **Cadastre as questões:** informe os dados, selecione as categorias e preencha o enunciado, as alternativas ou a resposta esperada.
3. **Busque e selecione:** utilize os filtros e marque as questões que deseja incluir na prova.
4. **Gere a prova:** configure o gabarito, as versões e o embaralhamento; depois salve os arquivos Word.

## Bancos de dados e backups

As questões são armazenadas localmente em arquivos SQLite (`.db`).

No Windows, a configuração e o banco padrão ficam na pasta:

    %USERPROFILE%\.gerador_provas_app

Bancos criados ou abertos manualmente podem estar em outros locais, conforme a escolha do usuário.

**Copiar apenas o executável não transfere as questões nem as configurações para outro computador.** Para transferir um banco, copie também o arquivo `.db` e abra-o no aplicativo.

Mantenha cópias de segurança dos seus bancos, especialmente antes de atualizar o programa. A versão 1.1 adiciona os novos campos aos bancos existentes sem exigir um novo cadastro das questões.

## Executar a partir do código-fonte

Arquivo principal da versão atual: `Prometheus1.1.py`.

O ambiente utilizado para gerar o executável Windows usa:

- Python 3.14.5 — 64 bits
- PySide6 6.11.1
- PyInstaller 6.20.0
- python-docx 1.2.0

No PowerShell, dentro da pasta do projeto:

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements-windows.txt
    .\.venv\Scripts\python.exe Prometheus1.1.py

## Privacidade

Os bancos de questões e as configurações são armazenados localmente. O usuário é responsável por escolher onde guardar, compartilhar e fazer backup desses arquivos.
