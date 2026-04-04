import os
import json
from datetime import datetime

class ReportWriter:
    def __init__(self):
        self.output_dir = "reports"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_report(self, target_domain, vulnerabilities):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # SECURITY: Sanitize domain to prevent path traversal
        # Remove all path separators and suspicious characters
        safe_domain = "".join(c if c.isalnum() or c in '-_' else '_' for c in target_domain)
        filename = f"HACKERONE_REPORT_{safe_domain}_{timestamp}.md"
        
        # Ensure file stays within reports directory
        filepath = os.path.abspath(os.path.join(self.output_dir, filename))
        output_abs = os.path.abspath(self.output_dir)
        
        # Validate the path is within output_dir (prevent path traversal)
        if not filepath.startswith(output_abs):
            raise ValueError(f"Path traversal attempt detected: {target_domain}")

        report_content = f"# 🐛 BUG BOUNTY SUBMISSION: {target_domain}\n"
        report_content += f"**Date Discovered:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report_content += f"**Discovered By:** Project Trishul (Autonomous Bug Bounty Pipeline)\n\n"
        report_content += "---\n\n"

        rendered_findings = 0
        for vuln in vulnerabilities:
            try:
                data = json.loads(vuln)
                info = data.get("info", {})
                
                name = info.get("name", "Unknown Vulnerability")
                severity = info.get("severity", "info").upper()
                url = data.get("matched-at", "Unknown URL")
                desc = info.get("description", "No description provided.")
                
                # Automated bounty estimator
                bounty_estimate = "$0 (Informational)"
                if severity == "CRITICAL": bounty_estimate = "$3,000 - $10,000+"
                elif severity == "HIGH": bounty_estimate = "$1,000 - $3,000"
                elif severity == "MEDIUM": bounty_estimate = "$500 - $1,000"
                elif severity == "LOW": bounty_estimate = "$50 - $200"

                report_content += f"## Vulnerability: {name}\n"
                report_content += f"**Severity:** {severity}\n"
                report_content += f"**Estimated Payout:** {bounty_estimate}\n\n"
                
                report_content += f"### Summary\n"
                report_content += f"{desc}\n\n"
                
                report_content += f"### Steps To Reproduce\n"
                report_content += f"1. Navigate to the following vulnerable endpoint:\n"
                report_content += f"   `{url}`\n"
                report_content += f"2. Observe the exposed sensitive data or successful exploit payload execution.\n\n"
                
                report_content += f"### Impact\n"
                if "takeover" in name.lower():
                    report_content += "An attacker can claim this dangling DNS record, allowing them to host malicious content, steal session cookies, or execute sophisticated phishing campaigns using the company's official domain.\n\n"
                elif "exposure" in name.lower() or "token" in name.lower():
                    report_content += "Hardcoded secrets allow an attacker to pivot into internal infrastructure, impersonate the application, or steal customer data, leading to a massive data breach.\n\n"
                else:
                    report_content += "This vulnerability allows an unauthorized attacker to compromise the integrity, confidentiality, or availability of the application.\n\n"
                
                report_content += "---\n\n"
                rendered_findings += 1

            except json.JSONDecodeError:
                continue

        if rendered_findings == 0:
            report_content += "## Scan Outcome\n"
            report_content += "**Result:** No vulnerabilities found.\n\n"
            report_content += "The scan completed without any reportable vulnerability findings for the provided target scope.\n\n"
            report_content += "---\n\n"

        with open(filepath, "w") as f:
            f.write(report_content)

        return filepath
