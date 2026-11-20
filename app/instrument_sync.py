"""Best-effort NSE cash equity master sync. Provider coverage is reported, never fabricated."""
import gzip, io, json, csv
import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .db import SessionLocal
from .db_models import InstrumentMaster

URLS = {
    "angel": "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json",
    "zerodha": "https://api.kite.trade/instruments/NSE",
    "dhan": "https://images.dhan.co/api-data/api-scrip-master.csv",
    "upstox": "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz",
}

def _rows_from_csv(raw: bytes):
    text = raw.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))

def _ticker(s):
    return (s or "").strip().upper().replace("-EQ", "")

def _merge_key(row):
    isin = (row.get("isin") or "").strip().upper()
    return f"ISIN:{isin}" if isin else f"TICKER:{_ticker(row.get('ticker'))}"

def normalize_angel(rows):
    out=[]
    for r in rows:
        symbol=_ticker(r.get("symbol"))
        if not symbol or r.get("exch_seg") not in ("NSE", "NSE_EQ"): continue
        if not symbol.endswith("-EQ") and r.get("instrumenttype", "") not in ("EQ", "EQUITY"): continue
        out.append(dict(ticker=symbol, name=r.get("name", ""), isin=r.get("isin"), angel=str(r.get("token", ""))))
    return out

def normalize_zerodha(rows):
    out=[]
    for r in rows:
        if r.get("exchange") != "NSE" or r.get("segment") != "NSE": continue
        if r.get("instrument_type") not in ("EQ", "") and not str(r.get("tradingsymbol", "")).endswith("-EQ"): continue
        sym=_ticker(r.get("tradingsymbol"))
        if sym: out.append(dict(ticker=sym,name=r.get("name", ""),isin=r.get("isin"),zerodha=str(r.get("instrument_token", ""))))
    return out

def normalize_dhan(rows):
    out=[]
    for r in rows:
        exch=(r.get("EXCH_ID") or r.get("exchange") or r.get("exchange_segment") or "").upper()
        segment=(r.get("SEGMENT") or r.get("segment") or "").upper()
        if exch not in ("NSE", "NSE_EQ") and "NSE" not in exch: continue
        sym=_ticker(r.get("SYMBOL_NAME") or r.get("symbol") or r.get("TRADING_SYMBOL"))
        if not sym: continue
        out.append(dict(ticker=sym,name=r.get("DISPLAY_NAME") or r.get("name") or "",isin=r.get("ISIN") or r.get("isin"),dhan=str(r.get("SECURITY_ID") or r.get("security_id") or "")))
    return out

def normalize_upstox(rows):
    out=[]
    for r in rows:
        if (r.get("segment") or r.get("exchange") or "").upper() not in ("NSE_EQ", "NSE", "NSE|EQ"): continue
        if (r.get("instrument_type") or r.get("instrumentType") or "").upper() not in ("EQ", "EQUITY", "") : continue
        sym=_ticker(r.get("trading_symbol") or r.get("tradingsymbol") or r.get("symbol"))
        if sym: out.append(dict(ticker=sym,name=r.get("name", ""),isin=r.get("isin"),upstox=r.get("instrument_key") or r.get("instrument_token") or ""))
    return out

async def _fetch(client, name):
    res=await client.get(URLS[name], timeout=60, follow_redirects=True)
    res.raise_for_status(); raw=res.content
    if name == "angel": return normalize_angel(json.loads(raw))
    if name == "zerodha": return normalize_zerodha(_rows_from_csv(raw))
    if name == "dhan": return normalize_dhan(_rows_from_csv(raw))
    if name == "upstox":
        if raw[:2] == b"\x1f\x8b": raw=gzip.decompress(raw)
        payload=json.loads(raw)
        if isinstance(payload,dict): payload=payload.get("data", payload.get("instruments", []))
        return normalize_upstox(payload)

async def sync_all_broker_instruments():
    fetched={}; errors={}
    async with httpx.AsyncClient(headers={"User-Agent":"quant-platform/0.1 contact-admin"}) as client:
        for provider in URLS:
            try: fetched[provider]=await _fetch(client,provider)
            except Exception as e: errors[provider]=str(e)[:300]
    merged={}
    for provider,rows in fetched.items():
        for r in rows:
            key=_merge_key(r)
            if key not in merged: merged[key]={"canonical_ticker":r["ticker"],"company_name":r.get("name", ""),"isin":r.get("isin"),"exchange":"NSE","segment":"EQ"}
            rec=merged[key]
            if r.get("name") and not rec["company_name"]: rec["company_name"]=r["name"]
            if r.get("isin") and not rec.get("isin"): rec["isin"]=r["isin"]
            field={"angel":"angel_token","zerodha":"zerodha_token","dhan":"dhan_security_id","upstox":"upstox_key"}[provider]
            if r.get(provider): rec[field]=str(r[provider])
    count=0
    async with SessionLocal() as session:
        for rec in merged.values():
            stmt=insert(InstrumentMaster).values(**rec).on_conflict_do_update(index_elements=["canonical_ticker","exchange"],set_={k:v for k,v in rec.items() if k not in ("canonical_ticker","exchange")})
            await session.execute(stmt); count+=1
        await session.commit()
    coverage={p:sum(1 for r in merged.values() if r.get({"angel":"angel_token","zerodha":"zerodha_token","dhan":"dhan_security_id","upstox":"upstox_key"}[p])) for p in URLS}
    return {"upserted":count,"provider_rows":{k:len(v) for k,v in fetched.items()},"coverage":coverage,"errors":errors}
