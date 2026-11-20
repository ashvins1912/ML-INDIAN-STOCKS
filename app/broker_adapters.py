from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
import yfinance as yf

class BaseMarketAdapter(ABC):
    provider="BASE"
    @abstractmethod
    async def historical(self, ticker:str, period="1y", interval="1d")->pd.DataFrame: ...

class YFinanceAdapter(BaseMarketAdapter):
    provider="YFINANCE"
    async def historical(self,ticker,period="1y",interval="1d"):
        symbol=ticker if ticker.endswith(".NS") else f"{ticker}.NS"
        frame=yf.download(symbol,period=period,interval=interval,auto_adjust=False,progress=False)
        if frame is None or frame.empty: return pd.DataFrame()
        if isinstance(frame.columns,pd.MultiIndex): frame.columns=frame.columns.get_level_values(0)
        return frame

class _BrokerAdapter(BaseMarketAdapter):
    async def historical(self,ticker,period="1y",interval="1d"):
        raise NotImplementedError(f"{self.provider} market history requires an authenticated session and API entitlement")
class AngelOneAdapter(_BrokerAdapter): provider="ANGEL_ONE"
class ZerodhaAdapter(_BrokerAdapter): provider="ZERODHA"
class DhanAdapter(_BrokerAdapter): provider="DHAN"
class UpstoxAdapter(_BrokerAdapter): provider="UPSTOX"

ADAPTERS={"ANGEL_ONE":AngelOneAdapter,"ZERODHA":ZerodhaAdapter,"DHAN":DhanAdapter,"UPSTOX":UpstoxAdapter,"YFINANCE":YFinanceAdapter}
def adapter_for(provider):
    if provider not in ADAPTERS: raise ValueError(f"Unsupported provider: {provider}")
    return ADAPTERS[provider]()
