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
    # For hackathon: return mock data
    # In production: query from database
    return {
        "scan_id": scan_id,
        "status": "completed",
        "progress": 100,
        "results": {
            "subdomains_found": 47,
            "live_hosts": 32,
            "open_ports": 156,
            "vulnerabilities": 12
        },
        "completed_at": datetime.utcnow().isoformat()
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
    scan_data = {
        'total_assets': 45,
        'critical_findings': 3,
        'high_findings': 8,
        'medium_findings': 15
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
    return {
        "user": current_user.get("email"),
        "tier": current_user.get("tier", "free"),
        "stats": {
            "total_scans": 127,
            "assets_monitored": 45,
            "vulnerabilities_found": 234,
            "critical_alerts": 8,
            "api_calls_today": 450,
            "storage_used_mb": 125.4
        },
        "limits": {
            "max_scans_per_month": 1000 if current_user.get("tier") == "pro" else 100,
            "max_assets": 500 if current_user.get("tier") == "pro" else 50,
            "rate_limit_per_minute": 100
        }
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
