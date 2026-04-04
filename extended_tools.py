import json
import logging
import os
import re
import shutil
import subprocess
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin

from scope_checker import ScopeChecker

logger = logging.getLogger(__name__)


URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def findings_to_nuclei_lines(findings: List[Dict[str, str]]) -> List[str]:
    """Convert supplemental findings into nuclei-like JSON lines for downstream reuse."""
    lines: List[str] = []
    seen: Set[str] = set()

    for finding in findings:
        tool = finding.get("tool", "supplemental")
        name = finding.get("name", "Supplemental Finding")
        severity = finding.get("severity", "medium").lower()
        url = finding.get("url", "")
        description = finding.get("description", "")
        evidence = finding.get("evidence", "")

        key = f"{tool}|{name}|{severity}|{url}"
        if key in seen:
            continue
        seen.add(key)

        payload = {
            "template-id": f"{tool}-supplemental",
            "info": {
                "name": name,
                "severity": severity,
                "description": description,
                "tags": tool,
            },
            "type": "http",
            "matched-at": url,
            "host": url,
        }
        if evidence:
            payload["extracted-results"] = [evidence[:500]]
        lines.append(json.dumps(payload))

    return lines


class ExternalCommandRunner:
    def __init__(self, scope_checker: Optional[ScopeChecker] = None):
        self.scope_checker = scope_checker or ScopeChecker()
        self.junk_extensions = {
            ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
            ".css", ".woff", ".woff2", ".ttf", ".eot",
            ".mp4", ".mp3", ".avi", ".pdf",
        }

    @staticmethod
    def _binary_available(binary: str) -> bool:
        return shutil.which(binary) is not None

    @staticmethod
    def _run(command: List[str], timeout: int = 120, input_text: Optional[str] = None) -> str:
        try:
            result = subprocess.run(
                command,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            if result.returncode != 0 and result.stderr:
                logger.debug("%s failed: %s", command[0], result.stderr.strip()[:300])
            return result.stdout or ""
        except subprocess.TimeoutExpired:
            logger.warning("%s timed out after %ss", command[0], timeout)
            return ""
        except OSError as exc:
            logger.warning("Failed running %s: %s", command[0], exc)
            return ""

    @staticmethod
    def _extract_urls(text: str) -> List[str]:
        return list({u.rstrip("),.]") for u in URL_RE.findall(text or "")})

    def _extract_subdomains(self, text: str, root_domain: str) -> List[str]:
        if not text:
            return []
        escaped = re.escape(root_domain)
        pattern = re.compile(rf"\b(?:[a-zA-Z0-9-]+\.)+{escaped}\b", re.IGNORECASE)
        found = set(m.group(0).lower() for m in pattern.finditer(text))
        return [d for d in found if self.scope_checker.is_in_scope(d, root_domain)]

    def _filter_web_urls(self, urls: List[str], root_domain: str) -> List[str]:
        clean: Set[str] = set()
        for url in urls:
            candidate = url.strip()
            if not candidate.startswith(("http://", "https://")):
                continue
            host = candidate.split("://", 1)[1].split("/", 1)[0].split(":")[0]
            if not self.scope_checker.is_in_scope(host, root_domain):
                continue
            base = candidate.split("?", 1)[0].lower()
            if any(base.endswith(ext) for ext in self.junk_extensions):
                continue
            clean.add(candidate)
        return list(clean)


class AmassRunner(ExternalCommandRunner):
    def discover_subdomains(self, root_domain: str) -> List[str]:
        if not self._binary_available("amass"):
            return []
        output = self._run(["amass", "enum", "-passive", "-d", root_domain], timeout=240)
        return self._extract_subdomains(output, root_domain)


class DNSReconRunner(ExternalCommandRunner):
    def discover_subdomains(self, root_domain: str) -> List[str]:
        if not self._binary_available("dnsrecon"):
            return []
        output = self._run(["dnsrecon", "-d", root_domain, "-t", "std"], timeout=180)
        return self._extract_subdomains(output, root_domain)


class WaybackUrlsRunner(ExternalCommandRunner):
    def fetch_history(self, root_domain: str) -> List[str]:
        if not self._binary_available("waybackurls"):
            return []
        output = self._run(["waybackurls", root_domain], timeout=180)
        urls = self._extract_urls(output)
        return self._filter_web_urls(urls, root_domain)


class WebDiscoveryRunner(ExternalCommandRunner):
    def discover_urls(self, seed_urls: List[str], root_domain: str, max_urls: int = 4) -> List[str]:
        if not seed_urls:
            return []
        targets = seed_urls[:max_urls]
        discovered: Set[str] = set()

        for url in targets:
            discovered.update(self._run_gobuster(url))
            discovered.update(self._run_dirsearch(url))
            discovered.update(self._run_feroxbuster(url))

        return self._filter_web_urls(list(discovered), root_domain)

    def _run_gobuster(self, url: str) -> List[str]:
        if not self._binary_available("gobuster"):
            return []
        wordlists = [
            "/usr/share/wordlists/dirb/common.txt",
            "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
        ]
        wordlist = next((w for w in wordlists if os.path.exists(w)), None)
        if not wordlist:
            return []
        output = self._run(
            ["gobuster", "dir", "-u", url, "-w", wordlist, "-q", "-t", "20"],
            timeout=90,
        )
        urls: Set[str] = set()
        for line in output.splitlines():
            m = re.match(r"^/[^ ]+", line.strip())
            if m:
                urls.add(urljoin(url.rstrip("/") + "/", m.group(0).lstrip("/")))
        return list(urls)

    def _run_dirsearch(self, url: str) -> List[str]:
        if not self._binary_available("dirsearch"):
            return []
        output = self._run(
            ["dirsearch", "-u", url, "--quiet", "--format", "plain", "-t", "20"],
            timeout=90,
        )
        return self._extract_urls(output)

    def _run_feroxbuster(self, url: str) -> List[str]:
        if not self._binary_available("feroxbuster"):
            return []
        output = self._run(
            ["feroxbuster", "-u", url, "-q", "-n", "-d", "1", "-t", "20"],
            timeout=90,
        )
        return self._extract_urls(output)


class ParamDiscoveryRunner(ExternalCommandRunner):
    def discover_urls(self, root_domain: str, seed_urls: List[str], max_urls: int = 6) -> List[str]:
        discovered: Set[str] = set()
        discovered.update(self._from_paramspider(root_domain))

        for url in seed_urls[:max_urls]:
            discovered.update(self._from_arjun(url))

        return self._filter_web_urls(list(discovered), root_domain)

    def _from_paramspider(self, root_domain: str) -> List[str]:
        if not self._binary_available("paramspider"):
            return []
        output = self._run(["paramspider", "-d", root_domain], timeout=180)
        return [u for u in self._extract_urls(output) if "?" in u]

    def _from_arjun(self, url: str) -> List[str]:
        if not self._binary_available("arjun"):
            return []
        output = self._run(["arjun", "-u", url, "--get", "--stable"], timeout=90)
        urls = set(self._extract_urls(output))
        # Arjun may output raw parameter names; synthesize probe URLs for downstream testing.
        for match in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]{2,40}\b", output):
            if match.lower() in {"http", "https", "target", "params", "parameter"}:
                continue
            urls.add(f"{url}?{match}=1")
        return list(urls)


class WhatWebRunner(ExternalCommandRunner):
    def fingerprint(self, urls: List[str], max_urls: int = 8) -> Dict[str, List[str]]:
        if not self._binary_available("whatweb"):
            return {}
        fingerprints: Dict[str, List[str]] = {}
        for url in urls[:max_urls]:
            output = self._run(["whatweb", "-a", "1", url], timeout=45)
            plugins: Set[str] = set()
            # Parse plugin tokens such as WordPress[6.5], Apache[2.4.54]
            for line in output.splitlines():
                for token in line.split(","):
                    token = token.strip()
                    if "[" in token:
                        plugins.add(token.split("[", 1)[0].strip())
                    elif token and "http" not in token.lower():
                        plugins.add(token)
            if plugins:
                fingerprints[url] = sorted(plugins)
        return fingerprints


class SupplementalWebScanner(ExternalCommandRunner):
    def scan(self, urls: List[str], target_domain: str, fingerprints: Optional[Dict[str, List[str]]] = None) -> List[Dict[str, str]]:
        findings: List[Dict[str, str]] = []
        if not urls:
            return findings

        candidate_urls = self._filter_web_urls(urls[:20], target_domain)
        param_urls = [u for u in candidate_urls if "?" in u][:3]
        wordpress_urls = [u for u in candidate_urls if "/wp-" in u.lower() or "wp-admin" in u.lower()]

        if fingerprints:
            for url, tech in fingerprints.items():
                tech_text = " ".join(tech).lower()
                if "wordpress" in tech_text:
                    wordpress_urls.append(url)
        wordpress_urls = list(dict.fromkeys(wordpress_urls))[:2]

        findings.extend(self._run_nikto(candidate_urls[:2]))
        findings.extend(self._run_wpscan(wordpress_urls))
        findings.extend(self._run_sqlmap(param_urls))
        findings.extend(self._run_dalfox(param_urls))
        return findings

    def _run_nikto(self, urls: List[str]) -> List[Dict[str, str]]:
        if not urls or not self._binary_available("nikto"):
            return []
        findings: List[Dict[str, str]] = []
        for url in urls:
            output = self._run(["nikto", "-h", url], timeout=120)
            for line in output.splitlines():
                if line.startswith("+ ") and ("OSVDB" in line or "vulnerability" in line.lower() or "risk" in line.lower()):
                    findings.append({
                        "tool": "nikto",
                        "name": "Nikto web vulnerability finding",
                        "severity": "medium",
                        "url": url,
                        "description": "Nikto reported a potential web server issue.",
                        "evidence": line.strip(),
                    })
        return findings[:10]

    def _run_wpscan(self, urls: List[str]) -> List[Dict[str, str]]:
        if not urls or not self._binary_available("wpscan"):
            return []
        findings: List[Dict[str, str]] = []
        for url in urls:
            output = self._run(["wpscan", "--url", url, "--enumerate", "vp,vt,cb,dbe"], timeout=150)
            for line in output.splitlines():
                if "[!]" in line or "vulnerab" in line.lower():
                    findings.append({
                        "tool": "wpscan",
                        "name": "WordPress security issue",
                        "severity": "high",
                        "url": url,
                        "description": "WPScan reported a potential WordPress vulnerability.",
                        "evidence": line.strip(),
                    })
        return findings[:10]

    def _run_sqlmap(self, urls: List[str]) -> List[Dict[str, str]]:
        if not urls or not self._binary_available("sqlmap"):
            return []
        findings: List[Dict[str, str]] = []
        for url in urls:
            output = self._run(
                ["sqlmap", "-u", url, "--batch", "--level", "1", "--risk", "1", "--threads", "1", "--smart"],
                timeout=120,
            )
            for line in output.splitlines():
                lowered = line.lower()
                if "is vulnerable" in lowered or "sql injection" in lowered or "[critical]" in lowered:
                    findings.append({
                        "tool": "sqlmap",
                        "name": "SQL injection indicator",
                        "severity": "critical",
                        "url": url,
                        "description": "SQLMap reported possible SQL injection.",
                        "evidence": line.strip(),
                    })
        return findings[:10]

    def _run_dalfox(self, urls: List[str]) -> List[Dict[str, str]]:
        if not urls or not self._binary_available("dalfox"):
            return []
        findings: List[Dict[str, str]] = []
        for url in urls:
            output = self._run(["dalfox", "url", url, "--silence"], timeout=90)
            for line in output.splitlines():
                lowered = line.lower()
                if "vulnerab" in lowered or "xss" in lowered or "[poc]" in lowered:
                    findings.append({
                        "tool": "dalfox",
                        "name": "XSS indicator",
                        "severity": "high",
                        "url": url,
                        "description": "Dalfox reported possible cross-site scripting.",
                        "evidence": line.strip(),
                    })
        return findings[:10]
