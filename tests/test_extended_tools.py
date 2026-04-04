import json

from extended_tools import (
    ExternalCommandRunner,
    ParamDiscoveryRunner,
    SupplementalWebScanner,
    findings_to_nuclei_lines,
)


def test_findings_to_nuclei_lines_deduplicates_and_shapes_payload():
    findings = [
        {
            "tool": "sqlmap",
            "name": "SQL injection indicator",
            "severity": "critical",
            "url": "https://api.example.com/item?id=1",
            "description": "SQLMap reported possible SQL injection.",
            "evidence": "parameter id appears injectable",
        },
        {
            "tool": "sqlmap",
            "name": "SQL injection indicator",
            "severity": "critical",
            "url": "https://api.example.com/item?id=1",
            "description": "SQLMap reported possible SQL injection.",
            "evidence": "duplicate finding",
        },
    ]

    lines = findings_to_nuclei_lines(findings)
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["template-id"] == "sqlmap-supplemental"
    assert payload["info"]["severity"] == "critical"
    assert payload["matched-at"] == "https://api.example.com/item?id=1"


def test_filter_web_urls_respects_scope_and_junk_extensions():
    runner = ExternalCommandRunner()
    urls = [
        "https://app.example.com/dashboard",
        "https://cdn.example.com/static/logo.png",
        "https://evil.com/steal",
        "http://api.example.com/v1/users?active=1",
        "not-a-url",
    ]

    filtered = runner._filter_web_urls(urls, "example.com")
    assert "https://app.example.com/dashboard" in filtered
    assert "http://api.example.com/v1/users?active=1" in filtered
    assert "https://cdn.example.com/static/logo.png" not in filtered
    assert "https://evil.com/steal" not in filtered


def test_param_runner_synthesizes_arjun_parameters_into_urls(monkeypatch):
    runner = ParamDiscoveryRunner()
    monkeypatch.setattr(runner, "_binary_available", lambda _bin: True)

    def fake_run(command, timeout=120, input_text=None):
        if command[0] == "paramspider":
            return "https://app.example.com/search?q=test\n"
        if command[0] == "arjun":
            return "Possible parameters: user_id token\n"
        return ""

    monkeypatch.setattr(runner, "_run", fake_run)
    urls = runner.discover_urls("example.com", ["https://app.example.com/profile"], max_urls=1)

    assert any(u.startswith("https://app.example.com/profile?user_id=") for u in urls)
    assert any("search?q=test" in u for u in urls)


def test_supplemental_web_scanner_routes_by_url_type(monkeypatch):
    scanner = SupplementalWebScanner()
    monkeypatch.setattr(scanner, "_binary_available", lambda _bin: True)

    monkeypatch.setattr(
        scanner,
        "_run_nikto",
        lambda urls: [{"tool": "nikto", "name": "Nikto finding", "severity": "medium", "url": urls[0]}] if urls else [],
    )
    monkeypatch.setattr(
        scanner,
        "_run_wpscan",
        lambda urls: [{"tool": "wpscan", "name": "WP finding", "severity": "high", "url": urls[0]}] if urls else [],
    )
    monkeypatch.setattr(
        scanner,
        "_run_sqlmap",
        lambda urls: [{"tool": "sqlmap", "name": "SQLi", "severity": "critical", "url": urls[0]}] if urls else [],
    )
    monkeypatch.setattr(
        scanner,
        "_run_dalfox",
        lambda urls: [{"tool": "dalfox", "name": "XSS", "severity": "high", "url": urls[0]}] if urls else [],
    )

    urls = [
        "https://blog.example.com/wp-admin",
        "https://api.example.com/item?id=1",
        "https://app.example.com/",
    ]
    findings = scanner.scan(urls=urls, target_domain="example.com", fingerprints={"https://blog.example.com/": ["WordPress"]})

    tools = {f["tool"] for f in findings}
    assert {"nikto", "wpscan", "sqlmap", "dalfox"}.issubset(tools)
