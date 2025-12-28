from pyramid_audit.analysis import score_discrepancy


def test_no_data_discrepancy():
    score = score_discrepancy([], [])
    assert score["severity"] == "none"
    assert score["likely_cause"] == "no_data"


def test_directionality_mismatch():
    score = score_discrepancy(["A"], ["A"], directionality_mismatch=True)
    assert score["severity"] == "major"
    assert score["likely_cause"] == "directionality_mismatch"


def test_minor_discrepancy():
    score = score_discrepancy(["A", "B"], ["A", "C"])
    assert score["severity"] == "minor"


def test_critical_discrepancy():
    score = score_discrepancy(["A", "B", "C", "D"], ["X"]) 
    assert score["severity"] == "critical"
