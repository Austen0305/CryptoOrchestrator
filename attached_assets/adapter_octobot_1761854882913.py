# OctoBot adapter - runs OctoBot from the cloned repo inside the container.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess, os, signal, json, time

app = FastAPI()
PROCESS = None
OCTOBOT_DIR = '/opt/octobot'

class Strategy(BaseModel):
    strategy: dict = {}

def start_octobot():
    # Start OctoBot via the python start.py script in the cloned repo
    cmd = f"python3 {OCTOBOT_DIR}/start.py"
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

@app.post('/start')
async def start(strategy: Strategy):
    global PROCESS
    if PROCESS and PROCESS.poll() is None:
        return {'status': 'already_running'}
    cfg = strategy.strategy or {}
    cfg_path = '/opt/octobot/user/config_from_orchestrator.json'
    os.makedirs('/opt/octobot/user', exist_ok=True)
    with open(cfg_path, 'w') as f:
        json.dump(cfg, f)
    PROCESS = start_octobot()
    return {'status': 'started'}

@app.post('/stop')
async def stop():
    global PROCESS
    if not PROCESS or PROCESS.poll() is not None:
        return {'status': 'not_running'}
    os.killpg(os.getpgid(PROCESS.pid), signal.SIGTERM)
    return {'status': 'stopping'}

@app.get('/status')
async def status():
    global PROCESS
    running = PROCESS and PROCESS.poll() is None
    return {'running': bool(running)}

@app.post('/config')
async def config(strategy: Strategy):
    cfg = strategy.strategy or {}
    cfg_path = '/opt/octobot/user/config_from_orchestrator.json'
    with open(cfg_path, 'w') as f:
        json.dump(cfg, f)
    return {'status': 'config_saved'}
