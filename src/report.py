"""
Geração do relatório visual do clipping — um HTML autocontido com:
  - total de notícias por veículo
  - distribuição de sentimento (positivo/neutro/negativo)
  - notícias por categoria
  - evolução mensal do volume de notícias
  - tabela com as notícias mais recentes

FERRAMENTA: Chart.js (open-source, MIT), carregado via CDN dentro do próprio
HTML — não precisa de servidor, Node, nem build step. O arquivo gerado pode
ser aberto direto no navegador, anexado a um e-mail, ou publicado como
página. Isso é deliberado: a equipe de comunicação não deve depender de
rodar um serviço Python para ver o relatório.

Este módulo só faz AGREGAÇÃO + TEMPLATE. Ele não sabe de onde os dados
vieram (Sheets, CSV local, teste) — recebe uma lista de dicts com as chaves
do cabeçalho definido em `sheets_writer.HEADER` e devolve uma string HTML.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

_SENTIMENT_ORDER = ["positivo", "neutro", "negativo"]
_SENTIMENT_COLORS = {"positivo": "#2e7d32", "neutro": "#9e9e9e", "negativo": "#c62828"}


def _aggregate(rows: list[dict]) -> dict:
    por_veiculo = Counter(r["veiculo"] for r in rows)
    por_sentimento = Counter(r["sentimento"] for r in rows)
    por_categoria = Counter(r["categoria"] for r in rows)

    por_mes = defaultdict(int)
    for r in rows:
        mes = (r.get("data_publicacao") or "")[:7]  # 'YYYY-MM'
        if mes:
            por_mes[mes] += 1
    meses_ordenados = sorted(por_mes.keys())

    recentes = sorted(rows, key=lambda r: r.get("data_publicacao", ""), reverse=True)[:15]

    return {
        "total": len(rows),
        "veiculos_labels": [v for v, _ in por_veiculo.most_common(12)],
        "veiculos_valores": [c for _, c in por_veiculo.most_common(12)],
        "sentimento_labels": [s for s in _SENTIMENT_ORDER if por_sentimento.get(s)],
        "sentimento_valores": [por_sentimento.get(s, 0) for s in _SENTIMENT_ORDER if por_sentimento.get(s)],
        "sentimento_cores": [_SENTIMENT_COLORS[s] for s in _SENTIMENT_ORDER if por_sentimento.get(s)],
        "categoria_labels": list(por_categoria.keys()),
        "categoria_valores": list(por_categoria.values()),
        "meses_labels": meses_ordenados,
        "meses_valores": [por_mes[m] for m in meses_ordenados],
        "recentes": recentes,
    }


def generate_html_report(rows: list[dict], titulo: str = "Clipping Digital — UFSB / ACS") -> str:
    agg = _aggregate(rows)
    data_json = json.dumps(agg, ensure_ascii=False)

    linhas_tabela = "\n".join(
        f'<tr><td>{r.get("data_publicacao","")}</td>'
        f'<td>{r.get("veiculo","")}</td>'
        f'<td><a href="{r.get("link","#")}" target="_blank" rel="noopener">{r.get("manchete","")}</a></td>'
        f'<td><span class="badge badge-{r.get("sentimento","neutro")}">{r.get("sentimento","")}</span></td>'
        f'<td>{r.get("categoria","")}</td></tr>'
        for r in agg["recentes"]
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{titulo}</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #f5f6f8; --card-bg: #ffffff; --text: #1a1a2e; --muted: #6b7280;
    --accent: #002878; --border: #e5e7eb;
    box-sizing: border-box;
    padding-top: env(safe-area-inset-top, 0px);
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #0f1117; --card-bg: #181b24; --text: #e8e8ec; --muted: #9aa0ac; --border: #2a2e3a;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #0f1117; --card-bg: #181b24; --text: #e8e8ec; --muted: #9aa0ac; --border: #2a2e3a;
  }}
  * {{ box-sizing: border-box; }}
  html {{ scroll-padding-top: env(safe-area-inset-top, 0px); }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    padding: 24px 16px 48px;
  }}
  h1 {{ font-size: 1.4rem; margin: 0 0 4px; color: var(--accent); }}
  .subtitulo {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 24px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }}
  .card {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px; min-width: 0;
  }}
  .card h2 {{ font-size: 0.95rem; margin: 0 0 12px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; }}
  .kpi {{ font-size: 2.2rem; font-weight: 700; color: var(--accent); }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .badge {{ padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; color: white; white-space: nowrap; }}
  .badge-positivo {{ background: #2e7d32; }}
  .badge-neutro {{ background: #9e9e9e; }}
  .badge-negativo {{ background: #c62828; }}
  .tabela-wrap {{ overflow-x: auto; }}
  canvas {{ max-width: 100%; }}
</style>
</head>
<body>
  <h1>{titulo}</h1>
  <div class="subtitulo">Gerado a partir de {agg['total']} notícias registradas</div>

  <div class="grid" style="margin-bottom:16px;">
    <div class="card"><h2>Total de notícias</h2><div class="kpi">{agg['total']}</div></div>
    <div class="card"><h2>Veículos distintos</h2><div class="kpi">{len(agg['veiculos_labels'])}</div></div>
    <div class="card"><h2>Categorias em uso</h2><div class="kpi">{len(agg['categoria_labels'])}</div></div>
  </div>

  <div class="grid" style="margin-bottom:16px;">
    <div class="card"><h2>Notícias por veículo</h2><canvas id="chartVeiculos"></canvas></div>
    <div class="card"><h2>Distribuição de sentimento</h2><canvas id="chartSentimento"></canvas></div>
    <div class="card"><h2>Notícias por categoria</h2><canvas id="chartCategoria"></canvas></div>
    <div class="card"><h2>Evolução mensal</h2><canvas id="chartMeses"></canvas></div>
  </div>

  <div class="card">
    <h2>Notícias mais recentes</h2>
    <div class="tabela-wrap">
      <table>
        <thead><tr><th>Data</th><th>Veículo</th><th>Manchete</th><th>Sentimento</th><th>Categoria</th></tr></thead>
        <tbody>
          {linhas_tabela}
        </tbody>
      </table>
    </div>
  </div>

<script>
  const dados = {data_json};

  function corTexto() {{
    return getComputedStyle(document.documentElement).getPropertyValue('--text').trim() || '#1a1a2e';
  }}

  new Chart(document.getElementById('chartVeiculos'), {{
    type: 'bar',
    data: {{ labels: dados.veiculos_labels, datasets: [{{ label: 'Notícias', data: dados.veiculos_valores, backgroundColor: '#002878' }}] }},
    options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ ticks: {{ color: corTexto() }} }}, y: {{ ticks: {{ color: corTexto() }} }} }} }}
  }});

  new Chart(document.getElementById('chartSentimento'), {{
    type: 'doughnut',
    data: {{ labels: dados.sentimento_labels, datasets: [{{ data: dados.sentimento_valores, backgroundColor: dados.sentimento_cores }}] }},
    options: {{ plugins: {{ legend: {{ position: 'bottom', labels: {{ color: corTexto() }} }} }} }}
  }});

  new Chart(document.getElementById('chartCategoria'), {{
    type: 'bar',
    data: {{ labels: dados.categoria_labels, datasets: [{{ label: 'Notícias', data: dados.categoria_valores, backgroundColor: '#4a90d9' }}] }},
    options: {{ indexAxis: 'y', plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ ticks: {{ color: corTexto() }} }}, y: {{ ticks: {{ color: corTexto() }} }} }} }}
  }});

  new Chart(document.getElementById('chartMeses'), {{
    type: 'line',
    data: {{ labels: dados.meses_labels, datasets: [{{ label: 'Notícias/mês', data: dados.meses_valores, borderColor: '#002878', backgroundColor: 'rgba(0,40,120,0.15)', fill: true, tension: 0.3 }}] }},
    options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ ticks: {{ color: corTexto() }} }}, y: {{ ticks: {{ color: corTexto() }} }} }} }}
  }});
</script>
</body>
</html>"""
