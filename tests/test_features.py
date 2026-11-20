import pandas as pd
from app.feature_engine import UnifiedFeatureEngine, FEATURES

def test_features_generate_expected_columns():
    idx=pd.date_range("2024-01-01",periods=100,freq="B")
    prices=pd.Series(range(100,200),index=idx,dtype=float)
    frame=pd.DataFrame({"Open":prices,"High":prices+1,"Low":prices-1,"Close":prices,"Volume":1000},index=idx)
    out=UnifiedFeatureEngine().transform(frame)
    assert set(FEATURES).issubset(out.columns)
    assert out.iloc[-1]["return_5d"]>0
