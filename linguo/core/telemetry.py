"""
Linguo Telemetry, Profiling & Rotating Logging
Provides sub-millisecond latency profiling and 30-day NDJSON event logging.
"""

import time
import json
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from .config import LOGS_DIR

_LAST_LOG_CLEANUP = 0.0


def rotate_and_cleanup_logs(max_days: int = 30):
    """Parsimonious log retention: purges daily log files older than max_days (30 days)."""
    global _LAST_LOG_CLEANUP
    now = time.time()
    if now - _LAST_LOG_CLEANUP < 3600:
        return
    _LAST_LOG_CLEANUP = now
    cutoff = now - (max_days * 86400)
    for f in LOGS_DIR.glob("linguo_*.log"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
        except Exception:
            pass


def log_event(level: str, component: str, message: str, meta: dict | None = None):
    """Appends structured log to daily rotating file and emits NDJSON for Vector/Loki ingestion."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        rotate_and_cleanup_logs(30)
        now_dt = datetime.now()
        today = now_dt.strftime("%Y-%m-%d")
        log_file = LOGS_DIR / f"linguo_{today}.log"
        jsonl_file = LOGS_DIR / "linguo_events.jsonl"
        ts = now_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        meta_str = f" | {json.dumps(meta, ensure_ascii=False)}" if meta else ""
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [{level.upper()}] [{component}] {message}{meta_str}\n")

        # Emit single-line NDJSON for enterprise log aggregation (Vector / Loki / Promtail)
        json_entry = {
            "timestamp": now_dt.isoformat(),
            "level": level.upper(),
            "component": component,
            "message": message,
            "meta": meta or {}
        }
        with open(jsonl_file, "a", encoding="utf-8") as f_json:
            f_json.write(json.dumps(json_entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


class PerfTracker:
    """Measures execution latency across individual operations to profile bottlenecks and fix bugs."""
    def __init__(self, action: str):
        self.action = action
        self.timings = {}
        self.start_total = time.perf_counter()

    @contextmanager
    def measure(self, step_name: str):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            dt_ms = (time.perf_counter() - t0) * 1000.0
            self.timings[step_name] = round(dt_ms, 2)

    def finish(self) -> dict:
        total_ms = (time.perf_counter() - self.start_total) * 1000.0
        self.timings["total_ms"] = round(total_ms, 2)
        log_event("INFO", "PERF", f"{self.action} completed", self.timings)
        return self.timings


def print_trace_summary(timings: dict):
    """Prints a styled execution latency table to diagnose pipeline bottlenecks."""
    print("\n\033[1;36m⏱️  ─── Linguo Latency & Bottleneck Trace ───\033[0m")
    total = timings.get("total_ms", 1.0)
    for step, ms in timings.items():
        if step == "total_ms":
            continue
        pct = (ms / total) * 100.0 if total > 0 else 0
        bar = "█" * int(min(20, max(1, pct / 5)))
        print(f"  • \033[1;33m{step.ljust(22)}\033[0m: \033[1m{ms:>7.2f} ms\033[0m ({pct:>5.1f}%) \033[90m{bar}\033[0m")
    print(f"  ──────────────────────────────────────────")
    print(f"  🏁 \033[1;32m{'Total Pipeline'.ljust(20)}\033[0m: \033[1;32m{total:>7.2f} ms\033[0m\n")


def show_logs(limit: int = 30):
    """Displays the last N structured log entries from the 30-day rotating logs."""
    rotate_and_cleanup_logs(30)
    log_files = sorted(LOGS_DIR.glob("linguo_*.log"))
    if not log_files:
        print("\n\033[1;33m📋 Nessun file di log recente presente in:\033[0m", LOGS_DIR)
        return

    print(f"\n\033[1;36m📋 ─── Linguo Logs (Ultime {limit} voci, retention 30 giorni) ───\033[0m\n")
    all_lines = []
    for lf in log_files[-3:]:
        try:
            with open(lf, "r", encoding="utf-8") as f:
                all_lines.extend(f.readlines())
        except Exception:
            pass

    for line in all_lines[-limit:]:
        line = line.strip()
        if "[PERF]" in line:
            print(f"\033[90m{line}\033[0m")
        elif "[ERROR]" in line or "[ERR]" in line:
            print(f"\033[1;31m{line}\033[0m")
        elif "[WARN]" in line:
            print(f"\033[1;33m{line}\033[0m")
        else:
            print(f"\033[36m{line}\033[0m")
    print()
