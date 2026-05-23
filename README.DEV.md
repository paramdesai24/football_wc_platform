# Development Setup & Commands

All commands run from the repo root in PowerShell. Use `127.0.0.1` consistently.

---

## Backend (FastAPI + Uvicorn)

### Start Backend (Stable, No Reload)

```powershell
Set-Location platform/backend-api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Expected output:
```
Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Start Backend (Development Mode with Reload)

```powershell
Set-Location platform/backend-api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Note:** Reload mode spawns watcher processes. For stable local debugging, use the stable version above.

### Verify Backend Health

```powershell
curl http://127.0.0.1:8000/health
```

Expected response:
```
200 OK
```

---

## Frontend (React + Vite)

### Start Frontend Dev Server

```powershell
Set-Location frontend
npm run dev
```

Expected output:
```
  VITE v5.1.0  ready in XXX ms

  ➜  Local:   http://127.0.0.1:3000/
```

---

## Process & Port Management

### Check Listeners on Port 8000

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
```

Expected output (if backend running):
```
LocalAddress LocalPort State  OwningProcess
------------- --------- ------ --------
127.0.0.1    8000      Listen 12345
```

### Check All Development Ports (3000, 3001, 3002, 8000, 8001, 8500)

```powershell
Get-NetTCPConnection -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' -and $_.LocalPort -in @(3000,3001,3002,8000,8001,8500) } | Select-Object LocalAddress, LocalPort, OwningProcess | Format-Table -AutoSize
```

### Inspect Python Processes

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' } | Select-Object ProcessId, ParentProcessId, Name, CommandLine | Format-List
```

This shows Python process hierarchy. Multiple PIDs indicate reload watchers spawning children.

### Inspect Node Processes

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'node*' } | Select-Object ProcessId, ParentProcessId, Name, CommandLine | Format-List
```

This shows Node/Vite process hierarchy.

---

## Cleanup

### Kill All Listeners on Port 8000

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' } | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force }
```

### Kill All Listeners on Common Dev Ports (3000, 3001, 3002, 8000, 8001, 8500)

```powershell
@(3000,3001,3002,8000,8001,8500) | ForEach-Object { Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' } | Select-Object -ExpandProperty OwningProcess -Unique } | Sort-Object -Unique | ForEach-Object { Stop-Process -Id $_ -Force }
```

---

## Troubleshooting

### Backend Binds to Wrong Address

**Symptom:** Backend logs say it's listening, but `curl http://127.0.0.1:8000/health` times out.

**Cause:** uvicorn binding to IPv6 `::1` instead of IPv4 `127.0.0.1`, or `0.0.0.0` not resolving correctly on this machine.

**Fix:** Ensure the startup command uses `--host 127.0.0.1` (not `localhost` or `0.0.0.0`).

### Port Still Listening After Kill

**Symptom:** `Get-NetTCPConnection -LocalPort 8000` still shows listeners after stopping the process.

**Cause:** Multiple independent processes bound to the port (e.g., multiple uvicorn instances, VS Code task auto-restart, or external service).

**Check:** Run the process inspection commands above to identify parent/child chains. If multiple Python PIDs exist, kill the parent (lower PID number, often the watcher).

### Vite Crash: "FS Watcher Error"

**Symptom:** Vite crashes with `Error: UNKNOWN: unknown error` when watching files.

**Cause:** Vite watcher trying to monitor `.venv` directory with many files (pyarrow, numpy, etc.).

**Fix:** Ensure `vite.config.ts` includes:
```ts
server: {
  watch: {
    ignored: ['**/.git/**', '**/.venv/**', '**/venv/**', '**/__pycache__/**', '**/node_modules/**', '**/dist/**', '**/build/**']
  }
}
```

### CIM/WMI Queries Hang or Timeout

**Symptom:** `Get-CimInstance Win32_Process` or similar commands hang indefinitely.

**Cause:** Windows Management Instrumentation under heavy churn (many process spawns/kills).

**Fix:** 
- Run PowerShell as Administrator
- Add `-OperationTimeoutSec 2` to CIM queries
- Use `Get-Process` instead (faster, but less detailed):
  ```powershell
  Get-Process python, node | Select-Object Id, ProcessName, Handles | Format-Table
  ```

### Multiple Listeners on Same Port

**Symptom:** netstat or CIM shows 2-4 PIDs listening on 8000, none are active Python.

**Cause:** 
- Reload mode spawning multiple worker processes.
- Zombie/TIME_WAIT sockets not yet cleaned up.
- External watcher (npm concurrently, supervisor, VS Code task) restarting process.

**Fix:**
1. Restart the machine (nuclear option).
2. Or: Use `netstat -ano | Select-String ':8000'` to see socket states; kill only `LISTENING` entries, ignore `TIME_WAIT` and `FIN_WAIT_2`.
3. Or: Use backend in stable mode (no `--reload`) to avoid watcher recursion.

### IPv4 vs IPv6 Confusion

**Symptom:** netstat shows listeners on `::1:3000` but curl uses `127.0.0.1:3000`.

**Fix:** Always use `127.0.0.1` in all commands and env vars. Never use `localhost` (resolves to IPv6 first on some Windows configs).

---

## Environment Variables

If you want to set env vars before running npm scripts:

```powershell
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
$env:VITE_USE_MOCKS = 'false'
Set-Location frontend
npm run dev
```

Or in `.env.local` (frontend):
```
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_USE_MOCKS=false
```

---

## Expected Success Indicators

✓ Backend: Uvicorn runs without errors on `127.0.0.1:8000`  
✓ Frontend: Vite runs on `127.0.0.1:3000`  
✓ Health: `GET /health` returns 200  
✓ Rankings: `GET /api/v1/countries/rankings` returns JSON  
✓ One listener per port: Only one PID per port during normal operation  
✓ Clean shutdown: Ports free within 2 seconds of process termination
