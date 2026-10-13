# Clipping Digital — UFSB / ACS

Pipeline automatizado, 100% gratuito e de código aberto, para coletar,
registrar, analisar sentimento e apresentar visualmente as notícias sobre a
UFSB.

## Ferramentas escolhidas (e por quê)

| Etapa | Ferramenta | Por quê |
|---|---|---|
| Orquestração/agendamento | **GitHub Actions** | Gratuito (2.000 min/mês em repositório privado, ilimitado em público), já usado no projeto, não exige servidor próprio. |
| Coleta contínua | **Google News RSS** (`feedparser`) | Sem chave, sem custo, cobre bem o "daqui pra frente". |
| Coleta complementar | **Scraper genérico configurável** (`requests` + `BeautifulSoup4`) | Pega veículos regionais que o Google News não indexa bem — você define os seletores CSS por site em `config.yaml`. |
| Backfill histórico | **GDELT DOC 2.0 API** | Única fonte gratuita com alguma profundidade histórica pesquisável por palavra-chave. |
| Impressão em PDF | **Playwright (Chromium headless)** | Renderiza a página como um navegador de verdade — mais fiel que `wkhtmltopdf` em sites modernos. |
| Armazenamento dos PDFs | **Google Drive API** (conta de serviço) | Já é o ambiente da instituição; não introduz outra ferramenta. |
| Registro estruturado | **Google Sheets** (`gspread`) | Qualquer pessoa da equipe abre/filtra sem saber SQL. |
| Análise de sentimento | **pysentimiento** (modelo `BERTabaporu`, PT-BR) | Único classificador aberto e gratuito que já devolve exatamente positivo/neutro/negativo em português, sem precisar de API paga. |
| Relatório visual | **Chart.js** num HTML autocontido | Abre em qualquer navegador, sem servidor, sem build. |

Todas as ferramentas são gratuitas e de código aberto — isso foi o critério
de seleção, independente de qual empresa/modelo de IA está por trás.

## ⚠️ Limitação importante: cobertura "desde 2013"

Isto é um resultado de pesquisa, não uma suposição: **não existe hoje uma
fonte gratuita com indexação textual completa da imprensa brasileira
(especialmente regional) pesquisável desde 2013.**

- O **Google News RSS** não é um arquivo histórico pesquisável — na prática
  devolve o que foi publicado recentemente, e cada consulta tem teto de
  ~100 itens.
- O **GDELT** (a fonte gratuita mais profunda que existe) tem sua base
  textual pesquisável (DOC 2.0 / GKG) começando efetivamente em **2015**, e
  mesmo depois disso prioriza veículos de grande alcance — cobertura de
  jornais regionais de Porto Seguro/Itabuna/Ilhéus/Teixeira de Freitas
  tende a ser esparsa.
- Não existe uma "Google News API" oficial gratuita com filtro de data
  confiável para períodos além de ~30 dias.

**Estratégia realista implementada:**
1. 2013–2015: só é recuperável de forma confiável buscando diretamente no
   arquivo/busca interna de cada veículo regional (quando existir) e no
   **Wayback Machine** (Internet Archive) para páginas já arquivadas — ambos
   são "melhor esforço", não garantia de cobertura completa.
2. 2015 em diante: GDELT como complemento + scrapers dedicados por veículo.
3. Daqui para frente: Google News RSS + scrapers, rodando 3x/dia — isso
   sim é confiável e completo.

## Plano B — backfill 2013–2015

O ano de 2013 não é arbitrário: é o ano de criação da UFSB (Lei nº
12.818/2013). Faz sentido a ACS querer cobertura "desde o início". Como
nenhuma fonte gratuita garante isso sozinha, a estratégia combina quatro
frentes, da mais para a menos confiável:

1. **Hemeroteca Digital Brasileira** (Biblioteca Nacional,
   `bndigital.bn.gov.br/hemeroteca-digital`) — acervo público, gratuito e
   com OCR de milhões de páginas de periódicos brasileiros digitalizados.
   É o recurso mais promissor para **A Tarde**, por ser um jornal impresso
   centenário (fundado em 1912) — vale checar diretamente no catálogo da
   Hemeroteca se a edição impressa de A Tarde está indexada lá para o
   período 2013–2015 (não confirmei isso com certeza; é uma verificação de
   5 minutos no site deles, não uma chamada de API). Não cobre portais
   nativamente digitais como Bahia Notícias ou Correio Online, só o que
   foi publicado em papel.
2. **Wayback Machine (Internet Archive)** — gratuito, sem chave, via CDX
   API. Não faz busca textual por palavra-chave; serve para recuperar uma
   URL específica que você já suspeita ter existido (ex. se o GDELT ou uma
   citação em outro lugar apontar para um link antigo do Correio ou da A
   Tarde que hoje dá 404, o Wayback pode ter uma cópia arquivada).
3. **Arquivo interno da própria ACS/UFSB** — antes de gastar esforço
   técnico, vale confirmar internamente: a Assessoria já manteve algum
   controle manual de clipping (recortes em PDF, pasta de e-mails, um
   Excel antigo) desde a fundação da universidade? Instituições costumam
   ter esse hábito mesmo sem automação, e seria a fonte mais completa e
   confiável de todas para esse período — nenhuma ferramenta técnica
   substitui checar isso primeiro.
4. **Pedido formal aos veículos ou via LAI** — para o que sobrar de lacuna
   depois das três frentes acima, jornais costumam ter seu próprio arquivo
   interno e podem ser solicitados diretamente; sendo os veículos em sua
   maioria privados, a Lei de Acesso à Informação (LAI) não os obriga
   diretamente, mas nada impede o pedido informal, e para órgãos públicos
   citados nas matérias (prefeituras, MEC etc.) a LAI pode ajudar a
   reconstituir o contexto de uma cobertura mesmo sem o link original.

Nenhuma dessas quatro frentes está implementada como código neste pacote
além do que já existe em `collector_gdelt.py` — são passos de pesquisa e
decisão que fazem mais sentido feitos por vocês antes de eu automatizar
algo que pode não ter volume que justifique o esforço de engenharia.

## Veículos regionais — como fechar Correio e A Tarde

Confirmei por pesquisa que **Correio** (`correio24horas.com.br`) e **A
Tarde** (`atarde.com.br`) são reais, ativos, e cobrem a UFSB — encontrei
artigos reais de ambos. O que não consegui confirmar, com as ferramentas
de pesquisa disponíveis aqui (que extraem texto legível da página, não o
HTML bruto com classes CSS), foi se existe uma página de busca ou de tag
por assunto como a que encontrei na Bahia Notícias (`/tags/ufsb`).

Inventar um seletor CSS sem ver o HTML real seria adivinhação — o scraper
simplesmente não funcionaria, e pior, falharia silenciosamente ou traria
lixo. Isso é rápido de resolver, mas precisa de alguém abrindo o site no
navegador:

1. Abra `correio24horas.com.br` (ou `atarde.com.br`) e procure por uma
   caixa de busca ou um link "Assunto"/"Tags"/"Editorias".
2. Pesquise "UFSB" e veja a URL que aparece. Se for algo como
   `/busca?q=ufsb` ou `/tag/ufsb`, me envie essa URL.
3. Clique com o botão direito num resultado → "Inspecionar" → me envie
   (ou cole aqui) o HTML de um card de resultado — só preciso da
   estrutura, não de conteúdo sensível.

Com isso, escrevo `collector_correio.py` e `collector_atarde.py` do mesmo
jeito que fiz para a Bahia Notícias: baseado em padrão real, testado,
sem seletor inventado.

## Estrutura do projeto

```
press-clipping/
├── config.yaml                      # palavras-chave, veículos, IDs do Sheets/Drive
├── requirements.txt
├── .github/workflows/clipping.yml   # agendamento (GitHub Actions)
├── src/
│   ├── dedup.py                     # deduplicação (URL + título normalizados)
│   ├── collector_google_news.py     # coleta via Google News RSS
│   ├── collector_bahianoticias.py   # coleta via página de tag real da Bahia Notícias
│   ├── collector_site_scraper.py    # coleta genérica via busca interna (configurável)
│   ├── collector_gdelt.py           # backfill via GDELT DOC 2.0
│   ├── sentiment.py                 # classificação positivo/neutro/negativo (pysentimiento)
│   ├── pdf_snapshot.py              # impressão da página em PDF (Playwright)
│   ├── drive_upload.py              # upload dos PDFs ao Google Drive
│   ├── sheets_writer.py             # registro estruturado no Google Sheets
│   ├── report.py                    # geração do dashboard HTML
│   └── pipeline.py                  # orquestra tudo (chamado pelo GitHub Actions)
└── tests/                           # 40 testes unitários offline (ver abaixo)
```

## O que já foi testado neste ambiente — e o que não pôde ser

O ambiente onde este projeto foi montado tem acesso de rede restrito a
repositórios de pacotes (PyPI, npm, GitHub) — **não alcança
`news.google.com`, `api.gdeltproject.org`, `googleapis.com` nem a Hugging
Face Hub**. Por isso:

✅ **Testado de verdade, com `pytest` (46 testes, todos passando):**
- Deduplicação (URL com parâmetros de rastreamento, redirecionamento do
  Google News, mesma notícia em veículos diferentes não é duplicata).
- Parser do feed RSS do Google News (com fixture offline).
- Parser da página de tag real da Bahia Notícias (fixture modelado na
  estrutura de fato observada em `/tags/ufsb`: link duplicado
  imagem+título, formato de data "DD/MM/AAAA - HHhMM", link de menu
  corretamente ignorado).
- Parser do scraper genérico de veículo (item malformado não derruba o lote).
- Parser da resposta da API do GDELT.
- Classificador de sentimento (com um analisador falso simulando a
  interface real do `pysentimiento` — a qualidade do modelo real só pode
  ser avaliada com acesso à internet, fora deste sandbox).
- Geração de nome de arquivo do PDF (slugify, truncamento, data ausente).
- Montagem do payload de upload ao Drive e validação do JSON da conta de serviço.
- Montagem das linhas do Sheets e extração de links já conhecidos.
- Agregação e geração do dashboard HTML (rodado de ponta a ponta com dados
  fictícios — ver `demo_report.html` anexo).
- **Integração entre todos os módulos** via `python src/pipeline.py --modo smoke-test`.

Dois bugs reais foram encontrados e corrigidos durante esse processo (nos
testes, não no código de produção) — ver histórico de commits sugerido
antes do primeiro push.

❌ **Não pôde ser testado neste ambiente (requer rede/credenciais que só
existem no seu ambiente):**
- Chamada real ao Google News RSS, GDELT, Wayback Machine.
- Autenticação e upload reais no Google Drive/Sheets.
- Download dos pesos do modelo `pysentimiento` (primeira execução baixa
  ~500MB da Hugging Face Hub).
- Geração de PDF com Chromium real (Playwright).

**Antes do primeiro uso em produção**, rode manualmente (`workflow_dispatch`
no GitHub Actions, modo `smoke-test` depois `monitoramento`) e confira as
primeiras linhas geradas no Sheets antes de deixar o agendamento automático rodando.

## Passo a passo de configuração

1. **Google Cloud**: crie um projeto, ative "Google Sheets API" e "Google
   Drive API", crie uma conta de serviço, gere a chave JSON.
2. **Compartilhamento**: compartilhe a planilha e a pasta do Drive de
   destino com o e-mail da conta de serviço (papel Editor).
3. **Secrets do GitHub**: em Settings → Secrets and variables → Actions,
   crie `GOOGLE_SERVICE_ACCOUNT_JSON` com o conteúdo integral do JSON.
4. **config.yaml**: preencha `spreadsheet_id`, `drive_pdf_folder_id`,
   ajuste `keywords` e, se for usar, os `outlets` com scraper dedicado.
5. **Primeira linha da planilha**: crie manualmente o cabeçalho exato
   definido em `src/sheets_writer.py::HEADER` (ordem importa).
6. **Rodar `workflow_dispatch` → `smoke-test`** para validar antes de ligar
   o agendamento automático.

## Dúvidas em aberto que precisam da sua decisão

- **Correio e A Tarde**: ver seção "Veículos regionais — como fechar
  Correio e A Tarde" acima — preciso da URL de busca/tag real de cada um
  (2 minutos no navegador da sua parte) para não inventar seletor.
- **Backfill 2013–2015**: ver "Plano B" acima — vale checar primeiro se a
  ACS já tem algum arquivo interno de clipping desde a fundação da UFSB,
  antes de investir esforço técnico em GDELT/Wayback/Hemeroteca para esse
  período específico.
- **Frequência**: confirmada em 3x/dia (`0 8,14,20 * * *`, horário de
  Brasília) — já configurada no workflow.
