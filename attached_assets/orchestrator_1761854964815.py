# orchestrator.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI(title="Crypto Bot Orchestrator (Full Implementation)")

BOTS = {
    "hummingbot": {"base_url": "http://hummingbot_adapter:9001", "display_name": "Hummingbot Adapter"},
    "gekko": {"base_url": "http://gekko_adapter:9002", "display_name": "Gekko Adapter"},
    "octobot": {"base_url": "http://octobot_adapter:9003", "display_name": "OctoBot Adapter"}
}

class StrategyRequest(BaseModel):
    strategy: dict = {}

@app.get("/bots")
async def list_bots():
    return [{"id": k, "display_name": v["display_name"], "base_url": v["base_url"]} for k,v in BOTS.items()]

@app.post("/bots/{bot_id}/start")
async def start_bot(bot_id: str, req: StrategyRequest):
    bot = BOTS.get(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(f"{bot['base_url']}/start", json=req.strategy)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/bots/{bot_id}/stop")
async def stop_bot(bot_id: str):
    bot = BOTS.get(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(f"{bot['base_url']}/stop")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/bots/{bot_id}/status")
async def bot_status(bot_id: str):
    bot = BOTS.get(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{bot['base_url']}/status")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/bots/{bot_id}/config")
async def set_config(bot_id: str, req: StrategyRequest):
    bot = BOTS.get(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(f"{bot['base_url']}/config", json=req.strategy)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
