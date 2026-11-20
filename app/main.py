from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from .db import Base,engine,SessionLocal
from .db_models import InstrumentMaster
from .instrument_sync import sync_all_broker_instruments
from .oauth_router import router as oauth_router
from .broker_adapters import adapter_for, ADAPTERS

@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn: await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
app=FastAPI(title="Indian Quant Platform",version="0.1.0",lifespan=lifespan)
app.include_router(oauth_router)
@app.get("/health")
async def health(): return {"status":"ok"}
@app.get("/api/v1/instruments/search")
async def instrument_search(q:str=Query(min_length=1,max_length=64),limit:int=Query(15,ge=1,le=50)):
    async with SessionLocal() as session:
        stmt=select(InstrumentMaster).where(or_(InstrumentMaster.canonical_ticker.ilike(f"%{q}%"),InstrumentMaster.company_name.ilike(f"%{q}%"))).order_by(InstrumentMaster.canonical_ticker).limit(limit)
        rows=(await session.execute(stmt)).scalars().all()
        return [{"ticker":r.canonical_ticker,"name":r.company_name,"isin":r.isin,"exchange":r.exchange} for r in rows]
@app.post("/api/v1/instruments/sync")
async def sync_instruments(): return await sync_all_broker_instruments()
@app.get("/api/v1/providers")
async def providers(): return {"providers":list(ADAPTERS.keys())}
@app.get("/api/v1/market/history/{ticker}")
async def history(ticker:str,provider:str="YFINANCE",period:str="1y",interval:str="1d"):
    try: adapter=adapter_for(provider.upper()); frame=await adapter.historical(ticker,period,interval)
    except Exception as exc: raise HTTPException(400,str(exc))
    if frame.empty: return {"ticker":ticker,"provider":provider,"bars":[]}
    frame=frame.reset_index(); frame.columns=[str(c) for c in frame.columns]
    return {"ticker":ticker,"provider":provider,"bars":json.loads(frame.to_json(orient="records",date_format="iso"))}
