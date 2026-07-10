# AutomaticExcelFill

Aplicativo desktop em Python (CustomTkinter) que monitora uma pasta, detecta arquivos CSV separados por tab e acrescenta os dados ao final da planilha Excel do mês atual.

## Funcionalidades iniciais

- **Etapa 1:** configurar a pasta principal a ser monitorada
- **Etapa 2:** ao detectar o arquivo esperado, colar os dados no Excel (aba do mês atual)
- **Fluxos:** cadastro com nome, arquivo esperado, destino do Excel e colunas do cabeçalho
- **Tema visual:** baseado no depósito [ArtemiS](https://github.com/Leftwardz/ArtemiS)

## Requisitos

- Python 3.9 ou 3.12
- Tkinter (no Linux: pacote `python3-tk`)

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

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
| Pasta do Excel | Onde criar/atualizar a planilha |
| Nome do Excel | Nome do arquivo `.xlsx` |
| Colunas | Cabeçalho gravado quando a aba do mês é nova ou vazia |

### Aba do mês

A aba usada segue o padrão `Julho 2026` (mês em português + ano). Se a aba não existir ou estiver vazia, o cabeçalho configurado no fluxo é criado antes de colar os dados.

### Wildcards no arquivo esperado

O campo **Arquivo esperado** aceita padrões com curingas:

| Padrão | Corresponde a |
|--------|----------------|
| `relatorio.csv` | Somente esse nome exato |
| `planilha_alc_*` | `planilha_alc_01.csv`, `planilha_alc_julho.txt`, etc. |
| `planilha_alc_*.csv` | Arquivos `.csv` com esse prefixo |
| `dados_????.tsv` | `dados_2026.tsv` (um `?` = um caractere) |

A comparação ignora maiúsculas/minúsculas. Se dois fluxos casarem com o mesmo arquivo, vale o primeiro fluxo ativo na lista.

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
