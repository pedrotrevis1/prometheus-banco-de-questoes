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
- Exportação de provas para Word, com questões em ordem escolhida, versões numeradas e gabarito opcional em arquivo separado.
- Geração de múltiplas versões, com embaralhamento de questões e alternativas e opção de preservar a ordem das alternativas de uma questão.
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

O código está disponível com todos os direitos reservados; nenhuma licença de
reutilização é concedida.

## Privacidade

Os bancos de questões e as configurações são armazenados localmente. O usuário é responsável por escolher onde guardar, compartilhar e fazer backup desses arquivos.
