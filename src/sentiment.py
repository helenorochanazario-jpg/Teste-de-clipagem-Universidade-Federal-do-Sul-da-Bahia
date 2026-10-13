"""
Classificação de sentimento (positivo / neutro / negativo) das manchetes.

FERRAMENTA ESCOLHIDA: pysentimiento (https://github.com/pysentimiento/pysentimiento)
  - Biblioteca aberta (MIT), mantida por pesquisadores (UBA/Argentina),
    com modelo dedicado para português: `create_analyzer(task="sentiment", lang="pt")`.
  - O modelo (BERTabaporu, RoBERTa treinado em tuítes em PT-BR) já classifica
    diretamente em POS / NEU / NEG — bate exatamente com o requisito.
  - Roda localmente (CPU é suficiente para o volume de um clipping
    institucional), sem custo por chamada, ao contrário de APIs comerciais
    (ex. Google Cloud NLP, AWS Comprehend).

RESSALVA HONESTA: o modelo foi treinado em tuítes, não em manchetes
jornalísticas — tende a acertar bem o tom geral, mas pode ser menos preciso
em textos mais formais/ambíguos ("UFSB abre inscrições" tende a NEU, o que
é correto, mas ironia ou crítica indireta em texto de opinião pode escapar).
Trate os relatórios de sentimento como indicativo, não como medição exata —
uma amostra revisada manualmente de tempos em tempos é recomendável.

LIMITAÇÃO DESTE AMBIENTE DE TESTE: baixar os pesos do modelo exige acesso à
Hugging Face Hub, que não está disponível na rede restrita deste sandbox.
Por isso este módulo foi desenhado com uma interface (`SentimentClassifier`)
que pode ser testada com um analisador falso (`_FakeAnalyzer`), e o
carregamento real (`load_real_analyzer`) só é chamado em produção, onde a
rede está liberada.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SentimentResult:
    label: str  # "positivo" | "neutro" | "negativo"
    score: float  # confiança do rótulo vencedor, 0-1


_LABEL_MAP = {"POS": "positivo", "NEU": "neutro", "NEG": "negativo"}


class _AnalyzerProtocol(Protocol):
    def predict(self, text: str):
        ...


def load_real_analyzer() -> "_AnalyzerProtocol":
    """
    Carrega o analisador real. Só funciona com acesso à internet (baixa os
    pesos do modelo no primeiro uso, ~500MB, depois fica em cache local).
    Chame isso uma vez no início do pipeline, não a cada notícia.
    """
    from pysentimiento import create_analyzer  # import local: dependência pesada
    return create_analyzer(task="sentiment", lang="pt")


class SentimentClassifier:
    """Wrapper fino em torno do analisador — permite trocar a implementação
    (ex. em teste) sem mudar o restante do pipeline."""

    def __init__(self, analyzer: "_AnalyzerProtocol"):
        self._analyzer = analyzer

    def classify(self, text: str) -> SentimentResult:
        output = self._analyzer.predict(text)
        label = _LABEL_MAP.get(output.output, "neutro")
        score = float(output.probas.get(output.output, 0.0))
        return SentimentResult(label=label, score=score)

    def classify_batch(self, texts: list[str]) -> list[SentimentResult]:
        return [self.classify(t) for t in texts]
