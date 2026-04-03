from ai_engine import analyze_asset_risk, batch_analyze_assets, AISecurityAssistant


def test_analyze_asset_risk_returns_expected_shape():
    asset = {
        "domain": "example.com",
        "technologies": [{"name": "nginx", "version": "1.18.0"}],
        "open_ports": [80, 443, 22],
    }
    result = analyze_asset_risk(asset)

    expected_keys = {
        "vulnerability_score",
        "risk_level",
        "exploit_likelihood",
        "color",
        "cves_found",
        "reasons",
        "recommendations",
        "ai_analysis",
    }
    assert expected_keys.issubset(result.keys())
    assert 0 <= result["vulnerability_score"] <= 100
    assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_batch_analyze_assets_aggregates_results():
    assets = [
        {"domain": "a.example", "technologies": [], "open_ports": [80]},
        {"domain": "b.example", "technologies": [], "open_ports": [22, 3306]},
    ]
    result = batch_analyze_assets(assets)

    assert result["total_assets"] == 2
    assert "average_risk_score" in result
    assert "detailed_results" in result
    assert len(result["detailed_results"]) == 2


def test_ai_assistant_fallback_summary_when_local_model_offline():
    assistant = AISecurityAssistant()
    assistant.use_local_ai = False

    summary = assistant.generate_report_summary(
        {"total_assets": 5, "critical_findings": 1, "high_findings": 2, "medium_findings": 3}
    )
    assert "Executive Summary" in summary
