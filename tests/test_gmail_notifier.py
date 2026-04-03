import os

from gmail_notifier import GmailNotifier


def test_format_time_hh_mm_ss():
    notifier = GmailNotifier()
    assert notifier._format_time(0) == "00:00:00"
    assert notifier._format_time(3661) == "01:01:01"


def test_format_vulnerabilities_empty():
    notifier = GmailNotifier()
    html = notifier._format_vulnerabilities([])
    assert "No vulnerabilities found" in html


def test_notifier_env_driven_enablement(monkeypatch):
    monkeypatch.delenv("EMAIL_USER", raising=False)
    monkeypatch.delenv("EMAIL_PASSWORD", raising=False)
    notifier = GmailNotifier()

    assert isinstance(notifier.enabled, bool)
    assert notifier.smtp_server == os.getenv("SMTP_SERVER", "smtp.gmail.com")
