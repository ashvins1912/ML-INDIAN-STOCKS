"""Leakage-conscious feature definitions; only past and current bars are used."""
from typing import Optional

import numpy as np
import pandas as pd
FEATURES=["rsi14","ema20_dist","ema50_dist","atr_pct","relative_volume","return_5d","return_20d","nifty_return_20d","india_vix"]
class UnifiedFeatureEngine:
    def transform(self, frame: pd.DataFrame, nifty: Optional[pd.Series]=None, vix: Optional[pd.Series]=None):
        df=frame.copy().sort_index()
        close=df["Close"].astype(float); high=df["High"].astype(float); low=df["Low"].astype(float); vol=df["Volume"].astype(float)
        delta=close.diff(); gain=delta.clip(lower=0); loss=-delta.clip(upper=0)
        avg_gain=gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean(); avg_loss=loss.ewm(alpha=1/14,min_periods=14,adjust=False).mean()
        rs=avg_gain/avg_loss.replace(0,np.nan)
        df["rsi14"]=100-(100/(1+rs))
        for span in (20,50): df[f"ema{span}_dist"]=close/close.ewm(span=span,adjust=False,min_periods=span).mean()-1
        prev=close.shift(1); tr=pd.concat([(high-low),(high-prev).abs(),(low-prev).abs()],axis=1).max(axis=1)
        atr=tr.ewm(alpha=1/14,min_periods=14,adjust=False).mean(); df["atr_pct"]=atr/close
        df["relative_volume"]=vol/vol.rolling(20,min_periods=10).mean()
        df["return_5d"]=close.pct_change(5); df["return_20d"]=close.pct_change(20)
        if nifty is not None: df["nifty_return_20d"]=nifty.reindex(df.index).ffill().pct_change(20)
        else: df["nifty_return_20d"]=0.0
        if vix is not None: df["india_vix"]=vix.reindex(df.index).ffill()
        else: df["india_vix"]=np.nan
        return df

def make_5d_target(df: pd.DataFrame):
    # Target is based on a forward 5-session return; keep target separate from features.
    return (df["Close"].shift(-5)/df["Close"]-1 > 0).astype("Int64")
