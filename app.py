"""Panel de monitoreo del sistema operativo.
Backend Flask que expone métricas del SO (CPU, memoria, disco, red, procesos)
leídas con psutil. El frontend las consulta cada pocos segundos."""
import os
import platform
import threading
import time

import psutil
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Primera llamada para "calentar" los contadores de CPU por proceso
psutil.cpu_percent(interval=None)
for p in psutil.process_iter():
    try:
        p.cpu_percent(None)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

CORES = psutil.cpu_count(logical=True) or 1
_cpu = {"percent": 0.0, "per_core": [0.0] * CORES}


def _cpu_sampler():
    """Mide el CPU cada segundo en un hilo aparte (evita lecturas de 0%)."""
    while True:
        per = psutil.cpu_percent(interval=1, percpu=True)
        _cpu["per_core"] = per
        _cpu["percent"] = round(sum(per) / len(per), 1)


threading.Thread(target=_cpu_sampler, daemon=True).start()

_last_net = {"t": time.time(), "io": psutil.net_io_counters()}


def top_processes(n=8):
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "status"]):
        try:
            if p.info["pid"] == 0:  # "System Idle Process" no es consumo real
                continue
            procs.append({
                "pid": p.info["pid"],
                "name": p.info["name"] or "?",
                "cpu": round(min(p.cpu_percent(None) / CORES, 100), 1),
                "mem": round(p.info["memory_percent"] or 0, 1),
                "status": p.info["status"],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: (x["cpu"], x["mem"]), reverse=True)
    return procs[:n]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/api/stats")
def stats():
    global _last_net
    now = time.time()
    io = psutil.net_io_counters()
    dt = max(now - _last_net["t"], 1e-6)
    up = (io.bytes_sent - _last_net["io"].bytes_sent) / dt
    down = (io.bytes_recv - _last_net["io"].bytes_recv) / dt
    _last_net = {"t": now, "io": io}

    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    disk = psutil.disk_usage("/")
    try:
        load = [round(x, 2) for x in os.getloadavg()]
    except (AttributeError, OSError):
        load = None

    return jsonify({
        "host": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "uptime_s": int(now - psutil.boot_time()),
        "cpu": {
            "percent": _cpu["percent"],
            "per_core": _cpu["per_core"],
            "cores": CORES,
            "load": load,
        },
        "memory": {"percent": vm.percent, "used": vm.used, "total": vm.total},
        "swap": {"percent": sw.percent, "used": sw.used, "total": sw.total},
        "disk": {"percent": disk.percent, "used": disk.used, "total": disk.total},
        "network": {"up_bps": max(up, 0), "down_bps": max(down, 0)},
        "processes": top_processes(),
        "process_count": len(psutil.pids()),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
