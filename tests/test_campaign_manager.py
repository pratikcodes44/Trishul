import uuid
from datetime import datetime

from campaign_manager import CampaignManager, Campaign, CampaignStatus, ProgramPlatform


def _make_campaign(campaign_id: str) -> Campaign:
    return Campaign(
        id=campaign_id,
        name="CI Test Campaign",
        platform=ProgramPlatform.HACKERONE.value,
        target_domain="example.com",
        status=CampaignStatus.ACTIVE.value,
        priority=4,
        scope=["example.com", "*.example.com"],
        out_of_scope=[],
        created_at=datetime.now().isoformat(),
    )


def test_create_and_get_campaign(tmp_path):
    db_file = tmp_path / "campaigns_test.db"
    manager = CampaignManager(db_path=str(db_file))

    campaign_id = str(uuid.uuid4())
    campaign = _make_campaign(campaign_id)

    assert manager.create_campaign(campaign) is True
    fetched = manager.get_campaign(campaign_id)
    assert fetched is not None
    assert fetched.target_domain == "example.com"


def test_add_finding_updates_stats(tmp_path):
    db_file = tmp_path / "campaigns_test.db"
    manager = CampaignManager(db_path=str(db_file))

    campaign_id = str(uuid.uuid4())
    manager.create_campaign(_make_campaign(campaign_id))

    finding = {
        "type": "sql-injection",
        "severity": "critical",
        "title": "SQL Injection",
        "description": "Injection on search endpoint",
        "asset": "https://example.com/search",
        "bounty": 1000.0,
    }

    assert manager.add_finding(campaign_id, finding) is True
    updated = manager.get_campaign(campaign_id)
    assert updated is not None
    assert updated.vulnerabilities_found >= 1
    assert updated.critical_count >= 1
