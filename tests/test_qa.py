import pytest
from datetime import datetime
from app.qa_validator import Candle,gap_requires_review

def test_valid_candle():
    Candle(ticker="ABC",timestamp=datetime.now(),open=100,high=110,low=90,close=105,volume=12)
def test_bad_high_rejected():
    with pytest.raises(ValueError): Candle(ticker="ABC",timestamp=datetime.now(),open=100,high=101,low=90,close=105,volume=1)
def test_gap_quarantine_threshold():
    assert gap_requires_review(100,123)
    assert not gap_requires_review(100,120)
