# TERMS OF SERVICE

**Last Updated: March 27, 2026**

## 1. ACCEPTANCE OF TERMS

By using Trishul ("the Software"), you agree to comply with and be bound by these Terms of Service. If you do not agree to these terms, **DO NOT USE THIS SOFTWARE**.

## 2. AUTHORIZATION REQUIREMENT

### 2.1 Written Authorization
**You MUST have explicit written authorization** before using this software to test any computer system, network, or web application. Acceptable forms of authorization include:

- ✅ Official bug bounty program participation (HackerOne, Bugcrowd, Intigriti, etc.)
- ✅ Signed penetration testing contract
- ✅ Written permission from the system owner
- ✅ Your own systems/infrastructure
- ✅ Designated security testing environments

### 2.2 Unauthorized Access is Illegal
Testing without authorization may violate:

- **Computer Fraud and Abuse Act (CFAA)** - 18 U.S.C. § 1030 (USA) - *Up to 10 years imprisonment*
- **Computer Misuse Act 1990** (UK) - *Up to 2 years imprisonment*
- **EU Cybercrime Directive** - Criminal penalties vary by member state
- **Local cybercrime laws** in your jurisdiction

### 2.3 Scope Compliance
You must:
- Only test targets within your authorized scope
- Respect out-of-scope exclusions
- Comply with bug bounty program rules
- Honor rate limits and testing restrictions
- Immediately report findings per disclosure policy

## 3. PROHIBITED USES

You may **NOT** use this software to:

❌ Test systems without authorization  
❌ Exploit vulnerabilities beyond proof-of-concept  
❌ Access, modify, or delete data without permission  
❌ Cause denial of service or system disruption  
❌ Exfiltrate sensitive data  
❌ Engage in social engineering or phishing  
❌ Test third-party systems outside your scope  
❌ Violate any applicable laws or regulations  

## 4. USER RESPONSIBILITIES

### 4.1 Legal Compliance
You are solely responsible for:
- Obtaining proper authorization
- Complying with all applicable laws
- Following bug bounty program rules
- Respecting rate limits and testing boundaries
- Ethical disclosure of findings

### 4.2 Scope Validation
You must:
- Define authorized scope using `--scope` flag
- Verify targets before testing
- Maintain audit logs of all testing activity
- Stop testing immediately if scope is exceeded

### 4.3 Professional Conduct
You agree to:
- Act in good faith as a security researcher
- Report vulnerabilities responsibly
- Not publicly disclose findings before remediation
- Cooperate with organizations on remediation
- Not demand payment beyond bug bounty rewards

## 5. BUG BOUNTY PROGRAM COMPLIANCE

### 5.1 Program Rules
When participating in bug bounty programs, you must:
- Read and comply with program-specific rules
- Respect testing restrictions (e.g., "no automated scanners")
- Honor disclosure timelines
- Submit findings through official channels
- Not test out-of-scope assets

### 5.2 Common Restrictions
Most programs prohibit:
- Denial of service testing
- Spam/phishing
- Social engineering
- Physical security testing
- Accessing other users' data beyond PoC
- Modifying or deleting data
- Automated high-volume testing without approval

### 5.3 Safe Harbor
Bug bounty safe harbor protections typically require:
- Testing within defined scope
- Acting in good faith
- Reporting promptly
- Not exploiting beyond PoC
- Cooperating with remediation

## 6. DISCLAIMER OF WARRANTIES

### 6.1 "AS IS" Provision
**THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.**

The creators make NO warranties, express or implied, including but not limited to:
- Fitness for a particular purpose
- Accuracy of vulnerability detection
- Absence of false positives/negatives
- Legal compliance in your jurisdiction
- Compatibility with bug bounty programs

### 6.2 No Legal Advice
Nothing in this software or documentation constitutes legal advice. Consult with a qualified attorney regarding:
- Authorization requirements
- Applicable laws in your jurisdiction
- Bug bounty program compliance
- Liability and risk management

## 7. LIMITATION OF LIABILITY

### 7.1 Maximum Liability
**TO THE MAXIMUM EXTENT PERMITTED BY LAW**, the creators, contributors, and maintainers of this software shall NOT be liable for:

- Direct, indirect, incidental, or consequential damages
- Legal fees, fines, or penalties from unauthorized use
-損害 (damages) from false positives/negatives
- Service disruptions caused by the software
- Data loss or corruption
- Criminal or civil liability from your actions
- Bug bounty disputes or payment issues

### 7.2 User Assumption of Risk
**YOU ASSUME ALL RISK** associated with using this software, including:
- Legal liability from unauthorized testing
- Violations of bug bounty program rules
- IP bans, account suspensions, or blacklisting
- Financial damages to tested systems
- Criminal prosecution if laws are violated

### 7.3 Indemnification
You agree to **indemnify and hold harmless** the software creators from any claims, damages, losses, liabilities, and expenses (including legal fees) arising from:
- Your use or misuse of the software
- Violations of these Terms of Service
- Violations of applicable laws
- Unauthorized testing
- Disputes with bug bounty programs or system owners

## 8. AUDIT LOGGING

### 8.1 Logging Requirement
The software generates audit logs of all testing activity. You must:
- Maintain these logs for legal accountability
- Provide logs if requested by system owners
- Use logs as evidence of authorized testing
- Not tamper with or delete audit logs

### 8.2 Log Retention
Recommended log retention: **Minimum 1 year** for legal protection.

## 9. RATE LIMITING AND RESPONSIBLE USE

### 9.1 Rate Limits
The software includes default rate limits to prevent:
- Service degradation
- WAF/security system triggering
- IP bans
- Violation of bug bounty "excessive testing" rules

### 9.2 Custom Limits
You may adjust rate limits using:
- `--request-delay` flag (default: 0.5s)
- `--max-idor-tests` flag (default: 20)
- `--read-only` mode for non-invasive testing

### 9.3 Stealth Mode
Use `--stealth` for extra-conservative testing with:
- Longer delays between requests
- Reduced request volumes
- Minimal impact on target systems

## 10. DATA PROTECTION

### 10.1 Sensitive Data
If you discover sensitive data during testing:
- Do NOT exfiltrate or store sensitive data
- Do NOT share findings publicly before disclosure
- Only collect minimum necessary evidence for PoC
- Immediately report to the organization
- Delete collected evidence after reporting

### 10.2 Privacy Compliance
You must comply with:
- GDPR (EU)
- CCPA (California)
- Other applicable data protection laws

## 11. UPDATES AND MODIFICATIONS

### 11.1 Terms Updates
These Terms may be updated at any time. Continued use of the software after updates constitutes acceptance of new terms.

### 11.2 Software Updates
You are responsible for:
- Keeping the software updated
- Reviewing changelog for legal/compliance changes
- Re-accepting terms after major updates

## 12. TERMINATION

### 12.1 Immediate Termination
Your license to use this software terminates immediately if you:
- Violate these Terms of Service
- Use the software for unauthorized testing
- Fail to comply with applicable laws
- Engage in malicious or unethical conduct

### 12.2 Effect of Termination
Upon termination, you must:
- Immediately cease using the software
- Delete all copies of the software
- Preserve audit logs for legal accountability

## 13. OPEN SOURCE LICENSE

### 13.1 License Terms
This software is released under the **MIT License** (see LICENSE file) with the following additional provisions:

- The MIT License's liability disclaimers apply
- These Terms of Service supplement the MIT License
- In case of conflict, the more restrictive provision applies
- The MIT License's permissions (modify, distribute) are subject to these Terms

### 13.2 Contributor Liability
Contributors to this project are also protected by the liability disclaimers in Section 7.

## 14. SEVERABILITY

If any provision of these Terms is found to be unenforceable or invalid, that provision shall be limited or eliminated to the minimum extent necessary, and the remaining provisions shall remain in full force.

## 15. GOVERNING LAW

These Terms shall be governed by and construed in accordance with the laws of the jurisdiction where the user is located, without regard to conflict of law provisions.

## 16. CONTACT

For legal questions or concerns:
- Open an issue on GitHub: [Your Repository URL]
- Email: [Your Email] (if applicable)

## 17. ACKNOWLEDGMENT

**BY USING THIS SOFTWARE, YOU ACKNOWLEDGE THAT:**

✅ You have read and understood these Terms of Service  
✅ You have the legal authority to agree to these Terms  
✅ You have explicit authorization for all testing activities  
✅ You understand the legal risks of unauthorized testing  
✅ You will comply with all applicable laws and bug bounty rules  
✅ You assume all liability for your use of this software  
✅ You will not hold the creators liable for any damages  

---

## EXPLICIT ACCEPTANCE REQUIRED

**This software will prompt you to explicitly accept these terms before each scan by typing "I AGREE".**

Failure to provide explicit consent will prevent the software from running.

**Last Updated: March 27, 2026**  
**Version: 1.0**

---

**IF YOU DO NOT AGREE TO THESE TERMS, DO NOT USE THIS SOFTWARE.**
