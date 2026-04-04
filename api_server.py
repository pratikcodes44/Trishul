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
import jwt
import os
import time
import sqlite3
import json
from collections import defaultdict
import hashlib
import secrets

# Import our AI engine
from ai_engine import analyze_asset_risk, batch_analyze_assets, ai_assistant

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
SCAN_TERMINAL_STATES = {"completed", "failed"}


def _db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(UI_STATE_DB)
    conn.row_factory = sqlite3.Row
    return conn


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
                status TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                started_at TEXT NOT NULL,
                completed_at TEXT,
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


def _upsert_scan_record(user: dict, scan_id: str, target: str, scan_type: str, status: str):
    conn = _db_conn()
    try:
        now = datetime.utcnow().isoformat()
        conn.execute(
            """
            INSERT INTO user_scan_history
              (user_id, user_email, scan_id, target, scan_type, status, progress, started_at, completed_at, results_json)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, NULL, '{}')
            ON CONFLICT(scan_id) DO UPDATE SET
                status=excluded.status
            """,
            (
                user.get("sub", "unknown"),
                user.get("email", "unknown"),
                scan_id,
                target,
                scan_type,
                status,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _update_scan_status(user: dict, scan_id: str, status: str, progress: int, results: Optional[Dict[str, Any]] = None):
    conn = _db_conn()
    try:
        completed_at = datetime.utcnow().isoformat() if status in SCAN_TERMINAL_STATES else None
        conn.execute(
            """
            UPDATE user_scan_history
            SET status = ?, progress = ?, completed_at = COALESCE(?, completed_at), results_json = ?
            WHERE scan_id = ? AND user_id = ?
            """,
            (
                status,
                progress,
                completed_at,
                json.dumps(results or {}),
                scan_id,
                user.get("sub", "unknown"),
            ),
        )
        conn.commit()
    finally:
        conn.close()


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
            SELECT scan_id, target, scan_type, status, progress, started_at, completed_at
            FROM user_scan_history
            WHERE user_id = ?
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (user.get("sub", "unknown"), limit),
        ).fetchall()
        return [dict(r) for r in rows]
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
              AND status IN ('completed', 'failed')
              AND target LIKE ?
            ORDER BY completed_at DESC, started_at DESC
            LIMIT ?
            """,
            (user.get("sub", "unknown"), like_q, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


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
    _upsert_scan_record(
        current_user,
        scan_id=scan_id,
        target=scan_request.target,
        scan_type=scan_request.scan_type,
        status="queued",
    )
    _record_event(
        current_user,
        event_type="scan.queued",
        detail=f"Scan queued for {scan_request.target}",
        severity="info",
        scan_id=scan_id,
    )
    
    return {
        "success": True,
        "scan_id": scan_id,
        "target": scan_request.target,
        "scan_type": scan_request.scan_type,
        "status": "queued",
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
    row = _get_scan_record(current_user, scan_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")

    status = row["status"]
    progress = row["progress"]
    # Demo progression to simulate lifecycle and ensure attacked-site tracking only on terminal states.
    if status == "queued":
        status = "running"
        progress = 35
        _update_scan_status(current_user, scan_id, status=status, progress=progress)
        _record_event(current_user, "scan.running", f"Scan started for {row['target']}", "info", scan_id=scan_id)
    elif status == "running":
        progress = min(progress + 30, 95)
        if progress >= 95:
            status = "completed"
            progress = 100
            results = {
                "subdomains_found": 47,
                "live_hosts": 32,
                "open_ports": 156,
                "vulnerabilities": 12,
            }
            _update_scan_status(current_user, scan_id, status=status, progress=progress, results=results)
            _record_event(current_user, "scan.completed", f"Scan completed for {row['target']}", "success", scan_id=scan_id)
        else:
            _update_scan_status(current_user, scan_id, status=status, progress=progress)

    row = _get_scan_record(current_user, scan_id)
    results = json.loads(row["results_json"] or "{}")
    return {
        "scan_id": row["scan_id"],
        "status": row["status"],
        "progress": row["progress"],
        "results": results,
        "completed_at": row["completed_at"],
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

    results = json.loads(row["results_json"] or "{}")
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
    scans = _list_user_scans(current_user, limit=20)
    events = _list_user_events(current_user, limit=30)
    running = [s for s in scans if s["status"] == "running"]
    completed = [s for s in scans if s["status"] == "completed"]
    failed = [s for s in scans if s["status"] == "failed"]
    return {
        "success": True,
        "summary": {
            "total_scans": len(scans),
            "running_scans": len(running),
            "completed_scans": len(completed),
            "failed_scans": len(failed),
        },
        "scans": scans,
        "events": events,
    }


@app.get("/api/v1/reports/analytics",
         dependencies=[Depends(rate_limit_check)],
         tags=["Reports"])
async def reports_analytics(current_user: dict = Depends(verify_token)):
    scans = _list_user_scans(current_user, limit=100)
    completed = [s for s in scans if s["status"] == "completed"]
    attacked_sites = len({s["target"] for s in completed})
    findings_total = 0
    for s in completed:
        row = _get_scan_record(current_user, s["scan_id"])
        if row:
            results = json.loads(row["results_json"] or "{}")
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
    scans = _list_user_scans(current_user, limit=500)
    completed = [s for s in scans if s["status"] == "completed"]
    attacked_sites = len({s["target"] for s in completed})
    vulnerabilities_found = 0
    for s in completed:
        row = _get_scan_record(current_user, s["scan_id"])
        if row:
            results = json.loads(row["results_json"] or "{}")
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
