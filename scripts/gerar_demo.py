"""
Gera um dashboard de exemplo com dados FICTÍCIOS, só para visualizar o
layout do relatório antes de haver dados reais na planilha.

Uso: python scripts/gerar_demo.py
Saída: demo_report.html (abra no navegador)
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from report import generate_html_report

random.seed(42)

# Veículos confirmados por pesquisa (ranking Comscore MMX MP citado pelo
# próprio Bahia Notícias): os maiores portais baianos por audiência digital.
VEICULOS = ["Bahia Notícias", "Correio", "A Tarde", "Ibahia", "G1 Bahia"]
CATEGORIAS = ["Institucional", "Pesquisa e Extensão", "Ensino", "Economia do Mar", "Cultura e Sociedade"]
SENTIMENTOS = ["positivo"] * 5 + ["neutro"] * 4 + ["negativo"] * 1  # distribuição plausível
MANCHETES = [
    "UFSB assina convênio com prefeitura de {cidade}",
    "UFSB abre inscrições para vestibular 2027",
    "Pesquisadores da UFSB publicam estudo sobre economia do mar",
    "UFSB e comunidade discutem impactos da cadeia do cacau",
    "Reitoria da UFSB inaugura novo laboratório em {cidade}",
    "Corte de verba federal preocupa gestão da UFSB",
    "UFSB promove festival de cultura na Semana Universitária",
    "Estudantes da UFSB vencem edital de extensão nacional",
]
CIDADES = ["Porto Seguro", "Itabuna", "Ilhéus", "Teixeira de Freitas"]

rows = []
for mes in range(1, 10):  # jan a set/2026
    for _ in range(random.randint(3, 9)):
        dia = random.randint(1, 28)
        manchete = random.choice(MANCHETES).format(cidade=random.choice(CIDADES))
        rows.append({
            "data_publicacao": f"2026-{mes:02d}-{dia:02d}",
            "veiculo": random.choice(VEICULOS),
            "categoria": random.choice(CATEGORIAS),
            "manchete": manchete,
            "link": "https://exemplo.com.br/noticia",
            "sentimento": random.choice(SENTIMENTOS),
        })

html = generate_html_report(rows, titulo="Clipping Digital — UFSB / ACS (dados de exemplo)")
out_path = Path(__file__).resolve().parents[1] / "demo_report.html"
out_path.write_text(html, encoding="utf-8")
print(f"Gerado: {out_path} ({len(rows)} notícias fictícias)")
