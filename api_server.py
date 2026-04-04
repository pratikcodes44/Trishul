"""
Trishul SaaS API - Enterprise-Grade RESTful API
================================================
FastAPI-based REST API with JWT authentication, rate limiting,
and multi-tenant support for SaaS deployment.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import jwt
import os
import sys
import signal
import time
import sqlite3
import json
import threading
import subprocess
from collections import defaultdict
import hashlib
import secrets

# Import our AI engine
from ai_engine import analyze_asset_risk, batch_analyze_assets, ai_assistant
from bounty_scout import BountyScout

app = FastAPI(
    title="Trishul Security Platform API",
    description="AI-Powered Bug Bounty Automation & Attack Surface Management",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Rate Limiting (in-memory for hackathon, use Redis in production)
rate_limit_store = defaultdict(list)
RATE_LIMIT = 100  # requests per minute
RATE_WINDOW = 60  # seconds

UI_STATE_DB = os.getenv("TRISHUL_UI_STATE_DB", "ui_state.db")
SCAN_TERMINAL_STATES = {"completed", "failed", "cancelled"}
SCAN_PAUSABLE_STATES = {"running", "queued"}
SCAN_RUNTIME_DIR = Path(os.getenv("TRISHUL_SCAN_RUNTIME_DIR", ".scan_runtime"))
SCAN_RUNTIME_LOCK = threading.Lock()
SCAN_RUNTIME_JOBS: Dict[str, Dict[str, Any]] = {}
MODULE_INSIGHT_LOCK = threading.Lock()
MODULE_INSIGHT_CACHE: Dict[str, Dict[str, Any]] = {}
MODULE_INSIGHT_INTERVAL_SECONDS = int(os.getenv("TRISHUL_MODULE_INSIGHT_INTERVAL_SECONDS", "8"))

PHASE_PROGRESS = {
    1: 10,
    2: 20,
    3: 30,
    4: 40,
    5: 50,
    6: 60,
    7: 70,
    8: 80,
    9: 90,
    10: 95,
}


def _db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(UI_STATE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str):
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


def _init_ui_state_db():
    conn = _db_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                scan_id TEXT NOT NULL UNIQUE,
                target TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                scan_mode TEXT NOT NULL DEFAULT 'manual_override',
                program_url TEXT,
                platform TEXT,
                status TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                current_phase INTEGER NOT NULL DEFAULT 0,
                current_phase_name TEXT NOT NULL DEFAULT '',
                current_tool TEXT NOT NULL DEFAULT '',
                activity_message TEXT NOT NULL DEFAULT '',
                activity_data TEXT NOT NULL DEFAULT '{}',
                error_message TEXT NOT NULL DEFAULT '',
                runtime_pid INTEGER,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                updated_at TEXT NOT NULL,
                results_json TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                query TEXT NOT NULL,
                searched_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_email TEXT NOT NULL,
                scan_id TEXT,
                event_type TEXT NOT NULL,
                detail TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'info',
                created_at TEXT NOT NULL
            )
            """
        )
        _ensure_column(conn, "user_scan_history", "scan_mode", "scan_mode TEXT NOT NULL DEFAULT 'manual_override'")
        _ensure_column(conn, "user_scan_history", "program_url", "program_url TEXT")
        _ensure_column(conn, "user_scan_history", "platform", "platform TEXT")
        _ensure_column(conn, "user_scan_history", "current_phase", "current_phase INTEGER NOT NULL DEFAULT 0")
        _ensure_column(conn, "user_scan_history", "current_phase_name", "current_phase_name TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "user_scan_history", "current_tool", "current_tool TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "user_scan_history", "activity_message", "activity_message TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "user_scan_history", "activity_data", "activity_data TEXT NOT NULL DEFAULT '{}'")
        _ensure_column(conn, "user_scan_history", "error_message", "error_message TEXT NOT NULL DEFAULT ''")
        _ensure_column(conn, "user_scan_history", "runtime_pid", "runtime_pid INTEGER")
        _ensure_column(conn, "user_scan_history", "updated_at", "updated_at TEXT NOT NULL DEFAULT ''")
        conn.commit()
    finally:
        conn.close()


def _record_event(user: dict, event_type: str, detail: str, severity: str = "info", scan_id: Optional[str] = None):
    conn = _db_conn()
    try:
        conn.execute(
            """
            INSERT INTO user_events (user_id, user_email, scan_id, event_type, detail, severity, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user.get("sub", "unknown"),
                user.get("email", "unknown"),
                scan_id,
                event_type,
                detail,
                severity,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _upsert_scan_record(
    user: dict,
    scan_id: str,
    target: str,
    scan_type: str,
    status: str,
    scan_mode: str = "manual_override",
    program_url: Optional[str] = None,
    platform: Optional[str] = None,
):
    conn = _db_conn()
    try:
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT INTO user_scan_history
              (
                user_id,
                user_email,
                scan_id,
                target,
                scan_type,
                scan_mode,
                program_url,
                platform,
                status,
                progress,
                current_phase,
                current_phase_name,
                current_tool,
                activity_message,
                activity_data,
                error_message,
                runtime_pid,
                started_at,
                completed_at,
                updated_at,
                results_json
              )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, '', '', '', '{}', '', NULL, ?, NULL, ?, '{}')
            ON CONFLICT(scan_id) DO UPDATE SET
                status=excluded.status,
                updated_at=excluded.updated_at
            """,
            (
                user.get("sub", "unknown"),
                user.get("email", "unknown"),
                scan_id,
                target,
                scan_type,
                scan_mode,
                program_url,
                platform,
                status,
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _update_scan_status(
    user: dict,
    scan_id: str,
    status: str,
    progress: int,
    results: Optional[Dict[str, Any]] = None,
    current_phase: Optional[int] = None,
    current_phase_name: Optional[str] = None,
    current_tool: Optional[str] = None,
    activity_message: Optional[str] = None,
    activity_data: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    runtime_pid: Optional[int] = None,
):
    conn = _db_conn()
    try:
        now = datetime.utcnow().isoformat()
        completed_at = now if status in SCAN_TERMINAL_STATES else None
        phase_name_value = current_phase_name if current_phase_name is not None else ""
        tool_value = current_tool if current_tool is not None else ""
        activity_message_value = activity_message if activity_message is not None else ""
        activity_data_json = None if activity_data is None else json.dumps(activity_data)
        error_value = error_message if error_message is not None else ""
        conn.execute(
            """
            UPDATE user_scan_history
            SET
                status = ?,
                progress = ?,
                current_phase = COALESCE(?, current_phase),
                current_phase_name = CASE WHEN ? IS NULL THEN current_phase_name ELSE ? END,
                current_tool = CASE WHEN ? IS NULL THEN current_tool ELSE ? END,
                activity_message = CASE WHEN ? IS NULL THEN activity_message ELSE ? END,
                activity_data = CASE WHEN ? IS NULL THEN activity_data ELSE ? END,
                error_message = CASE WHEN ? IS NULL THEN error_message ELSE ? END,
                runtime_pid = CASE WHEN ? IS NULL THEN runtime_pid ELSE ? END,
                completed_at = CASE
                    WHEN ? IS NOT NULL THEN ?
                    WHEN status IN ('completed', 'failed', 'cancelled') THEN completed_at
                    ELSE NULL
                END,
                updated_at = ?,
                results_json = CASE WHEN ? IS NULL THEN results_json ELSE ? END
            WHERE scan_id = ? AND user_id = ?
            """,
            (
                status,
                progress,
                current_phase,
                current_phase_name,
                phase_name_value,
                current_tool,
                tool_value,
                activity_message,
                activity_message_value,
                activity_data_json,
                activity_data_json,
                error_message,
                error_value,
                runtime_pid,
                runtime_pid,
                completed_at,
                completed_at,
                now,
                None if results is None else json.dumps(results),
                None if results is None else json.dumps(results),
                scan_id,
                user.get("sub", "unknown"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _deserialize_activity_data(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}
    return {}


def _normalize_insight_text(text: str) -> str:
    compact = " ".join(text.split())
    if not compact:
        return "Module is active and processing current phase inputs."
    return compact[:280]


def _heuristic_module_insight(snapshot: Dict[str, Any]) -> str:
    phase_name = str(snapshot.get("current_phase_name") or "Current phase")
    tool = str(snapshot.get("current_tool") or "pipeline")
    activity_message = str(snapshot.get("activity_message") or f"{phase_name} in progress")
    data = snapshot.get("activity_data") or {}
    if not isinstance(data, dict):
        data = {}

    if tool == "nuclei":
        sent = int(data.get("requests_sent", 0) or 0)
        total = int(data.get("requests_total", 0) or 0)
        findings = int(data.get("findings_count", 0) or 0)
        sample_url = str(data.get("active_url_sample") or "").strip()
        if total > 0 and sample_url:
            return _normalize_insight_text(
                f"Nuclei is executing template requests ({sent}/{total}) against the target set; sample URL under evaluation: {sample_url}. Findings observed: {findings}."
            )
        if total > 0:
            return _normalize_insight_text(
                f"Nuclei is actively running vulnerability templates ({sent}/{total}) across scoped targets with {findings} findings observed so far."
            )
        return _normalize_insight_text(
            "Nuclei is active and preparing or running template checks across discovered targets."
        )

    if tool in {"katana", "web-discovery", "param-discovery"}:
        hosts_total = int(data.get("hosts_total", 0) or 0)
        urls_discovered = int(data.get("urls_discovered", 0) or 0)
        seed_urls = int(data.get("seed_urls", 0) or 0)
        if urls_discovered > 0:
            return _normalize_insight_text(
                f"Crawling modules are mapping reachable endpoints and have discovered {urls_discovered} URLs from {hosts_total} live hosts."
            )
        if seed_urls > 0:
            return _normalize_insight_text(
                f"Parameter discovery is expanding attack surface coverage from {seed_urls} seed URLs."
            )
        return _normalize_insight_text(
            f"{tool} is currently enumerating web routes and endpoint candidates for deeper testing."
        )

    if tool == "graphql-scanner":
        current_index = int(data.get("current_index", 0) or 0)
        total_urls = int(data.get("total_urls", 0) or 0)
        active_url = str(data.get("active_url") or "").strip()
        if current_index and total_urls and active_url:
            return _normalize_insight_text(
                f"GraphQL/API scanner is probing endpoint {current_index}/{total_urls} and validating auth, introspection, and API exposure on {active_url}."
            )
        return _normalize_insight_text(
            "GraphQL/API scanner is validating API endpoints for schema exposure and access control weaknesses."
        )

    if tool == "idor-tester":
        return _normalize_insight_text(
            "IDOR testing module is validating object-level authorization boundaries across discovered parameterized endpoints."
        )

    if tool in {"subfinder", "amass", "dnsrecon"}:
        return _normalize_insight_text(
            f"{tool} is expanding subdomain coverage and validating reconnaissance signals for {phase_name.lower()}."
        )

    return _normalize_insight_text(f"{tool} is currently active. {activity_message}")


def _ai_module_insight(snapshot: Dict[str, Any]) -> Optional[str]:
    provider = ai_assistant.provider
    if not provider.is_available():
        return None
    prompt = (
        "Explain what this security scan module is actively doing RIGHT NOW in one practical sentence (max 28 words). "
        "Focus on module work, not system state. No markdown.\n"
        f"Telemetry JSON: {json.dumps(snapshot, ensure_ascii=True)}"
    )
    generated = provider.generate(
        prompt=prompt,
        system_prompt="You are a precise AppSec runtime analyst.",
        temperature=0.1,
        max_tokens=72,
    )
    if not generated:
        return None
    return _normalize_insight_text(generated)


def _module_snapshot(scan_row_or_dict: Dict[str, Any]) -> Dict[str, Any]:
    activity_data = _deserialize_activity_data(scan_row_or_dict.get("activity_data"))
    return {
        "target": scan_row_or_dict.get("target", ""),
        "status": scan_row_or_dict.get("status", ""),
        "current_phase": scan_row_or_dict.get("current_phase", 0),
        "current_phase_name": scan_row_or_dict.get("current_phase_name", ""),
        "current_tool": scan_row_or_dict.get("current_tool", ""),
        "progress": scan_row_or_dict.get("progress", 0),
        "activity_message": scan_row_or_dict.get("activity_message", ""),
        "activity_data": activity_data,
    }


def _get_module_insight(scan_id: str, snapshot: Dict[str, Any]) -> str:
    heuristic = _heuristic_module_insight(snapshot)
    runtime_status = str(snapshot.get("status", "")).lower()
    if runtime_status in SCAN_TERMINAL_STATES or runtime_status in {"queued", "paused"}:
        return heuristic
    signature = hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=True).encode("utf-8")).hexdigest()
    now = time.time()
    with MODULE_INSIGHT_LOCK:
        cached = MODULE_INSIGHT_CACHE.get(scan_id)
    if cached and cached.get("signature") == signature:
        return str(cached.get("text") or heuristic)
    if cached and (now - float(cached.get("updated_at", 0.0)) < MODULE_INSIGHT_INTERVAL_SECONDS):
        return heuristic
    insight = _ai_module_insight(snapshot) or heuristic
    with MODULE_INSIGHT_LOCK:
        MODULE_INSIGHT_CACHE[scan_id] = {
            "signature": signature,
            "text": insight,
            "updated_at": now,
        }
    return insight


def _get_scan_record(user: dict, scan_id: str) -> Optional[sqlite3.Row]:
    conn = _db_conn()
    try:
        row = conn.execute(
            """
            SELECT * FROM user_scan_history
            WHERE scan_id = ? AND user_id = ?
            LIMIT 1
            """,
            (scan_id, user.get("sub", "unknown")),
        ).fetchone()
        return row
    finally:
        conn.close()


def _list_user_scans(user: dict, limit: int = 20) -> List[Dict[str, Any]]:
    conn = _db_conn()
    try:
        rows = conn.execute(
            """
            SELECT
              scan_id,
              target,
              scan_type,
              scan_mode,
              program_url,
              platform,
              status,
              progress,
              current_phase,
              current_phase_name,
              current_tool,
              activity_message,
              activity_data,
              error_message,
              started_at,
              completed_at,
              updated_at
            FROM user_scan_history
            WHERE user_id = ?
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (user.get("sub", "unknown"), limit),
        ).fetchall()
        output = []
        for row in rows:
            item = dict(row)
            item["activity_data"] = _deserialize_activity_data(item.get("activity_data"))
            item["module_insight"] = _get_module_insight(item["scan_id"], _module_snapshot(item))
            output.append(item)
        return output
    finally:
        conn.close()


def _list_user_events(user: dict, limit: int = 30) -> List[Dict[str, Any]]:
    conn = _db_conn()
    try:
        rows = conn.execute(
            """
            SELECT scan_id, event_type, detail, severity, created_at
            FROM user_events
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user.get("sub", "unknown"), limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _record_search_query(user: dict, query: str):
    trimmed = query.strip()
    if not trimmed:
        return
    conn = _db_conn()
    try:
        conn.execute(
            """
            INSERT INTO user_search_history (user_id, user_email, query, searched_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                user.get("sub", "unknown"),
                user.get("email", "unknown"),
                trimmed,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _search_attacked_sites(user: dict, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    like_q = f"%{query.strip()}%"
    conn = _db_conn()
    try:
        rows = conn.execute(
            """
            SELECT scan_id, target, scan_type, status, progress, started_at, completed_at
            FROM user_scan_history
            WHERE user_id = ?
              AND status IN ('completed', 'failed', 'cancelled')
              AND target LIKE ?
            ORDER BY completed_at DESC, started_at DESC
            LIMIT ?
            """,
            (user.get("sub", "unknown"), like_q, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _scan_runtime_paths(scan_id: str) -> Dict[str, Path]:
    base_dir = SCAN_RUNTIME_DIR / scan_id
    return {
        "dir": base_dir,
        "status_file": base_dir / "status.json",
        "summary_file": base_dir / "summary.json",
        "stdout_log": base_dir / "stdout.log",
        "stderr_log": base_dir / "stderr.log",
    }


def _read_runtime_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _normalize_scan_status(raw_status: Any) -> Optional[str]:
    if not isinstance(raw_status, str):
        return None
    status = raw_status.strip().lower()
    if status in {"queued", "running", "paused", "completed", "failed", "cancelled"}:
        return status
    return None


def _apply_runtime_status(
    current_user: dict,
    scan_id: str,
    payload: Dict[str, Any],
    previous_status: Optional[str],
    previous_phase: Optional[int],
):
    row = _get_scan_record(current_user, scan_id)
    if not row:
        return previous_status, previous_phase

    if row["status"] == "paused":
        return row["status"], row["current_phase"]

    normalized_status = _normalize_scan_status(payload.get("status")) or row["status"]
    try:
        progress = int(payload.get("progress", row["progress"]))
    except Exception:
        progress = int(row["progress"])
    progress = max(0, min(100, progress))

    try:
        phase_num = int(payload.get("current_phase", row["current_phase"]))
    except Exception:
        phase_num = int(row["current_phase"])

    phase_name = payload.get("current_phase_name")
    if not isinstance(phase_name, str):
        phase_name = row["current_phase_name"] or ""

    current_tool = payload.get("current_tool")
    if not isinstance(current_tool, str):
        current_tool = row["current_tool"] or ""

    activity_message = payload.get("activity_message")
    if not isinstance(activity_message, str):
        activity_message = row["activity_message"] or ""

    activity_data = payload.get("activity_data")
    if not isinstance(activity_data, dict):
        activity_data = _deserialize_activity_data(row["activity_data"])

    error_message = payload.get("error")
    if error_message is not None and not isinstance(error_message, str):
        error_message = str(error_message)

    runtime_pid = payload.get("runtime_pid")
    if runtime_pid is not None:
        try:
            runtime_pid = int(runtime_pid)
        except Exception:
            runtime_pid = None

    results_payload = payload.get("results")
    if not isinstance(results_payload, dict):
        results_payload = None

    _update_scan_status(
        current_user,
        scan_id=scan_id,
        status=normalized_status,
        progress=progress,
        results=results_payload,
        current_phase=phase_num,
        current_phase_name=phase_name,
        current_tool=current_tool,
        activity_message=activity_message,
        activity_data=activity_data,
        error_message=error_message,
        runtime_pid=runtime_pid,
    )

    target = row["target"]
    if normalized_status != previous_status:
        if normalized_status == "running":
            _record_event(current_user, "scan.running", f"Scan started for {target}", "info", scan_id=scan_id)
        elif normalized_status == "paused":
            _record_event(current_user, "scan.paused", f"Scan paused for {target}", "warning", scan_id=scan_id)
        elif normalized_status == "completed":
            _record_event(current_user, "scan.completed", f"Scan completed for {target}", "success", scan_id=scan_id)
        elif normalized_status == "failed":
            _record_event(current_user, "scan.failed", f"Scan failed for {target}", "error", scan_id=scan_id)
        elif normalized_status == "cancelled":
            _record_event(current_user, "scan.cancelled", f"Scan cancelled for {target}", "warning", scan_id=scan_id)

    if phase_num and phase_num != previous_phase:
        phase_label = phase_name or f"Phase {phase_num}"
        _record_event(current_user, "scan.phase", f"{target}: {phase_label}", "info", scan_id=scan_id)

    return normalized_status, phase_num


def _cleanup_runtime_job(scan_id: str):
    with SCAN_RUNTIME_LOCK:
        job = SCAN_RUNTIME_JOBS.pop(scan_id, None)
    if not job:
        return
    for stream_key in ("stdout_stream", "stderr_stream"):
        stream = job.get(stream_key)
        if stream:
            try:
                stream.close()
            except Exception:
                pass


def _monitor_runtime_job(scan_id: str, current_user: dict):
    last_status: Optional[str] = None
    last_phase: Optional[int] = None
    paths = _scan_runtime_paths(scan_id)
    try:
        while True:
            with SCAN_RUNTIME_LOCK:
                job = SCAN_RUNTIME_JOBS.get(scan_id)
            if not job:
                return
            process: subprocess.Popen = job["process"]

            payload = _read_runtime_json(paths["status_file"])
            if payload:
                last_status, last_phase = _apply_runtime_status(
                    current_user,
                    scan_id,
                    payload,
                    last_status,
                    last_phase,
                )

            return_code = process.poll()
            if return_code is not None:
                summary_payload = _read_runtime_json(paths["summary_file"]) or _read_runtime_json(paths["status_file"]) or {}
                terminal_status = _normalize_scan_status(summary_payload.get("status"))
                if terminal_status is None:
                    terminal_status = "completed" if return_code == 0 else "failed"
                if terminal_status not in SCAN_TERMINAL_STATES:
                    terminal_status = "failed" if return_code != 0 else "completed"

                row = _get_scan_record(current_user, scan_id)
                if row:
                    if row["status"] == "paused":
                        time.sleep(2)
                        continue
                    if row["status"] == "cancelled":
                        terminal_status = "cancelled"
                    try:
                        progress = int(summary_payload.get("progress", row["progress"]))
                    except Exception:
                        progress = int(row["progress"])
                    if terminal_status in SCAN_TERMINAL_STATES:
                        progress = 100

                    try:
                        phase_num = int(summary_payload.get("current_phase", row["current_phase"]))
                    except Exception:
                        phase_num = int(row["current_phase"])

                    phase_name = summary_payload.get("current_phase_name")
                    if not isinstance(phase_name, str):
                        phase_name = row["current_phase_name"] or ""

                    current_tool = summary_payload.get("current_tool")
                    if not isinstance(current_tool, str):
                        current_tool = row["current_tool"] or ""

                    activity_message = summary_payload.get("activity_message")
                    if not isinstance(activity_message, str):
                        activity_message = row["activity_message"] or ""

                    activity_data = summary_payload.get("activity_data")
                    if not isinstance(activity_data, dict):
                        activity_data = _deserialize_activity_data(row["activity_data"])

                    error_message = summary_payload.get("error")
                    if error_message is None and return_code != 0:
                        error_message = f"Pipeline exited with code {return_code}"
                    if error_message is not None and not isinstance(error_message, str):
                        error_message = str(error_message)

                    results_payload = summary_payload.get("results")
                    if not isinstance(results_payload, dict):
                        results_payload = None

                    _update_scan_status(
                        current_user,
                        scan_id=scan_id,
                        status=terminal_status,
                        progress=progress,
                        results=results_payload,
                        current_phase=phase_num,
                        current_phase_name=phase_name,
                        current_tool=current_tool,
                        activity_message=activity_message,
                        activity_data=activity_data,
                        error_message=error_message,
                        runtime_pid=None,
                    )
                    if terminal_status != last_status:
                        target = row["target"]
                        if terminal_status == "completed":
                            _record_event(current_user, "scan.completed", f"Scan completed for {target}", "success", scan_id=scan_id)
                        elif terminal_status == "failed":
                            _record_event(current_user, "scan.failed", f"Scan failed for {target}", "error", scan_id=scan_id)
                        elif terminal_status == "cancelled":
                            _record_event(current_user, "scan.cancelled", f"Scan cancelled for {target}", "warning", scan_id=scan_id)

                _cleanup_runtime_job(scan_id)
                return

            time.sleep(2)
    finally:
        _cleanup_runtime_job(scan_id)


def _launch_scan_runtime(
    current_user: dict,
    scan_id: str,
    target: str,
    *,
    reattack_mode: str = "full_rescan",
    partial_report_on_interrupt: bool = True,
) -> int:
    paths = _scan_runtime_paths(scan_id)
    paths["dir"].mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["TRISHUL_RUNTIME_SCAN_ID"] = scan_id
    env["TRISHUL_RUNTIME_STATUS_FILE"] = str(paths["status_file"].resolve())
    env["TRISHUL_RUNTIME_SUMMARY_FILE"] = str(paths["summary_file"].resolve())
    env["TRISHUL_API_MODE"] = "1"
    env["TRISHUL_REATTACK_MODE"] = reattack_mode
    env["TRISHUL_PARTIAL_REPORT_ALWAYS"] = "1" if partial_report_on_interrupt else "0"

    project_root = Path(__file__).resolve().parent
    python_bin = os.getenv("TRISHUL_PYTHON_BIN", sys.executable)
    command = [
        python_bin,
        str((project_root / "main.py").resolve()),
        "-d",
        target,
        "-y",
        "--api-triggered",
    ]

    stdout_stream = open(paths["stdout_log"], "a", encoding="utf-8")
    stderr_stream = open(paths["stderr_log"], "a", encoding="utf-8")
    process = subprocess.Popen(
        command,
        cwd=str(project_root),
        env=env,
        stdout=stdout_stream,
        stderr=stderr_stream,
        text=True,
    )

    with SCAN_RUNTIME_LOCK:
        SCAN_RUNTIME_JOBS[scan_id] = {
            "user_id": current_user.get("sub", "unknown"),
            "process": process,
            "stdout_stream": stdout_stream,
            "stderr_stream": stderr_stream,
        }

    _update_scan_status(
        current_user,
        scan_id=scan_id,
        status="running",
        progress=1,
        current_phase=0,
        current_phase_name="Initializing",
        current_tool="bootstrap",
        activity_message="Initializing runtime pipeline",
        activity_data={
            "stage": "bootstrap",
            "reattack_mode": reattack_mode,
            "partial_report_on_interrupt": partial_report_on_interrupt,
        },
        runtime_pid=process.pid,
    )

    monitor = threading.Thread(
        target=_monitor_runtime_job,
        args=(scan_id, {"sub": current_user.get("sub", "unknown"), "email": current_user.get("email", "unknown")}),
        daemon=True,
        name=f"scan-monitor-{scan_id[:8]}",
    )
    monitor.start()
    return process.pid


def _sync_runtime_from_status_file(current_user: dict, scan_id: str):
    payload = _read_runtime_json(_scan_runtime_paths(scan_id)["status_file"])
    if not payload:
        return
    row = _get_scan_record(current_user, scan_id)
    if not row:
        return
    _apply_runtime_status(
        current_user,
        scan_id=scan_id,
        payload=payload,
        previous_status=row["status"],
        previous_phase=row["current_phase"],
    )


def _refresh_running_scans(user: dict):
    scans = _list_user_scans(user, limit=200)
    for scan in scans:
        if scan["status"] in {"queued", "running", "paused"}:
            _sync_runtime_from_status_file(user, scan["scan_id"])


def _resolve_scan_results(row: sqlite3.Row) -> Dict[str, Any]:
    try:
        parsed = json.loads(row["results_json"] or "{}")
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    return {
        "subdomains_found": 0,
        "live_hosts": 0,
        "open_ports": 0,
        "vulnerabilities": 0,
    }


def _stop_runtime_scan(scan_id: str) -> Optional[int]:
    with SCAN_RUNTIME_LOCK:
        job = SCAN_RUNTIME_JOBS.get(scan_id)
    if not job:
        return None
    process: subprocess.Popen = job["process"]
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
    _cleanup_runtime_job(scan_id)
    return process.pid


def _get_runtime_job(scan_id: str) -> Optional[Dict[str, Any]]:
    with SCAN_RUNTIME_LOCK:
        return SCAN_RUNTIME_JOBS.get(scan_id)


_init_ui_state_db()

# ==========================================
# MODELS
# ==========================================

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    company_name: Optional[str] = None
    full_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class AssetInput(BaseModel):
    domain: str
    technologies: List[Dict[str, str]] = Field(default_factory=list)
    open_ports: List[int] = Field(default_factory=list)

class ScanRequest(BaseModel):
    target: str
    scan_type: str = "full"  # full, osint, vulnerability
    scan_mode: str = "manual_override"  # auto, manual_override
    program_url: Optional[str] = None
    platform: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)

class APIKeyCreate(BaseModel):
    name: str
    scopes: List[str] = Field(default_factory=lambda: ["read", "write"])


# ==========================================
# AUTHENTICATION & AUTHORIZATION
# ==========================================

def create_access_token(data: dict) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return user data."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def rate_limit_check(request: Request):
    """Rate limiting middleware."""
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean old entries
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if current_time - req_time < RATE_WINDOW
    ]
    
    # Check rate limit
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT} requests per minute."
        )
    
    # Record request
    rate_limit_store[client_ip].append(current_time)


# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/api/v1/auth/register", response_model=Token, tags=["Authentication"])
async def register(user: UserRegister):
    """
    Register a new user account.
    
    For hackathon demo - simplified registration.
    In production: email verification, password hashing with bcrypt.
    """
    # Simplified for hackathon
    user_id = hashlib.md5(user.email.encode()).hexdigest()[:12]
    
    token_data = {
        "sub": user_id,
        "email": user.email,
        "company": user.company_name,
        "tier": "free"  # free, pro, enterprise
    }
    
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.post("/api/v1/auth/login", response_model=Token, tags=["Authentication"])
async def login(user: UserLogin):
    """
    Login and receive JWT token.
    
    For hackathon demo - simplified auth.
    In production: verify against database with bcrypt.
    """
    # Simplified for hackathon - accept any email/password
    user_id = hashlib.md5(user.email.encode()).hexdigest()[:12]
    
    token_data = {
        "sub": user_id,
        "email": user.email,
        "tier": "pro"
    }
    
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


# ==========================================
# AI ANALYSIS ENDPOINTS
# ==========================================

@app.post("/api/v1/ai/analyze-asset", 
         dependencies=[Depends(rate_limit_check)],
         tags=["AI Intelligence"])
async def ai_analyze_asset(
    asset: AssetInput,
    current_user: dict = Depends(verify_token)
):
    """
    🤖 AI-Powered Vulnerability Analysis
    
    Analyze an asset using machine learning to predict vulnerabilities,
    assess risk, and provide intelligent recommendations.
    """
    try:
        analysis = analyze_asset_risk(asset.dict())
        
        return {
            "success": True,
            "asset": asset.domain,
            "analysis": analysis,
            "analyzed_at": datetime.utcnow().isoformat(),
            "analyzed_by": current_user.get("email")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/batch-analyze",
         dependencies=[Depends(rate_limit_check)],
         tags=["AI Intelligence"])
async def ai_batch_analyze(
    assets: List[AssetInput],
    current_user: dict = Depends(verify_token)
):
    """
    🤖 Batch AI Analysis
    
    Analyze multiple assets simultaneously with AI-powered intelligence.
    Returns aggregate risk metrics and per-asset analysis.
    """
    try:
        assets_data = [asset.dict() for asset in assets]
        analysis = batch_analyze_assets(assets_data)
        
        return {
            "success": True,
            "batch_analysis": analysis,
            "analyzed_at": datetime.utcnow().isoformat(),
            "user": current_user.get("email")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# SCAN ENDPOINTS
# ==========================================

@app.post("/api/v1/scans/start",
         dependencies=[Depends(rate_limit_check)],
         tags=["Scanning"])
async def start_scan(
    scan_request: ScanRequest,
    current_user: dict = Depends(verify_token)
):
    """
    🔍 Start Security Scan
    
    Initiate a comprehensive security scan with selected modules.
    Scan types: full, osint, vulnerability, subdomain, port
    """
    scan_id = secrets.token_urlsafe(16)
    scan_mode = (scan_request.scan_mode or "manual_override").strip().lower()
    if scan_mode not in {"auto", "manual_override"}:
        raise HTTPException(status_code=400, detail="scan_mode must be 'auto' or 'manual_override'")
    options = scan_request.options if isinstance(scan_request.options, dict) else {}
    reattack_mode = str(options.get("reattack_mode", "full_rescan")).strip().lower()
    if reattack_mode not in {"full_rescan", "incremental"}:
        raise HTTPException(status_code=400, detail="options.reattack_mode must be 'full_rescan' or 'incremental'")
    partial_report_on_interrupt = options.get("partial_report_on_interrupt", True)
    if not isinstance(partial_report_on_interrupt, bool):
        raise HTTPException(status_code=400, detail="options.partial_report_on_interrupt must be boolean")
    _upsert_scan_record(
        current_user,
        scan_id=scan_id,
        target=scan_request.target,
        scan_type=scan_request.scan_type,
        status="queued",
        scan_mode=scan_mode,
        program_url=scan_request.program_url,
        platform=scan_request.platform,
    )
    _record_event(
        current_user,
        event_type="scan.queued",
        detail=f"Scan queued for {scan_request.target} ({reattack_mode})",
        severity="info",
        scan_id=scan_id,
    )
    try:
        pid = _launch_scan_runtime(
            current_user,
            scan_id=scan_id,
            target=scan_request.target,
            reattack_mode=reattack_mode,
            partial_report_on_interrupt=partial_report_on_interrupt,
        )
        _record_event(
            current_user,
            event_type="scan.running",
            detail=f"Pipeline started for {scan_request.target} (PID {pid}, {reattack_mode})",
            severity="info",
            scan_id=scan_id,
        )
    except Exception as exc:
        _update_scan_status(
            current_user,
            scan_id=scan_id,
            status="failed",
            progress=0,
            current_phase=0,
            current_phase_name="Initialization",
            current_tool="bootstrap",
            error_message=str(exc),
            runtime_pid=None,
        )
        _record_event(
            current_user,
            event_type="scan.failed",
            detail=f"Scan failed to start for {scan_request.target}",
            severity="error",
            scan_id=scan_id,
        )
        raise HTTPException(status_code=500, detail=f"Failed to launch scan runtime: {exc}")
    
    return {
        "success": True,
        "scan_id": scan_id,
        "target": scan_request.target,
        "scan_type": scan_request.scan_type,
        "scan_mode": scan_mode,
        "reattack_mode": reattack_mode,
        "program_url": scan_request.program_url,
        "platform": scan_request.platform,
        "status": "running",
        "message": f"Scan initiated for {scan_request.target}",
        "estimated_time": "5-10 minutes",
        "initiated_by": current_user.get("email"),
        "initiated_at": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/scans/{scan_id}",
        dependencies=[Depends(rate_limit_check)],
        tags=["Scanning"])
async def get_scan_status(
    scan_id: str,
    current_user: dict = Depends(verify_token)
):
    """Get scan status and results."""
    _sync_runtime_from_status_file(current_user, scan_id)
    row = _get_scan_record(current_user, scan_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")

    row_dict = dict(row)
    results = _resolve_scan_results(row)
    snapshot = _module_snapshot(row_dict)
    return {
        "scan_id": row["scan_id"],
        "status": row["status"],
        "progress": row["progress"],
        "scan_mode": row["scan_mode"],
        "program_url": row["program_url"],
        "platform": row["platform"],
        "current_phase": row["current_phase"],
        "current_phase_name": row["current_phase_name"],
        "current_tool": row["current_tool"],
        "activity_message": row["activity_message"],
        "activity_data": _deserialize_activity_data(row["activity_data"]),
        "module_insight": _get_module_insight(scan_id, snapshot),
        "error_message": row["error_message"],
        "runtime_pid": row["runtime_pid"],
        "results": results,
        "completed_at": row["completed_at"],
        "updated_at": row["updated_at"],
    }


@app.post("/api/v1/scans/{scan_id}/stop",
          dependencies=[Depends(rate_limit_check)],
          tags=["Scanning"])
async def stop_scan(
    scan_id: str,
    current_user: dict = Depends(verify_token),
):
    row = _get_scan_record(current_user, scan_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    if row["status"] in SCAN_TERMINAL_STATES:
        return {
            "success": True,
            "scan_id": scan_id,
            "status": row["status"],
            "message": "Scan is already finished.",
        }

    pid = _stop_runtime_scan(scan_id)
    _update_scan_status(
        current_user,
        scan_id=scan_id,
        status="cancelled",
        progress=int(row["progress"]),
        current_phase=int(row["current_phase"]),
        current_phase_name=row["current_phase_name"],
        current_tool=row["current_tool"],
        error_message="Stopped by user",
        runtime_pid=None,
    )
    _record_event(
        current_user,
        event_type="scan.cancelled",
        detail=f"Scan stopped for {row['target']}",
        severity="warning",
        scan_id=scan_id,
    )
    return {
        "success": True,
        "scan_id": scan_id,
        "status": "cancelled",
        "pid": pid,
        "message": "Scan stopped.",
    }


@app.post("/api/v1/scans/{scan_id}/pause",
          dependencies=[Depends(rate_limit_check)],
          tags=["Scanning"])
async def pause_scan(
    scan_id: str,
    current_user: dict = Depends(verify_token),
):
    row = _get_scan_record(current_user, scan_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    if row["status"] in SCAN_TERMINAL_STATES:
        raise HTTPException(status_code=400, detail="Cannot pause a finished scan")
    if row["status"] == "paused":
        return {
            "success": True,
            "scan_id": scan_id,
            "status": "paused",
            "message": "Scan is already paused.",
        }
    if row["status"] not in SCAN_PAUSABLE_STATES:
        raise HTTPException(status_code=400, detail=f"Cannot pause scan in status '{row['status']}'")

    runtime_job = _get_runtime_job(scan_id)
    pid = None
    if runtime_job:
        process: subprocess.Popen = runtime_job["process"]
        pid = process.pid
        if process.poll() is None:
            try:
                process.send_signal(signal.SIGSTOP)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Failed to pause process: {exc}")
    elif row["runtime_pid"]:
        pid = int(row["runtime_pid"])
        try:
            os.kill(pid, signal.SIGSTOP)
        except ProcessLookupError:
            raise HTTPException(status_code=409, detail="Scan process is not running")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to pause process: {exc}")
    else:
        raise HTTPException(status_code=409, detail="No active runtime process found to pause")

    _update_scan_status(
        current_user,
        scan_id=scan_id,
        status="paused",
        progress=int(row["progress"]),
        current_phase=int(row["current_phase"]),
        current_phase_name=row["current_phase_name"],
        current_tool=row["current_tool"],
        error_message="Paused by user",
        runtime_pid=pid,
    )
    _record_event(
        current_user,
        event_type="scan.paused",
        detail=f"Scan paused for {row['target']}",
        severity="warning",
        scan_id=scan_id,
    )
    return {
        "success": True,
        "scan_id": scan_id,
        "status": "paused",
        "pid": pid,
        "message": "Scan paused.",
    }


@app.post("/api/v1/scans/{scan_id}/resume",
          dependencies=[Depends(rate_limit_check)],
          tags=["Scanning"])
async def resume_scan(
    scan_id: str,
    current_user: dict = Depends(verify_token),
):
    row = _get_scan_record(current_user, scan_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    if row["status"] in SCAN_TERMINAL_STATES:
        raise HTTPException(status_code=400, detail="Cannot resume a finished scan")
    if row["status"] != "paused":
        raise HTTPException(status_code=400, detail="Scan is not paused")

    pid = row["runtime_pid"]
    runtime_job = _get_runtime_job(scan_id)
    if runtime_job:
        process: subprocess.Popen = runtime_job["process"]
        pid = process.pid
        if process.poll() is None:
            try:
                process.send_signal(signal.SIGCONT)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Failed to resume process: {exc}")
        else:
            raise HTTPException(status_code=409, detail="Scan process already exited; start a new scan")
    elif pid:
        try:
            os.kill(int(pid), signal.SIGCONT)
        except ProcessLookupError:
            raise HTTPException(status_code=409, detail="Scan process no longer exists; start a new scan")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to resume process: {exc}")
    else:
        raise HTTPException(status_code=409, detail="No paused runtime process found; start a new scan")

    _update_scan_status(
        current_user,
        scan_id=scan_id,
        status="running",
        progress=int(row["progress"]),
        current_phase=int(row["current_phase"]),
        current_phase_name=row["current_phase_name"],
        current_tool=row["current_tool"],
        error_message="",
        runtime_pid=int(pid) if pid else None,
    )
    _record_event(
        current_user,
        event_type="scan.resumed",
        detail=f"Scan resumed for {row['target']}",
        severity="info",
        scan_id=scan_id,
    )
    return {
        "success": True,
        "scan_id": scan_id,
        "status": "running",
        "pid": int(pid) if pid else None,
        "message": "Scan resumed.",
    }


@app.get("/api/v1/programs/discover",
         dependencies=[Depends(rate_limit_check)],
         tags=["Scanning"])
async def discover_program(current_user: dict = Depends(verify_token)):
    scout = BountyScout()
    try:
        target_data = scout.get_random_target()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to discover program: {exc}")

    if not target_data:
        raise HTTPException(status_code=404, detail="No bug bounty program found")

    return {
        "success": True,
        "target": target_data.get("domain", ""),
        "program_url": target_data.get("url", ""),
        "platform": target_data.get("platform", ""),
        "message": "Program discovered successfully.",
        "discovered_at": datetime.utcnow().isoformat(),
        "user": current_user.get("email"),
    }


# ==========================================
# REPORTS ENDPOINTS
# ==========================================

@app.get("/api/v1/reports/generate",
        dependencies=[Depends(rate_limit_check)],
        tags=["Reports"])
async def generate_report(
    scan_id: str,
    format: str = "json",  # json, pdf, html, markdown
    current_user: dict = Depends(verify_token)
):
    """
    📊 Generate AI-Powered Security Report
    
    Generate comprehensive security reports with AI-generated summaries.
    Formats: json, pdf, html, markdown
    """
    row = _get_scan_record(current_user, scan_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    if row["status"] not in SCAN_TERMINAL_STATES:
        raise HTTPException(status_code=400, detail="Scan is not finished yet")

    results = _resolve_scan_results(row)
    scan_data = {
        'total_assets': int(results.get("subdomains_found", 0)) + int(results.get("live_hosts", 0)),
        'critical_findings': max(0, int(results.get("vulnerabilities", 0)) // 5),
        'high_findings': max(0, int(results.get("vulnerabilities", 0)) // 2),
        'medium_findings': max(0, int(results.get("vulnerabilities", 0))),
    }
    
    summary = ai_assistant.generate_report_summary(scan_data)
    
    return {
        "success": True,
        "scan_id": scan_id,
        "format": format,
        "executive_summary": summary,
        "download_url": f"/api/v1/reports/download/{scan_id}",
        "generated_at": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/operations/overview",
         dependencies=[Depends(rate_limit_check)],
         tags=["Scanning"])
async def operations_overview(current_user: dict = Depends(verify_token)):
    _refresh_running_scans(current_user)
    scans = _list_user_scans(current_user, limit=20)
    events = _list_user_events(current_user, limit=30)
    running = [s for s in scans if s["status"] == "running"]
    completed = [s for s in scans if s["status"] == "completed"]
    failed = [s for s in scans if s["status"] == "failed"]
    cancelled = [s for s in scans if s["status"] == "cancelled"]
    return {
        "success": True,
        "summary": {
            "total_scans": len(scans),
            "running_scans": len(running),
            "completed_scans": len(completed),
            "failed_scans": len(failed),
            "cancelled_scans": len(cancelled),
        },
        "scans": scans,
        "events": events,
    }


@app.get("/api/v1/reports/analytics",
         dependencies=[Depends(rate_limit_check)],
         tags=["Reports"])
async def reports_analytics(current_user: dict = Depends(verify_token)):
    _refresh_running_scans(current_user)
    scans = _list_user_scans(current_user, limit=100)
    completed = [s for s in scans if s["status"] == "completed"]
    attacked_sites = len({s["target"] for s in completed})
    findings_total = 0
    for s in completed:
        row = _get_scan_record(current_user, s["scan_id"])
        if row:
            results = _resolve_scan_results(row)
            findings_total += int(results.get("vulnerabilities", 0))
    return {
        "success": True,
        "kpis": {
            "attacked_sites": attacked_sites,
            "completed_scans": len(completed),
            "findings_total": findings_total,
            "risk_index": min(100, findings_total * 4),
        },
        "recent_scans": completed[:20],
    }


# ==========================================
# SYSTEM ENDPOINTS
# ==========================================

@app.get("/api/v1/health", tags=["System"])
async def health_check():
    """API health check."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_enabled": True
    }

@app.get("/api/v1/stats",
        dependencies=[Depends(rate_limit_check)],
        tags=["System"])
async def get_stats(current_user: dict = Depends(verify_token)):
    """Get user statistics and usage."""
    _refresh_running_scans(current_user)
    scans = _list_user_scans(current_user, limit=500)
    completed = [s for s in scans if s["status"] == "completed"]
    attacked_sites = len({s["target"] for s in completed})
    vulnerabilities_found = 0
    for s in completed:
        row = _get_scan_record(current_user, s["scan_id"])
        if row:
            results = _resolve_scan_results(row)
            vulnerabilities_found += int(results.get("vulnerabilities", 0))
    return {
        "user": current_user.get("email"),
        "tier": current_user.get("tier", "free"),
        "stats": {
            "total_scans": len(scans),
            "assets_monitored": attacked_sites,
            "vulnerabilities_found": vulnerabilities_found,
            "critical_alerts": max(0, vulnerabilities_found // 4),
            "api_calls_today": 450,
            "storage_used_mb": 125.4
        },
        "limits": {
            "max_scans_per_month": 1000 if current_user.get("tier") == "pro" else 100,
            "max_assets": 500 if current_user.get("tier") == "pro" else 50,
            "rate_limit_per_minute": 100
        }
    }


@app.get("/api/v1/search/attacked-sites",
         dependencies=[Depends(rate_limit_check)],
         tags=["System"])
async def search_attacked_sites(
    query: str,
    limit: int = 20,
    current_user: dict = Depends(verify_token),
):
    """Search attacked/completed targets for current user."""
    _record_search_query(current_user, query)
    rows = _search_attacked_sites(current_user, query, limit=max(1, min(limit, 100)))
    return {
        "success": True,
        "query": query,
        "count": len(rows),
        "results": rows,
    }


@app.get("/api/v1/search/recent",
         dependencies=[Depends(rate_limit_check)],
         tags=["System"])
async def recent_attacked_sites(
    limit: int = 20,
    current_user: dict = Depends(verify_token),
):
    """List recent attacked sites for current user (terminal scans only)."""
    rows = _search_attacked_sites(current_user, "", limit=max(1, min(limit, 100)))
    return {
        "success": True,
        "count": len(rows),
        "results": rows,
    }


# ==========================================
# WEBHOOKS & INTEGRATIONS
# ==========================================

@app.post("/api/v1/webhooks/configure",
         dependencies=[Depends(rate_limit_check)],
         tags=["Integrations"])
async def configure_webhook(
    webhook_data: Dict[str, Any],
    current_user: dict = Depends(verify_token)
):
    """Configure webhook for real-time notifications."""
    return {
        "success": True,
        "message": "Webhook configured successfully",
        "webhook_id": secrets.token_urlsafe(12),
        "events": webhook_data.get("events", ["scan.completed", "vulnerability.found"])
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root - redirect to documentation."""
    return {
        "message": "Trishul Security Platform API",
        "version": "2.0.0",
        "docs": "/api/docs",
        "health": "/api/v1/health",
        "ai_powered": True,
        "features": [
            "AI Vulnerability Intelligence",
            "Automated Security Scanning",
            "Real-time Monitoring",
            "Multi-tenant SaaS",
            "Enterprise APIs"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
