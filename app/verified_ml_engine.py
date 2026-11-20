"""Train/test helpers and baseline calibrated ensemble. Tune only with temporal folds."""
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss
from sklearn.base import clone
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

class PurgedDateTimeSeriesSplit:
    def __init__(self, n_splits=5, embargo_sessions=6): self.n_splits=n_splits; self.embargo_sessions=embargo_sessions
    def split(self, X, dates):
        dates=np.asarray(dates); unique=np.unique(dates); base=TimeSeriesSplit(self.n_splits)
        for tr,te in base.split(unique):
            train_dates=unique[tr]; test_dates=unique[te]
            if len(test_dates)==0: continue
            embargo_start=test_dates[0]
            train_dates=train_dates[train_dates < embargo_start]
            if len(train_dates)==0: continue
            cutoff_idx=np.searchsorted(unique, test_dates[0])-self.embargo_sessions
            if cutoff_idx<=0: continue
            allowed=unique[:cutoff_idx]
            train_idx=np.where(np.isin(dates,allowed))[0]; test_idx=np.where(np.isin(dates,test_dates))[0]
            if len(train_idx) and len(test_idx): yield train_idx,test_idx

def default_models():
    return {
      "lightgbm":LGBMClassifier(n_estimators=350,learning_rate=.035,num_leaves=24,max_depth=-1,subsample=.85,colsample_bytree=.85,verbosity=-1),
      "xgboost":XGBClassifier(n_estimators=350,max_depth=4,learning_rate=.035,subsample=.85,colsample_bytree=.85,eval_metric="logloss",n_jobs=4)
    }

def fit_calibrated(X_train,y_train,model,cv=3):
    # Caller must provide temporally isolated training/calibration data in production.
    calibrated=CalibratedClassifierCV(estimator=model,method="isotonic",cv=cv)
    return calibrated.fit(X_train,y_train)

def brier(y,p): return brier_score_loss(y,p)

def consensus(p_lgb,p_xgb,cutoff=.65,spread_max=.12,vix=None):
    spread=abs(p_lgb-p_xgb); avg=(p_lgb+p_xgb)/2
    blocked=(vix is not None and vix>24) or spread>=spread_max or min(p_lgb,p_xgb)<cutoff
    return {"probability":float(avg),"spread":float(spread),"signal":"CONFIRMED_BUY" if not blocked else "WATCH","blocked_reason":"VIX_HIGH" if vix is not None and vix>24 else "CONSENSUS_FAIL" if blocked else None}
