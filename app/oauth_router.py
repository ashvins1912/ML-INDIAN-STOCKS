from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from .config import settings
from .session_manager import create_oauth_state, consume_oauth_state
router=APIRouter(prefix="/api/v1/auth",tags=["auth"])
class OAuthInit(BaseModel):
    provider:str
    user_id:str="local-user"
@router.post("/init")
async def oauth_init(payload:OAuthInit):
    provider=payload.provider.upper()
    if provider not in ("ZERODHA","UPSTOX"): raise HTTPException(400,"OAuth is supported for Zerodha and Upstox only")
    state=await create_oauth_state(provider)
    # OAuth URLs need API credentials and broker-side registered callback URLs. Avoid leaking secrets here.
    return {"provider":provider,"state":state,"message":"State created. Configure provider client ID and callback URI before redirect flow."}
@router.get("/zerodha/callback")
async def zerodha_callback(request_token:Optional[str]=None,state:Optional[str]=None):
    if not state or not await consume_oauth_state(state,"ZERODHA"): raise HTTPException(400,"Invalid or expired OAuth state")
    if not request_token: raise HTTPException(400,"Missing request_token; token exchange is not configured without broker API key/secret")
    # Deliberately do not store unexchanged callback tokens as access tokens.
    return RedirectResponse(settings.frontend_url+"/?auth=received&provider=zerodha")
@router.get("/upstox/callback")
async def upstox_callback(code:Optional[str]=None,state:Optional[str]=None):
    if not state or not await consume_oauth_state(state,"UPSTOX"): raise HTTPException(400,"Invalid or expired OAuth state")
    if not code: raise HTTPException(400,"Missing authorization code")
    return RedirectResponse(settings.frontend_url+"/?auth=received&provider=upstox")
