"""
Trishul AI Engine - AI-Powered Vulnerability Intelligence
==========================================================
Machine Learning and AI capabilities for vulnerability prediction,
risk assessment, and intelligent security insights.
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)


class LocalLLMProvider:
    """Local LLM provider (Ollama-compatible) for Mistral and other models."""

    def __init__(self):
        self.api_url = os.getenv(
            "LOCAL_AI_API_URL",
            os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434/api/generate"),
        )
        self.model = os.getenv(
            "LOCAL_AI_MODEL",
            os.getenv("OLLAMA_MODEL", "mistral:latest"),
        )
        self.timeout = int(os.getenv("LOCAL_AI_TIMEOUT", "20"))
        self._availability_cached: Optional[bool] = None

    def _tags_url(self) -> str:
        if self.api_url.endswith("/api/generate"):
            return self.api_url.replace("/api/generate", "/api/tags")
        return self.api_url.rstrip("/") + "/api/tags"

    def is_available(self, refresh: bool = False) -> bool:
        if self._availability_cached is not None and not refresh:
            return self._availability_cached
        try:
            response = requests.get(self._tags_url(), timeout=2)
            self._availability_cached = response.status_code == 200
        except requests.RequestException:
            self._availability_cached = False
        return self._availability_cached

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.2,
        max_tokens: int = 220,
    ) -> Optional[str]:
        if not self.is_available():
            return None

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
            if response.status_code != 200:
                logger.debug("Local AI request failed with status: %s", response.status_code)
                return None
            text = response.json().get("response", "").strip()
            return text or None
        except (requests.RequestException, ValueError) as exc:
            logger.debug("Local AI request error: %s", exc)
            return None


class VulnerabilityIntelligence:
    """AI-powered vulnerability prediction and risk assessment."""

    def __init__(self):
        self.cve_database = self._load_cve_database()
        self.risk_weights = {
            "critical_cve": 0.9,
            "known_exploit": 0.85,
            "recent_disclosure": 0.75,
            "tech_stack_match": 0.7,
            "port_exposure": 0.65,
            "default_config": 0.8,
            "outdated_version": 0.75,
        }

    def _load_cve_database(self) -> Dict[str, Any]:
        """Load and cache CVE database for fast lookup."""
        return {
            "nginx": {
                "1.18.0": ["CVE-2021-23017"],
                "1.19.0": [],
                "1.20.0": ["CVE-2021-23017"],
            },
            "apache": {
                "2.4.48": ["CVE-2021-41773", "CVE-2021-42013"],
                "2.4.49": ["CVE-2021-41773"],
                "2.4.50": [],
            },
            "wordpress": {
                "5.7": ["CVE-2021-29447", "CVE-2021-29450"],
                "5.8": ["CVE-2021-39201"],
                "6.0": [],
            },
            "laravel": {
                "8.0": ["CVE-2021-43808"],
                "9.0": [],
            },
            "jenkins": {
                "2.303": ["CVE-2021-21685", "CVE-2021-21686"],
                "2.319": [],
            },
        }

    def predict_vulnerability_score(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered vulnerability prediction based on asset fingerprinting.

        Returns risk score (0-100), likelihood, and reasoning.
        """
        score = 0.0
        reasons: List[str] = []
        vulnerabilities: List[str] = []

        techs = asset_data.get("technologies", [])
        ports = asset_data.get("open_ports", [])
        domain = asset_data.get("domain", "unknown")

        for tech in techs:
            tech_name = tech.get("name", "").lower()
            version = tech.get("version", "")
            if tech_name in self.cve_database and version:
                cves = self.cve_database[tech_name].get(version, [])
                if cves:
                    score += len(cves) * self.risk_weights["critical_cve"] * 10
                    vulnerabilities.extend(cves)
                    reasons.append(f"Known CVEs in {tech_name} {version}: {', '.join(cves)}")

        dangerous_ports = {
            22: "SSH - Potential brute force target",
            23: "Telnet - Unencrypted protocol",
            3389: "RDP - Common attack vector",
            3306: "MySQL - Database exposure",
            5432: "PostgreSQL - Database exposure",
            6379: "Redis - Unauthenticated access risk",
            27017: "MongoDB - Often misconfigured",
            9200: "Elasticsearch - Data exposure",
        }

        for port in ports:
            if port in dangerous_ports:
                score += self.risk_weights["port_exposure"] * 8
                reasons.append(f"Port {port} exposed: {dangerous_ports[port]}")

        tech_names_lower = [t.get("name", "").lower() for t in techs]
        if "wordpress" in tech_names_lower:
            score += 15
            reasons.append("WordPress detected - Common attack target")
        if "jenkins" in tech_names_lower:
            score += 20
            reasons.append("Jenkins detected - High-value target with RCE history")
        if "apache" in tech_names_lower or "nginx" in tech_names_lower:
            score += 10
            reasons.append("Web server detected - Check for misconfigurations")

        final_score = min(score, 100)
        if final_score >= 75:
            risk_level, likelihood, color = "CRITICAL", "Very High", "red"
        elif final_score >= 50:
            risk_level, likelihood, color = "HIGH", "High", "orange"
        elif final_score >= 25:
            risk_level, likelihood, color = "MEDIUM", "Moderate", "yellow"
        else:
            risk_level, likelihood, color = "LOW", "Low", "green"

        return {
            "vulnerability_score": round(final_score, 2),
            "risk_level": risk_level,
            "exploit_likelihood": likelihood,
            "color": color,
            "cves_found": vulnerabilities,
            "reasons": reasons,
            "recommendations": self._generate_recommendations(asset_data, reasons),
            "ai_analysis": self._generate_ai_summary(domain, final_score, reasons),
        }

    def _generate_recommendations(self, asset_data: Dict[str, Any], reasons: List[str]) -> List[str]:
        recommendations: List[str] = []
        techs = [t.get("name", "").lower() for t in asset_data.get("technologies", [])]
        ports = asset_data.get("open_ports", [])

        if 22 in ports:
            recommendations.append("Implement SSH key-based auth and disable password login")
        if 3306 in ports or 5432 in ports:
            recommendations.append("Restrict database access to internal network only")
        if 6379 in ports:
            recommendations.append("Enable Redis authentication and bind to localhost")

        if "wordpress" in techs:
            recommendations.append("Update WordPress core and all plugins to latest versions")
            recommendations.append("Install security plugins (Wordfence, iThemes Security)")
        if "jenkins" in techs:
            recommendations.append("Enable Jenkins authentication and CSRF protection")
            recommendations.append("Restrict script console to authorized users only")
        if any("cve" in r.lower() for r in reasons):
            recommendations.append("Patch all known CVEs immediately - prioritize CVSS 9.0+")

        recommendations.append("Implement WAF and rate limiting")
        recommendations.append("Enable security headers (CSP, HSTS, X-Frame-Options)")
        return recommendations

    def _generate_ai_summary(self, domain: str, score: float, reasons: List[str]) -> str:
        if score >= 75:
            summary = f"CRITICAL ALERT: {domain} shows extremely high vulnerability risk. "
            summary += f"Immediate action required. {len(reasons)} critical issues detected."
        elif score >= 50:
            summary = f"HIGH RISK: {domain} has significant security concerns. "
            summary += f"{len(reasons)} important issues found."
        elif score >= 25:
            summary = f"MODERATE RISK: {domain} shows some security gaps. "
            summary += f"Review {len(reasons)} identified issues."
        else:
            summary = f"LOW RISK: {domain} appears relatively secure."
        return summary

    def batch_analyze(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        total_score = 0
        critical_count = 0
        high_count = 0

        for asset in assets:
            analysis = self.predict_vulnerability_score(asset)
            results.append({"asset": asset.get("domain", "unknown"), "analysis": analysis})
            total_score += analysis["vulnerability_score"]
            if analysis["risk_level"] == "CRITICAL":
                critical_count += 1
            elif analysis["risk_level"] == "HIGH":
                high_count += 1

        avg_score = total_score / len(assets) if assets else 0
        return {
            "total_assets": len(assets),
            "average_risk_score": round(avg_score, 2),
            "critical_assets": critical_count,
            "high_risk_assets": high_count,
            "detailed_results": results,
            "summary": (
                f"Analyzed {len(assets)} assets: {critical_count} critical, "
                f"{high_count} high risk. Average score: {avg_score:.1f}/100"
            ),
        }


class AISecurityAssistant:
    """AI-powered security assistant for intelligent recommendations."""

    def __init__(self):
        self.provider = LocalLLMProvider()
        self.use_local_ai = self.provider.is_available()

    def generate_report_summary(self, scan_data: Dict[str, Any]) -> str:
        """Generate executive summary using local Mistral when available."""
        if self.use_local_ai:
            prompt = (
                "You are a senior application security analyst. Write a concise executive summary "
                "for this scan data in markdown with: overview, key risks, and top 3 remediation actions.\n\n"
                f"Scan data JSON:\n{json.dumps(scan_data, ensure_ascii=True)}"
            )
            result = self.provider.generate(prompt=prompt, max_tokens=320)
            if result:
                return result
        return self._generate_template_summary(scan_data)

    def generate_phase_guidance(self, phase_num: int, phase_name: str, context: Dict[str, Any]) -> str:
        """Generate short AI guidance for a pipeline phase."""
        fallback = {
            1: "Correlate passive intel with scope to reduce false positives early.",
            2: "Prioritize newly discovered subdomains with business-facing naming patterns.",
            3: "Validate takeover candidates with DNS/CNAME evidence before triage.",
            4: "Focus on exposed admin, DB, and remote-access ports first.",
            5: "Baseline live hosts by status code and response behavior.",
            6: "Prioritize crawl paths containing auth, admin, and API keywords.",
            7: "Probe GraphQL introspection and weak auth paths first.",
            8: "Rank historical endpoints that still resolve and expose sensitive paths.",
            9: "Test authorization boundaries across object identifiers systematically.",
            10: "Prioritize exploitable critical/high findings with clear reproduction paths.",
        }

        if self.use_local_ai:
            prompt = (
                "Return one short practical sentence (max 24 words) for security analysts.\n"
                f"Phase {phase_num}: {phase_name}\n"
                f"Context: {json.dumps(context, ensure_ascii=True)}"
            )
            result = self.provider.generate(prompt=prompt, max_tokens=64, temperature=0.1)
            if result:
                return " ".join(result.split())[:220]

        return fallback.get(phase_num, "Continue with least-noisy, highest-signal validation steps.")

    def _generate_template_summary(self, scan_data: Dict[str, Any]) -> str:
        total_assets = scan_data.get("total_assets", 0)
        critical = scan_data.get("critical_findings", 0)
        high = scan_data.get("high_findings", 0)
        medium = scan_data.get("medium_findings", 0)
        summary = f"""
## Executive Summary

- Total Assets Scanned: {total_assets}
- Critical Findings: {critical}
- High Risk Findings: {high}
- Medium Risk Findings: {medium}

Immediate priority is remediation of critical and high-risk findings, followed by hardening and verification of exposed attack surface.
"""
        return summary.strip()

    def explain_finding(self, finding: Dict[str, Any]) -> str:
        """Explain a security finding in simple terms."""
        if self.use_local_ai:
            prompt = (
                "Explain this security finding in plain language for developers in 2 short sentences.\n"
                f"Finding: {json.dumps(finding, ensure_ascii=True)}"
            )
            result = self.provider.generate(prompt=prompt, max_tokens=120, temperature=0.1)
            if result:
                return result

        severity = finding.get("severity", "unknown")
        explanations = {
            "sql-injection": "SQL Injection allows attackers to manipulate database queries and access unauthorized data.",
            "xss": "Cross-Site Scripting (XSS) lets attackers inject malicious scripts into user browsers.",
            "open-redirect": "Open Redirect can be abused for phishing by redirecting users to malicious domains.",
            "subdomain-takeover": "Subdomain Takeover occurs when DNS points to unclaimed services that attackers can hijack.",
        }
        return explanations.get(
            finding.get("type", "").lower(),
            f"This {severity} severity finding requires security review.",
        )


vuln_intel = VulnerabilityIntelligence()
ai_assistant = AISecurityAssistant()


def analyze_asset_risk(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to analyze asset vulnerability risk."""
    return vuln_intel.predict_vulnerability_score(asset_data)


def batch_analyze_assets(assets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze multiple assets in batch."""
    return vuln_intel.batch_analyze(assets)


if __name__ == "__main__":
    sample_asset = {
        "domain": "example.com",
        "technologies": [
            {"name": "nginx", "version": "1.18.0"},
            {"name": "wordpress", "version": "5.7"},
        ],
        "open_ports": [80, 443, 22, 3306],
    }

    print(json.dumps(analyze_asset_risk(sample_asset), indent=2))
    print("\n--- AI report summary preview ---")
    print(
        ai_assistant.generate_report_summary(
            {"total_assets": 12, "critical_findings": 2, "high_findings": 5, "medium_findings": 7}
        )
    )
