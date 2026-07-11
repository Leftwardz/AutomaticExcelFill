# AutomaticExcelFill

Aplicativo desktop em Python (CustomTkinter) que monitora uma pasta, detecta arquivos CSV separados por tab e acrescenta os dados ao final da planilha Excel do mês atual.

## Funcionalidades iniciais

- **Etapa 1:** configurar a pasta principal a ser monitorada
- **Etapa 2:** ao detectar o arquivo esperado, colar os dados no Excel (aba do mês atual)
- **Fluxos:** cadastro com nome, arquivo esperado, destino do Excel e colunas do cabeçalho
- **Tema visual:** baseado no depósito [ArtemiS](https://github.com/Leftwardz/ArtemiS)

## Requisitos

- **Python 3.9+** (testado em 3.9 e 3.12)
- Tkinter (no Linux: pacote `python3-tk`)

## Instalação

### Windows (recomendado)

Dê dois cliques ou rode no terminal, **na pasta do projeto**:

```bat
scripts\install_deps.bat
```

Ou no PowerShell:

```powershell
.\scripts\install_deps.ps1
```

O script cria o `.venv`, atualiza `pip` e instala as dependências.

### Manual (qualquer sistema)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
```

> **Use sempre `python -m pip`**, não só `pip` — evita pegar o Python errado.

### Erro `encoding must be str, not None` no pip

Quase sempre é ambiente Python incorreto no Windows:

1. Confirme a versão: `python --version` → precisa ser **3.9+**
2. Não use Python 2.x (`python2`, `pip2`)
3. Rode o `scripts\install_deps.bat` (define UTF-8 e cria venv limpo)
4. Se ainda falhar, no CMD antes do install:
   ```bat
   chcp 65001
   set PYTHONUTF8=1
   set PYTHONIOENCODING=utf-8
   python -m pip install -U pip setuptools wheel
   python -m pip install -r requirements.txt
   ```
5. Evite pastas com acentos ou permissão restrita (ex.: `C:\Users\...\AutomaticExcelFill`)

## Executar

```bash
python main.py
```

### Teste rápido no Linux (sem monitor)

```bash
sudo apt-get install -y python3-tk xvfb
PYTHONPATH=. xvfb-run -a python3 scripts/smoke_test_gui.py
```

## Gerar executável (PyInstaller)

```bash
pyinstaller AutomaticExcelFill.spec
```

O executável será gerado em `dist/AutomaticExcelFill`.

## Configuração

As configurações ficam em `config.json` na mesma pasta do aplicativo (ou do executável).

### Fluxo

Cada fluxo define:

| Campo | Descrição |
|-------|-----------|
| Nome | Identificação do fluxo |
| Arquivo esperado | Nome exato ou com wildcards (`*`, `?`) na pasta monitorada |
| Pasta do Excel | Onde criar/atualizar a planilha (o app cria subpasta do ano, ex.: `2026/`) |
| Nome do Excel | Nome do arquivo `.xlsx` |
| Senha para modificar | Opcional — igual ao Excel: *Salvar como → Opções gerais → Senha para modificar* |
| Colunas | Cabeçalho gravado quando a aba do mês é nova ou vazia — cole a linha copiada do Excel |

**Senha para modificar:** o arquivo **abre sem senha de abertura**. No Excel o usuário pode escolher **Somente leitura**; para salvar no original precisa da senha. Sem a senha, só **Salvar uma cópia**. O aplicativo grava no arquivo original usando a senha configurada no fluxo.

**Colunas:** copie a linha de cabeçalho no Excel e clique em *Colar da área de transferência* no cadastro do fluxo (ou cole direto no campo de texto).

> A senha fica salva em texto no `config.json` compartilhado na pasta monitorada (uso em máquina/desktop).

### Aba do mês

O Excel de cada fluxo é criado em uma subpasta do **ano atual** dentro da pasta configurada. Exemplo: pasta `D:\Planilhas` → arquivo em `D:\Planilhas\2026\relatorio.xlsx`.

A aba usada segue só o **nome do mês em português** (minúsculas): `julho`, `junho`, etc. Se a aba não existir ou estiver vazia, o cabeçalho configurado no fluxo é criado antes de colar os dados.

### Cores alternadas por dia

As linhas coladas pelo aplicativo recebem cor de fundo que alterna a cada **dia do calendário**:

- No primeiro dia processado na aba, as linhas ficam **brancas**
- No dia seguinte, **roxo claro**
- No próximo dia, branco de novo — e assim por diante

Vários arquivos no **mesmo dia** mantêm a mesma cor. O controle fica em uma aba oculta `__AEF__` dentro do Excel (não altere essa aba manualmente).

### Formatação da planilha

- **Cabeçalho (linha 1):** fundo roxo escuro, texto branco em negrito
- **Dados:** sempre gravados como texto (não viram número/data no Excel)
- **Largura das colunas:** ajustada automaticamente para caber o conteúdo (sem cortar o texto visível)

### Wildcards no arquivo esperado

O campo **Arquivo esperado** aceita padrões com curingas:

| Padrão | Corresponde a |
|--------|----------------|
| `relatorio.csv` | Somente esse nome exato |
| `planilha_alc_*` | `planilha_alc_01.csv`, `planilha_alc_julho.txt`, etc. |
| `planilha_alc_*.csv` | Arquivos `.csv` com esse prefixo |
| `dados_????.tsv` | `dados_2026.tsv` (um `?` = um caractere) |

A comparação ignora maiúsculas/minúsculas. Se dois fluxos casarem com o mesmo arquivo, vale o primeiro fluxo ativo na lista.

### Dois computadores na mesma pasta

Para evitar que os dois processem o mesmo arquivo ou gravem no Excel ao mesmo tempo:

- O app cria locks em `{pasta monitorada}/.automatic_fill_locks/`
- Quem conseguir o lock do **arquivo CSV** primeiro processa; o outro ignora com mensagem no monitor
- O lock do **Excel** garante gravação sequencial na mesma planilha

Use a **mesma pasta monitorada** nos dois PCs. O `config.json` completo fica em `{pasta monitorada}/config.json`; ao lado do executável fica só um arquivo mínimo com o caminho da pasta (bootstrap).

### Confiabilidade em rede

- **Polling automático** em caminhos UNC (`\\servidor\pasta`) — mais estável que eventos do sistema em pasta compartilhada
- **Aguarda cópia terminar** — só processa quando o tamanho do arquivo estabiliza
- **Gravação atômica** do Excel (arquivo temporário + renomear)
- **Qualquer falha** (duplicata, senha, encoding, permissão) move o arquivo para `falhas/` quando configurado
- **Locks inteligentes** — detectam processo morto e mostram qual PC está processando
- **CSV com encoding alternativo** — tenta UTF-8, depois `cp1252` e `latin-1`

### Operação na interface

- **Log compartilhado** visível na aba Monitoramento (atualiza ao processar ou no botão)
- **Processar arquivo...** — reprocessamento manual de um CSV
- **Ativar/Desativar fluxo** — na lista de fluxos ou no cadastro
- Ao **salvar configurações**, o monitoramento reinicia automaticamente se estiver ativo

### Linhas duplicadas

Antes de colar, o app compara cada linha nova com as que já existem na aba (e com as outras linhas do mesmo arquivo). Se encontrar uma linha **idêntica**:

- O job **falha** e **nada é gravado** na planilha
- O arquivo vai para a subpasta **`falhas`** (configurável)
- Um registro é escrito no **log compartilhado** (`automatic_fill.log` na pasta monitorada, ou caminho customizado)

O log inclui data/hora, computador, fluxo, arquivo e motivo — visível nos dois PCs se estiver numa pasta de rede.

## Estrutura

```
app/
  models/       # schema e persistência (config.json)
  services/     # Excel, monitoramento de pasta
  ui/           # interface CustomTkinter
main.py
theme/presets.json
```

## Workflow de desenvolvimento

**Neste projeto, trabalhe sempre direto na branch `main`.**

- Não criar branches de feature (`cursor/...`) nem abrir pull requests.
- Fazer as alterações, commitar na `main` e dar `git push origin main`.
- Mensagens de commit claras e em português ou inglês, conforme o contexto da mudança.

Instrução para agentes/automações (Cursor Cloud e similares): aplicar mudanças, testar quando fizer sentido, commitar e enviar **somente para `main`** — sem PR intermediário.
