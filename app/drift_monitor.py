from sqlalchemy import select
from .db import SessionLocal
from .db_models import PredictionLog
async def grade_matured_predictions():
    # Placeholder for price-return joins. The grading process should only mark records matured
    # after the five-session forward window and actual-price data are available.
    async with SessionLocal() as db:
        matured=await db.execute(select(PredictionLog).where(PredictionLog.matured.is_(False)))
        rows=matured.scalars().all()
        return {"pending_grading":len(rows),"graded":0,"note":"Add verified OHLC outcome join before enabling force-retrain trigger."}
