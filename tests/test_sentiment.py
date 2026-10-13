import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sentiment import SentimentClassifier


@dataclass
class _FakeOutput:
    output: str
    probas: dict


class _FakeAnalyzer:
    """
    Simula a interface real do pysentimiento
    (AnalyzerOutput com .output e .probas), sem baixar nenhum modelo.
    Isso testa a integração do nosso wrapper com o formato de saída
    documentado da biblioteca, não a qualidade do modelo em si — a
    qualidade do modelo real só pode ser avaliada com acesso à rede,
    fora deste sandbox.
    """
    _CANNED = {
        "ótima notícia": _FakeOutput("POS", {"POS": 0.97, "NEU": 0.02, "NEG": 0.01}),
        "nota neutra": _FakeOutput("NEU", {"POS": 0.10, "NEU": 0.85, "NEG": 0.05}),
        "péssima gestão": _FakeOutput("NEG", {"POS": 0.02, "NEU": 0.08, "NEG": 0.90}),
    }

    def predict(self, text: str):
        return self._CANNED.get(text, _FakeOutput("NEU", {"POS": 0.3, "NEU": 0.4, "NEG": 0.3}))


def test_classify_maps_pos_neu_neg_to_portuguese_labels():
    clf = SentimentClassifier(_FakeAnalyzer())
    assert clf.classify("ótima notícia").label == "positivo"
    assert clf.classify("nota neutra").label == "neutro"
    assert clf.classify("péssima gestão").label == "negativo"


def test_classify_returns_confidence_score():
    clf = SentimentClassifier(_FakeAnalyzer())
    result = clf.classify("péssima gestão")
    assert 0.0 <= result.score <= 1.0
    assert result.score == 0.90


def test_classify_unknown_label_defaults_to_neutro():
    clf = SentimentClassifier(_FakeAnalyzer())
    result = clf.classify("texto não previsto no fake")
    assert result.label == "neutro"


def test_classify_batch_preserves_order():
    clf = SentimentClassifier(_FakeAnalyzer())
    results = clf.classify_batch(["ótima notícia", "péssima gestão", "nota neutra"])
    assert [r.label for r in results] == ["positivo", "negativo", "neutro"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
