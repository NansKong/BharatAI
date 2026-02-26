from app.ai.classifier import DomainClassifier


class _DummyPipeline:
    def __init__(self, labels, scores):
        self._labels = labels
        self._scores = scores

    def __call__(self, text, candidate_labels, multi_label):  # noqa: ARG002
        return {"labels": self._labels, "scores": self._scores}


def test_classifier_assigns_domain_above_threshold():
    classifier = DomainClassifier(threshold=0.6)
    classifier._pipeline = _DummyPipeline(["AI/DS", "Finance"], [0.91, 0.33])

    result = classifier.classify(
        "Machine learning fellowship with deep learning projects"
    )

    assert result.primary_domain == "ai_ds"
    assert result.secondary_domain == "finance"
    assert result.confidence == 0.91


def test_classifier_flags_unclassified_below_threshold():
    classifier = DomainClassifier(threshold=0.6)
    classifier._pipeline = _DummyPipeline(["Finance", "Management"], [0.42, 0.30])

    result = classifier.classify("General program")

    assert result.primary_domain == "unclassified"
    assert result.secondary_domain is None
    assert result.confidence == 0.42
