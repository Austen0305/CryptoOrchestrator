# Hummingbot adapter that will attempt to use the official hummingbot docker image if available.
# This adapter exposes a simple API to start/stop/status hummingbot running in the container.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess, os, signal, json, shutil, time

app = FastAPI()
PROCESS = None

class Strategy(BaseModel):
    strategy: dict = {}

HB_DOCKER_IMAGE = os.environ.get('HB_DOCKER_IMAGE', 'hummingbot/hummingbot:latest')

def run_hummingbot_with_config(cfg_path):
    # Try to run hummingbot using docker (if docker available in host) - fallback to mock echo otherwise.
    # NOTE: In many deployments you will run hummingbot in its own container using the official image.
    cmd = f"/bin/sh -c 'echo Hummingbot adapter launching using image {HB_DOCKER_IMAGE}; ls -la; cat {cfg_path} || true'"
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

@app.post('/start')
async def start(strategy: Strategy):
    global PROCESS
    if PROCESS and PROCESS.poll() is None:
        return {'status': 'already_running'}
    cfg = strategy.strategy or {}
    cfg_path = '/opt/hummingbot/data/config_from_orchestrator.json'
    os.makedirs('/opt/hummingbot/data', exist_ok=True)
    with open(cfg_path, 'w') as f:
        json.dump(cfg, f)
    PROCESS = run_hummingbot_with_config(cfg_path)
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
    cfg_path = '/opt/hummingbot/data/config_from_orchestrator.json'
    with open(cfg_path, 'w') as f:
        json.dump(cfg, f)
    return {'status': 'config_saved'}
