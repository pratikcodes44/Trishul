# Copyright (c) 2024-2026 Project Trishul Contributors
# Licensed under the MIT License - see LICENSE file for details

"""
Gmail Notifier - SMTP Email Notification System
================================================
Replaces Discord notifications with Gmail-based email alerts for:
- Target discovery
- Attack start/completion
- Vulnerability reports with PDF attachments
- Attack interruptions and stuck detection
"""

import smtplib
import os
import logging
import time
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class GmailNotifier:
    """Gmail-based email notification system for Trishul security scanner."""
    
    def __init__(self):
        """Initialize Gmail notifier with environment configuration."""
        self.email_user = os.getenv('EMAIL_USER', 'pratikkotecha67@gmail.com')
        self.email_password = os.getenv('EMAIL_PASSWORD', 'tgbw tmio efzm rpyq')
        self.email_recipient = os.getenv('EMAIL_RECIPIENT', self.email_user)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        # Validate configuration
        if not self.email_user or not self.email_password:
            logger.warning("⚠️  Gmail credentials not configured. Email notifications disabled.")
            logger.warning("Set EMAIL_USER and EMAIL_PASSWORD environment variables to enable.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info(f"✅ Gmail notifier enabled: {self.email_user} → {self.email_recipient}")
    
    def _create_connection(self) -> Optional[smtplib.SMTP]:
        """
        Create SMTP connection with retry logic.
        
        Returns:
            SMTP connection or None if failed
        """
        if not self.enabled:
            return None
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
                server.starttls()
                server.login(self.email_user, self.email_password)
                return server
            except smtplib.SMTPAuthenticationError:
                logger.error("❌ Gmail authentication failed. Check EMAIL_PASSWORD (use app password, not regular password)")
                return None
            except Exception as e:
                logger.warning(f"SMTP connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"❌ Failed to connect to Gmail SMTP after {max_retries} attempts")
                    return None
        
        return None
    
    def _send_email_safe(self, subject: str, html_body: str, pdf_path: Optional[str] = None):
        """Thread-safe wrapper for _send_email that catches exceptions."""
        try:
            self._send_email(subject, html_body, pdf_path)
        except Exception as e:
            logger.error(f"Background email send failed: {e}")
    
    def _send_email(self, subject: str, html_body: str, pdf_path: Optional[str] = None) -> bool:
        """
        Send email with optional PDF attachment.
        
        Args:
            subject: Email subject line
            html_body: HTML formatted email body
            pdf_path: Optional path to PDF report to attach
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Email notifications disabled, skipping send")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = self.email_recipient
            msg['Subject'] = subject
            
            # Add HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Attach PDF if provided
            if pdf_path and os.path.exists(pdf_path):
                try:
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_attachment = MIMEBase('application', 'pdf')
                        pdf_attachment.set_payload(pdf_file.read())
                        encoders.encode_base64(pdf_attachment)
                        pdf_attachment.add_header(
                            'Content-Disposition',
                            f'attachment; filename={os.path.basename(pdf_path)}'
                        )
                        msg.attach(pdf_attachment)
                        logger.info(f"📎 Attached PDF report: {os.path.basename(pdf_path)}")
                except Exception as e:
                    logger.warning(f"Failed to attach PDF {pdf_path}: {e}")
            
            # Send email
            server = self._create_connection()
            if not server:
                return False
            
            try:
                server.send_message(msg)
                logger.info(f"📧 Email sent successfully: {subject}")
                return True
            finally:
                server.quit()
                
        except Exception as e:
            logger.error(f"❌ Failed to send email '{subject}': {e}")
            return False
    
    def _format_time(self, seconds: float) -> str:
        """
        Format elapsed time as HH:MM:SS.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _format_vulnerabilities(self, vulns: List[Dict[str, Any]]) -> str:
        """
        Format vulnerability list as HTML table.
        
        Args:
            vulns: List of vulnerability dictionaries
            
        Returns:
            HTML table string
        """
        if not vulns:
            return "<p style='color: #28a745; font-weight: bold;'>✅ No vulnerabilities found</p>"
        
        # Group by severity
        critical = [v for v in vulns if v.get('severity', '').lower() == 'critical']
        high = [v for v in vulns if v.get('severity', '').lower() == 'high']
        medium = [v for v in vulns if v.get('severity', '').lower() == 'medium']
        low = [v for v in vulns if v.get('severity', '').lower() == 'low']
        info = [v for v in vulns if v.get('severity', '').lower() == 'info']
        
        html = f"""
        <h3>Vulnerability Summary</h3>
        <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr style="background-color: #f8f9fa;">
                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Severity</th>
                <th style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">Count</th>
            </tr>
        """
        
        if critical:
            html += f"""
            <tr style="background-color: #dc3545; color: white;">
                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>🔴 Critical</strong></td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;"><strong>{len(critical)}</strong></td>
            </tr>
            """
        
        if high:
            html += f"""
            <tr style="background-color: #fd7e14; color: white;">
                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>🟠 High</strong></td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;"><strong>{len(high)}</strong></td>
            </tr>
            """
        
        if medium:
            html += f"""
            <tr style="background-color: #ffc107;">
                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>🟡 Medium</strong></td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;"><strong>{len(medium)}</strong></td>
            </tr>
            """
        
        if low:
            html += f"""
            <tr style="background-color: #17a2b8; color: white;">
                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>🔵 Low</strong></td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;"><strong>{len(low)}</strong></td>
            </tr>
            """
        
        if info:
            html += f"""
            <tr style="background-color: #6c757d; color: white;">
                <td style="border: 1px solid #dee2e6; padding: 8px;"><strong>⚪ Info</strong></td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;"><strong>{len(info)}</strong></td>
            </tr>
            """
        
        html += f"""
            <tr style="background-color: #e9ecef; font-weight: bold;">
                <td style="border: 1px solid #dee2e6; padding: 8px;">Total</td>
                <td style="border: 1px solid #dee2e6; padding: 8px; text-align: center;">{len(vulns)}</td>
            </tr>
        </table>
        """
        
        # Show top 10 vulnerabilities
        html += "<h3>Top Vulnerabilities</h3><ul style='line-height: 1.8;'>"
        for vuln in vulns[:10]:
            severity = vuln.get('severity', 'unknown').upper()
            name = vuln.get('name', vuln.get('title', 'Unknown'))
            url = vuln.get('matched-at', vuln.get('url', ''))
            
            severity_color = {
                'CRITICAL': '#dc3545',
                'HIGH': '#fd7e14',
                'MEDIUM': '#ffc107',
                'LOW': '#17a2b8',
                'INFO': '#6c757d'
            }.get(severity, '#6c757d')
            
            html += f"""
            <li>
                <span style="color: {severity_color}; font-weight: bold;">[{severity}]</span> 
                {name}
                {f"<br><small style='color: #6c757d;'>URL: {url}</small>" if url else ""}
            </li>
            """
        
        if len(vulns) > 10:
            html += f"<li><em>... and {len(vulns) - 10} more (see attached PDF report)</em></li>"
        
        html += "</ul>"
        
        return html
    
    def send_target_found(self, domain: str, program_url: str, platform: str) -> bool:
        """
        Send notification when a bug bounty target is discovered.
        
        Args:
            domain: Target domain name
            program_url: URL to bug bounty program
            platform: Platform name (HackerOne, Bugcrowd, etc.)
            
        Returns:
            True if sent successfully
        """
        subject = f"🎯 Trishul: Target Found - {domain}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #007bff; color: white; padding: 20px; border-radius: 5px;">
                <h1 style="margin: 0;">🎯 Bug Bounty Target Discovered</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2 style="color: #007bff;">Target Information</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6; width: 150px;"><strong>Domain:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><code>{domain}</code></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6;"><strong>Platform:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{platform}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6;"><strong>Program URL:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><a href="{program_url}">{program_url}</a></td>
                    </tr>
                </table>
                
                <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 3px;">
                    <p style="margin: 0;"><strong>⏳ Status:</strong> Awaiting user confirmation to start attack...</p>
                </div>
            </div>
            
            <div style="padding: 20px; background-color: #f8f9fa; border-top: 2px solid #dee2e6; margin-top: 20px;">
                <p style="margin: 0; color: #6c757d; font-size: 12px;">
                    Sent by Trishul Security Scanner • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </body>
        </html>
        """
        
        # Send email asynchronously in background thread (non-blocking)
        thread = threading.Thread(
            target=self._send_email_safe,
            args=(subject, html_body),
            daemon=True,
            name="EmailNotifier-TargetFound"
        )
        thread.start()
        logger.info("📧 Target found notification queued (async)")
        return True  # Returns immediately without blocking
    
    def send_attack_started(self, domain: str, start_time: float) -> bool:
        """
        Send notification when attack begins.
        
        Args:
            domain: Target domain
            start_time: Attack start timestamp
            
        Returns:
            True if sent successfully
        """
        subject = f"🚀 Trishul: Attack Started - {domain}"
        
        start_datetime = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #28a745; color: white; padding: 20px; border-radius: 5px;">
                <h1 style="margin: 0;">🚀 Attack Initiated</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2 style="color: #28a745;">Attack in Progress</h2>
                <p><strong>Target:</strong> <code>{domain}</code></p>
                <p><strong>Started:</strong> {start_datetime}</p>
                
                <div style="margin-top: 30px; padding: 15px; background-color: #d1ecf1; border-left: 4px solid #17a2b8; border-radius: 3px;">
                    <p style="margin: 0;"><strong>⏱️ Timer Started:</strong> Continuous monitoring active</p>
                    <p style="margin: 10px 0 0 0;">You will be notified upon completion, interruption, or if any phase gets stuck.</p>
                </div>
            </div>
            
            <div style="padding: 20px; background-color: #f8f9fa; border-top: 2px solid #dee2e6; margin-top: 20px;">
                <p style="margin: 0; color: #6c757d; font-size: 12px;">
                    Sent by Trishul Security Scanner • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(subject, html_body)
    
    def send_attack_completed(self, domain: str, elapsed_time: float, 
                             vulns: List[Dict[str, Any]], pdf_path: Optional[str] = None) -> bool:
        """
        Send notification when attack completes with results.
        
        Args:
            domain: Target domain
            elapsed_time: Total attack duration in seconds
            vulns: List of discovered vulnerabilities
            pdf_path: Optional path to PDF report
            
        Returns:
            True if sent successfully
        """
        time_str = self._format_time(elapsed_time)
        vuln_count = len(vulns)
        
        if vuln_count > 0:
            subject = f"✅ Trishul: Attack Complete - {vuln_count} Vulnerabilities Found - {domain}"
            status_color = "#dc3545"  # Red for vulnerabilities found
            status_icon = "🔴"
        else:
            subject = f"✅ Trishul: Attack Complete - No Vulnerabilities - {domain}"
            status_color = "#28a745"  # Green for clean scan
            status_icon = "🟢"
        
        vuln_html = self._format_vulnerabilities(vulns)
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: {status_color}; color: white; padding: 20px; border-radius: 5px;">
                <h1 style="margin: 0;">{status_icon} Attack Completed</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2 style="color: {status_color};">Scan Results</h2>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6; width: 150px;"><strong>Target:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><code>{domain}</code></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6;"><strong>Duration:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong style="font-size: 18px; color: #007bff;">{time_str}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6;"><strong>Total Findings:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong style="font-size: 18px; color: {status_color};">{vuln_count}</strong></td>
                    </tr>
                </table>
                
                {vuln_html}
                
                {f'<div style="margin-top: 30px; padding: 15px; background-color: #d4edda; border-left: 4px solid #28a745; border-radius: 3px;"><p style="margin: 0;"><strong>📎 Full Report:</strong> See attached PDF for complete details</p></div>' if pdf_path else ''}
            </div>
            
            <div style="padding: 20px; background-color: #f8f9fa; border-top: 2px solid #dee2e6; margin-top: 20px;">
                <p style="margin: 0; color: #6c757d; font-size: 12px;">
                    Sent by Trishul Security Scanner • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(subject, html_body, pdf_path)
    
    def send_no_vulnerabilities(self, domain: str, elapsed_time: float) -> bool:
        """
        Send notification when scan completes with no vulnerabilities found.
        
        Args:
            domain: Target domain
            elapsed_time: Total scan duration in seconds
            
        Returns:
            True if sent successfully
        """
        return self.send_attack_completed(domain, elapsed_time, [], None)
    
    def send_attack_interrupted(self, domain: str, elapsed_time: float, current_phase: int) -> bool:
        """
        Send notification when attack is interrupted (Ctrl+C).
        
        Args:
            domain: Target domain
            elapsed_time: Time elapsed before interruption
            current_phase: Phase number where interruption occurred
            
        Returns:
            True if sent successfully
        """
        time_str = self._format_time(elapsed_time)
        subject = f"⚠️ Trishul: Attack Interrupted - {domain}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #ffc107; color: #000; padding: 20px; border-radius: 5px;">
                <h1 style="margin: 0;">⚠️ Attack Interrupted</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2 style="color: #ffc107;">Interruption Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6; width: 150px;"><strong>Target:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><code>{domain}</code></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6;"><strong>Runtime:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">{time_str}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6;"><strong>Phase:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">Phase {current_phase}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6;"><strong>Reason:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;">User interruption (Ctrl+C / KeyboardInterrupt)</td>
                    </tr>
                </table>
                
                <div style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 3px;">
                    <p style="margin: 0;"><strong>ℹ️ Note:</strong> Partial results may have been saved. Check the reports directory for any generated outputs.</p>
                </div>
            </div>
            
            <div style="padding: 20px; background-color: #f8f9fa; border-top: 2px solid #dee2e6; margin-top: 20px;">
                <p style="margin: 0; color: #6c757d; font-size: 12px;">
                    Sent by Trishul Security Scanner • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(subject, html_body)
    
    def send_stuck_alert(self, domain: str, phase_num: int, phase_name: str, stuck_duration: float) -> bool:
        """
        Send alert when a phase appears to be stuck.
        
        Args:
            domain: Target domain
            phase_num: Phase number that is stuck
            phase_name: Phase name
            stuck_duration: How long the phase has been stuck (seconds)
            
        Returns:
            True if sent successfully
        """
        time_str = self._format_time(stuck_duration)
        subject = f"🚨 Trishul: Phase Stuck Alert - {domain}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #dc3545; color: white; padding: 20px; border-radius: 5px;">
                <h1 style="margin: 0;">🚨 STUCK DETECTION ALERT</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2 style="color: #dc3545;">Phase Appears to be Stuck</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6; width: 150px;"><strong>Target:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><code>{domain}</code></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6;"><strong>Stuck Phase:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Phase {phase_num}: {phase_name}</strong></td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6;"><strong>Stuck Duration:</strong></td>
                        <td style="padding: 10px; border: 1px solid #dee2e6;"><strong style="color: #dc3545;">{time_str}</strong></td>
                    </tr>
                </table>
                
                <div style="margin-top: 30px; padding: 15px; background-color: #f8d7da; border-left: 4px solid #dc3545; border-radius: 3px;">
                    <p style="margin: 0;"><strong>⚠️ Action Required:</strong></p>
                    <ul style="margin: 10px 0 0 0;">
                        <li>Check if the scan is still running</li>
                        <li>Monitor system resources (CPU, memory, network)</li>
                        <li>Consider manually stopping and restarting the scan</li>
                        <li>Check logs for errors or timeouts</li>
                    </ul>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #d1ecf1; border-left: 4px solid #17a2b8; border-radius: 3px;">
                    <p style="margin: 0;"><strong>💡 Possible Causes:</strong></p>
                    <ul style="margin: 10px 0 0 0;">
                        <li>Target is very slow to respond</li>
                        <li>WAF/CDN is blocking requests</li>
                        <li>Network connectivity issues</li>
                        <li>Tool timeout or hang (e.g., Nuclei, Subfinder)</li>
                        <li>AI engine timeout (if applicable)</li>
                    </ul>
                </div>
            </div>
            
            <div style="padding: 20px; background-color: #f8f9fa; border-top: 2px solid #dee2e6; margin-top: 20px;">
                <p style="margin: 0; color: #6c757d; font-size: 12px;">
                    Sent by Trishul Security Scanner • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(subject, html_body)


# Singleton instance
_gmail_notifier = None


def get_notifier() -> GmailNotifier:
    """Get or create Gmail notifier singleton instance."""
    global _gmail_notifier
    if _gmail_notifier is None:
        _gmail_notifier = GmailNotifier()
    return _gmail_notifier


# Quick testing
if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("Gmail Notifier Test")
    print("=" * 60)
    
    notifier = get_notifier()
    
    if not notifier.enabled:
        print("\n❌ Gmail notifier is not configured.")
        print("\nTo configure:")
        print("1. Set EMAIL_USER environment variable (your Gmail address)")
        print("2. Set EMAIL_PASSWORD environment variable (Gmail app password)")
        print("3. Optionally set EMAIL_RECIPIENT (defaults to EMAIL_USER)")
        print("\nGmail App Password Setup:")
        print("1. Enable 2-factor authentication on your Gmail account")
        print("2. Go to: https://myaccount.google.com/apppasswords")
        print("3. Generate app password for 'Mail'")
        print("4. Use the 16-character password (not your regular password)")
        sys.exit(1)
    
    print(f"\n✅ Gmail configured: {notifier.email_user} → {notifier.email_recipient}")
    print("\nTesting notifications...\n")
    
    # Test target found notification
    print("1️⃣  Sending target found notification...")
    result = notifier.send_target_found(
        domain="example.com",
        program_url="https://hackerone.com/example",
        platform="HackerOne"
    )
    print(f"   {'✅ Sent' if result else '❌ Failed'}")
    
    time.sleep(1)
    
    # Test completion notification
    print("\n2️⃣  Sending completion notification...")
    test_vulns = [
        {'severity': 'critical', 'name': 'SQL Injection', 'matched-at': 'https://example.com/api'},
        {'severity': 'high', 'name': 'XSS', 'matched-at': 'https://example.com/search'},
        {'severity': 'medium', 'name': 'CSRF', 'matched-at': 'https://example.com/form'}
    ]
    result = notifier.send_attack_completed(
        domain="example.com",
        elapsed_time=3665,  # 1h 1m 5s
        vulns=test_vulns
    )
    print(f"   {'✅ Sent' if result else '❌ Failed'}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete! Check your inbox.")
    print("=" * 60)
