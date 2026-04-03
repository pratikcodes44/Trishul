"""
Trishul Campaign Manager - Multi-Target Bug Bounty Orchestration
================================================================
AI-powered campaign management for multiple bug bounty programs
with intelligent prioritization and resource allocation.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import os


class CampaignStatus(Enum):
    """Campaign status enum."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProgramPlatform(Enum):
    """Bug bounty platforms."""
    HACKERONE = "hackerone"
    BUGCROWD = "bugcrowd"
    INTIGRITI = "intigriti"
    YESWEHACK = "yeswehack"
    SYNACK = "synack"
    CUSTOM = "custom"


@dataclass
class Campaign:
    """Bug bounty campaign data model."""
    id: str
    name: str
    platform: str
    target_domain: str
    status: str
    priority: int  # 1-5, 5 being highest
    scope: List[str]
    out_of_scope: List[str]
    created_at: str
    last_scan: Optional[str] = None
    total_assets: int = 0
    vulnerabilities_found: int = 0
    critical_count: int = 0
    high_count: int = 0
    bounty_earned: float = 0.0
    ai_priority_score: float = 0.0
    notes: str = ""
    

class CampaignManager:
    """Manage multiple bug bounty campaigns with AI prioritization."""
    
    def __init__(self, db_path: str = "campaigns.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for campaigns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                platform TEXT NOT NULL,
                target_domain TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 3,
                scope TEXT,  -- JSON array
                out_of_scope TEXT,  -- JSON array
                created_at TEXT NOT NULL,
                last_scan TEXT,
                total_assets INTEGER DEFAULT 0,
                vulnerabilities_found INTEGER DEFAULT 0,
                critical_count INTEGER DEFAULT 0,
                high_count INTEGER DEFAULT 0,
                bounty_earned REAL DEFAULT 0.0,
                ai_priority_score REAL DEFAULT 0.0,
                notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                scan_type TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                results TEXT,  -- JSON
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT NOT NULL,
                finding_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                asset TEXT,
                discovered_at TEXT NOT NULL,
                status TEXT DEFAULT 'new',  -- new, reported, accepted, duplicate
                bounty_amount REAL DEFAULT 0.0,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_campaign(self, campaign: Campaign) -> bool:
        """Create a new campaign."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO campaigns VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                campaign.id,
                campaign.name,
                campaign.platform,
                campaign.target_domain,
                campaign.status,
                campaign.priority,
                json.dumps(campaign.scope),
                json.dumps(campaign.out_of_scope),
                campaign.created_at,
                campaign.last_scan,
                campaign.total_assets,
                campaign.vulnerabilities_found,
                campaign.critical_count,
                campaign.high_count,
                campaign.bounty_earned,
                campaign.ai_priority_score,
                campaign.notes
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating campaign: {e}")
            return False
    
    def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get campaign by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Campaign(
            id=row[0],
            name=row[1],
            platform=row[2],
            target_domain=row[3],
            status=row[4],
            priority=row[5],
            scope=json.loads(row[6]) if row[6] else [],
            out_of_scope=json.loads(row[7]) if row[7] else [],
            created_at=row[8],
            last_scan=row[9],
            total_assets=row[10],
            vulnerabilities_found=row[11],
            critical_count=row[12],
            high_count=row[13],
            bounty_earned=row[14],
            ai_priority_score=row[15],
            notes=row[16] or ""
        )
    
    def list_campaigns(self, status: Optional[str] = None) -> List[Campaign]:
        """List all campaigns, optionally filtered by status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM campaigns WHERE status = ? ORDER BY ai_priority_score DESC", (status,))
        else:
            cursor.execute("SELECT * FROM campaigns ORDER BY ai_priority_score DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        campaigns = []
        for row in rows:
            campaigns.append(Campaign(
                id=row[0],
                name=row[1],
                platform=row[2],
                target_domain=row[3],
                status=row[4],
                priority=row[5],
                scope=json.loads(row[6]) if row[6] else [],
                out_of_scope=json.loads(row[7]) if row[7] else [],
                created_at=row[8],
                last_scan=row[9],
                total_assets=row[10],
                vulnerabilities_found=row[11],
                critical_count=row[12],
                high_count=row[13],
                bounty_earned=row[14],
                ai_priority_score=row[15],
                notes=row[16] or ""
            ))
        
        return campaigns
    
    def update_campaign(self, campaign: Campaign) -> bool:
        """Update existing campaign."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE campaigns SET
                    name = ?, platform = ?, target_domain = ?, status = ?,
                    priority = ?, scope = ?, out_of_scope = ?, last_scan = ?,
                    total_assets = ?, vulnerabilities_found = ?,
                    critical_count = ?, high_count = ?, bounty_earned = ?,
                    ai_priority_score = ?, notes = ?
                WHERE id = ?
            """, (
                campaign.name, campaign.platform, campaign.target_domain,
                campaign.status, campaign.priority, json.dumps(campaign.scope),
                json.dumps(campaign.out_of_scope), campaign.last_scan,
                campaign.total_assets, campaign.vulnerabilities_found,
                campaign.critical_count, campaign.high_count, campaign.bounty_earned,
                campaign.ai_priority_score, campaign.notes, campaign.id
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating campaign: {e}")
            return False
    
    def calculate_ai_priority(self, campaign: Campaign) -> float:
        """
        AI-powered priority calculation based on multiple factors.
        Returns score 0-100.
        """
        score = 0.0
        
        # Base priority (1-5) contributes 20 points max
        score += (campaign.priority / 5.0) * 20
        
        # Recent activity bonus
        if campaign.last_scan:
            days_since_scan = (datetime.now() - datetime.fromisoformat(campaign.last_scan)).days
            if days_since_scan > 7:
                score += 15  # Needs attention
            elif days_since_scan > 14:
                score += 25  # Urgent attention
        else:
            score += 30  # Never scanned - high priority
        
        # Vulnerability density
        if campaign.total_assets > 0:
            vuln_rate = campaign.vulnerabilities_found / campaign.total_assets
            score += min(vuln_rate * 100, 25)  # Max 25 points
        
        # Critical findings weight heavily
        score += campaign.critical_count * 5  # Each critical adds 5 points
        score += campaign.high_count * 2      # Each high adds 2 points
        
        # ROI factor - higher bounty = higher priority
        if campaign.bounty_earned > 1000:
            score += 20
        elif campaign.bounty_earned > 500:
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def update_all_priorities(self):
        """Recalculate AI priority scores for all active campaigns."""
        campaigns = self.list_campaigns(status=CampaignStatus.ACTIVE.value)
        
        for campaign in campaigns:
            campaign.ai_priority_score = self.calculate_ai_priority(campaign)
            self.update_campaign(campaign)
    
    def add_finding(self, campaign_id: str, finding: Dict[str, Any]) -> bool:
        """Add a vulnerability finding to a campaign."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO campaign_findings (
                    campaign_id, finding_type, severity, title, 
                    description, asset, discovered_at, status, bounty_amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                campaign_id,
                finding.get('type', 'unknown'),
                finding.get('severity', 'info'),
                finding.get('title', 'Untitled Finding'),
                finding.get('description', ''),
                finding.get('asset', ''),
                datetime.now().isoformat(),
                'new',
                finding.get('bounty', 0.0)
            ))
            
            # Update campaign stats
            cursor.execute("""
                UPDATE campaigns 
                SET vulnerabilities_found = vulnerabilities_found + 1,
                    critical_count = critical_count + CASE WHEN ? = 'critical' THEN 1 ELSE 0 END,
                    high_count = high_count + CASE WHEN ? = 'high' THEN 1 ELSE 0 END
                WHERE id = ?
            """, (finding.get('severity'), finding.get('severity'), campaign_id))
            
            conn.commit()
            conn.close()
            
            # Recalculate priority
            campaign = self.get_campaign(campaign_id)
            if campaign:
                campaign.ai_priority_score = self.calculate_ai_priority(campaign)
                self.update_campaign(campaign)
            
            return True
        except Exception as e:
            print(f"Error adding finding: {e}")
            return False
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics for dashboard."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Campaign counts
        cursor.execute("SELECT COUNT(*) FROM campaigns WHERE status = 'active'")
        active_campaigns = cursor.fetchone()[0]
        
        # Total stats
        cursor.execute("""
            SELECT 
                SUM(total_assets),
                SUM(vulnerabilities_found),
                SUM(critical_count),
                SUM(high_count),
                SUM(bounty_earned)
            FROM campaigns WHERE status = 'active'
        """)
        totals = cursor.fetchone()
        
        # Top campaign
        cursor.execute("""
            SELECT name, ai_priority_score 
            FROM campaigns 
            WHERE status = 'active'
            ORDER BY ai_priority_score DESC 
            LIMIT 1
        """)
        top_campaign = cursor.fetchone()
        
        conn.close()
        
        return {
            'active_campaigns': active_campaigns,
            'total_assets': totals[0] or 0,
            'total_vulnerabilities': totals[1] or 0,
            'critical_vulnerabilities': totals[2] or 0,
            'high_vulnerabilities': totals[3] or 0,
            'total_bounty_earned': totals[4] or 0.0,
            'top_priority_campaign': top_campaign[0] if top_campaign else None,
            'top_priority_score': top_campaign[1] if top_campaign else 0
        }


# Singleton instance
campaign_manager = CampaignManager()


if __name__ == "__main__":
    # Demo usage
    import uuid
    
    # Create sample campaign
    campaign = Campaign(
        id=str(uuid.uuid4()),
        name="Acme Corp Bug Bounty",
        platform=ProgramPlatform.HACKERONE.value,
        target_domain="acme.com",
        status=CampaignStatus.ACTIVE.value,
        priority=4,
        scope=["*.acme.com", "acme.com", "api.acme.com"],
        out_of_scope=["test.acme.com", "dev.acme.com"],
        created_at=datetime.now().isoformat(),
        notes="High-value target, focus on API endpoints"
    )
    
    manager = CampaignManager()
    manager.create_campaign(campaign)
    
    print("Campaign created successfully!")
    print(f"Dashboard stats: {manager.get_dashboard_stats()}")
