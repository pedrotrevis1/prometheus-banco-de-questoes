# Prometheus — Banco de Questões

Aplicativo para organizar bancos de questões e montar provas em formato Word, com interface em português brasileiro.

Desenvolvido por **Pedro Trevisan** em Python, utilizando PySide6, SQLite e python-docx.

## Funcionalidades

- Organização de bancos de questões por disciplina e categorias.
- Cadastro, edição e duplicação de questões de múltipla escolha e dissertativas.
- Classificação por dificuldade, segmento e ano/série escolar.
- Registro da fonte da questão e do ano de origem.
- Formatação de texto e equações em enunciados, alternativas e respostas esperadas; imagens nos enunciados.
- Busca com filtros por categoria, texto, dificuldade, tipo, ano/série, fonte e ano de origem.
- Seleção de questões para composição de provas.
- Provas salvas com nome, turma, ordem das questões e opções de geração.
- Histórico de uso das questões e filtros por questões nunca usadas ou não usadas desde uma data.
- Exportação de provas para Word, com questões em ordem escolhida, versões numeradas e gabarito opcional em arquivo separado.
- Geração de múltiplas versões, com embaralhamento de questões e alternativas e opção de preservar a ordem das alternativas de uma questão.
- Interface com temas claro e escuro.

## Novidades da versão 2.0.0

- Edição e duplicação de questões, com preservação do conteúdo formatado.
- Categorias que podem ser renomeadas e movidas; filtrar uma categoria também inclui suas subcategorias.
- Busca pelo texto visível, sem diferenciar maiúsculas ou acentos, incluindo alternativas e respostas esperadas.
- Questões de múltipla escolha com duas a cinco alternativas.
- Resultados paginados, seleção preservada entre páginas e filtro por intervalo do ano de origem.
- Provas salvas por turma, histórico de uso e regeneração com preservação das ordens compatíveis.
- Melhorias na exportação Word, nas imagens, nos gabaritos e na identificação das versões.
- Atualização dos bancos com backup automático e relatório dos valores que precisam de revisão.

O código-fonte está preparado para a versão 2.0.0. A compilação e a verificação
dos executáveis Windows e macOS ainda estão pendentes; não há novos aplicativos
compilados nesta preparação. Consulte as [notas da versão](docs/releases/v2.0.0.md).

O ano de origem identifica quando a questão foi publicada ou aplicada. Ele é independente do ano/série escolar ao qual a questão se destina.

## Como usar no Windows

1. Baixe o executável Windows da versão publicada na seção **Releases** deste repositório. A preparação do código-fonte 2.0.0 não significa que o executável dessa versão já foi publicado.
2. Salve o executável em uma pasta de sua preferência.
3. Abra o arquivo para iniciar o aplicativo.

A versão executável inclui as dependências necessárias. Não é preciso instalar Python nem executar um instalador.

### Fluxo de trabalho

1. **Escolha a disciplina:** crie um banco de questões ou abra um banco existente.
2. **Cadastre as questões:** informe os dados, selecione as categorias e preencha o enunciado, as alternativas ou a resposta esperada.
3. **Busque e selecione:** utilize os filtros e marque as questões que deseja incluir na prova.
4. **Salve e gere a prova:** informe o nome e a turma, ajuste a ordem, o gabarito, as versões e o embaralhamento; depois salve os arquivos Word. Provas salvas podem ser retomadas posteriormente.

## Bancos de dados e backups

As questões são armazenadas localmente em arquivos SQLite (`.db`).

Antes de atualizar um banco antigo, confira o caminho exibido e mantenha uma
cópia de segurança. **Não abra um banco atualizado em versões antigas do
Prometheus:** elas não mostrarão as alterações corretamente. Leia o relatório de
atualização e revise os valores indicados, sem substituir seu banco pelo backup.

No Windows, a configuração e o banco padrão ficam na pasta:

    %USERPROFILE%\.gerador_provas_app

Bancos criados ou abertos manualmente podem estar em outros locais, conforme a escolha do usuário.

**Copiar apenas o executável não transfere as questões nem as configurações para outro computador.** Para transferir um banco, copie também o arquivo `.db` e abra-o no aplicativo.

Use **Fazer backup** no menu para salvar uma cópia do banco em um novo arquivo.
Antes de atualizar a estrutura de um banco, o aplicativo cria uma cópia
automática. São mantidos até três backups automáticos por banco; quando for
necessário excluir um backup antigo, o aplicativo exibirá o caminho e pedirá
confirmação. Se você recusar, a atualização será cancelada.

Se um banco não for encontrado, localize o arquivo ou remova a disciplina da
lista. Remover da lista não apaga o arquivo. Evite sincronizar um banco aberto
por serviços de nuvem e mantenha cópias de segurança separadas.

## Executar a partir do código-fonte

Use Python 3.14. As dependências de execução e desenvolvimento têm versões
fixadas em `requirements.txt` e `requirements-dev.txt`.

No PowerShell, dentro da pasta do projeto:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements-dev.txt
    python -m prometheus

No macOS, ative o ambiente com `source .venv/bin/activate` e use os mesmos
comandos de instalação e execução. Para executar os testes sem abrir uma janela:

    python -m pytest

Para gerar o executável no Windows, no ambiente preparado acima:

    .\build_windows.ps1

O executável é criado em `dist/Prometheus.exe`. O comando deve ser executado no
Windows; o resultado precisa ser testado nesse sistema, incluindo o QR Code Pix
em **Sobre**. O macOS também é uma plataforma oficialmente suportada.

Os builds usam o ícone oficial em `icon/prometheus-icon-apple Exports/`. Ele é
aplicado à janela em execução e ao artefato do sistema; no Windows, o build usa
`icon/Prometheus.ico`. Para gerar o macOS, instale as dependências de
`requirements-dev.txt` (o PyInstaller usa Pillow para converter o PNG para o
formato de ícone do bundle) e execute `./build_macos.sh` em um Mac. O bundle
usa o identificador `com.pedrotrevisan.prometheus`.

O código está disponível com todos os direitos reservados; nenhuma licença de
reutilização é concedida.

## Privacidade

Os bancos de questões e as configurações são armazenados localmente. O usuário é responsável por escolher onde guardar, compartilhar e fazer backup desses arquivos.
