// Gekko adapter that runs the local cloned Gekko repo in the container.
const express = require('express');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const app = express();
app.use(express.json());
let proc = null;

const gekkoPath = '/opt/gekko';

app.post('/start', (req, res) => {
  if (proc && !proc.killed) return res.json({status: 'already_running'});
  const strategy = req.body || {};
  fs.writeFileSync(path.join(gekkoPath,'strategy_from_orchestrator.json'), JSON.stringify(strategy));
  // Start Gekko UI headless or run a strategy - this example runs a mock spawn that echoes the saved file.
  proc = spawn('sh', ['-c', `echo Gekko launching; cat ${path.join(gekkoPath,'strategy_from_orchestrator.json')}`], {stdio: 'inherit'});
  res.json({status: 'started'});
});

app.post('/stop', (req, res) => {
  if (!proc) return res.json({status: 'not_running'});
  proc.kill();
  proc = null;
  res.json({status: 'stopping'});
});

app.get('/status', (req, res) => {
  res.json({running: proc != null});
});

app.post('/config', (req, res) => {
  fs.writeFileSync(path.join(gekkoPath,'strategy_from_orchestrator.json'), JSON.stringify(req.body||{}));
  res.json({status: 'config_saved'});
});

const port = process.env.ADAPTER_PORT || 9002;
app.listen(port, () => console.log('Gekko adapter listening on', port));
