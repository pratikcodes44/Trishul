"""
DNS Deep Analyzer
Extracts comprehensive DNS records beyond basic A records
"""

import dns.resolver
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class DNSAnalyzer:
    """
    Perform deep DNS reconnaissance.
    Extracts MX, TXT, NS, CAA, SOA records for infrastructure mapping.
    """
    
    def __init__(self):
        self.record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CAA', 'SOA', 'CNAME']
    
    def analyze(self, domain: str) -> Dict:
        """
        Perform comprehensive DNS analysis.
        
        Args:
            domain: Target domain
        
        Returns:
            Dictionary of DNS records by type
        """
        records = {}
        
        logger.info(f"🔍 Performing DNS deep dive on {domain}...")
        
        for record_type in self.record_types:
            try:
                answers = dns.resolver.resolve(domain, record_type)
                records[record_type.lower()] = []
                
                for rdata in answers:
                    if record_type == 'MX':
                        records[record_type.lower()].append({
                            'priority': rdata.preference,
                            'server': str(rdata.exchange)
                        })
                    elif record_type == 'TXT':
                        # TXT records often contain SPF, DKIM, verification tokens
                        txt_value = str(rdata).strip('"')
                        records[record_type.lower()].append(txt_value)
                    elif record_type == 'SOA':
                        records[record_type.lower()].append({
                            'mname': str(rdata.mname),
                            'rname': str(rdata.rname),
                            'serial': rdata.serial,
                        })
                    else:
                        records[record_type.lower()].append(str(rdata))
                
                logger.debug(f"✓ Found {len(records[record_type.lower()])} {record_type} record(s)")
                
            except dns.resolver.NoAnswer:
                logger.debug(f"No {record_type} records found for {domain}")
            except dns.resolver.NXDOMAIN:
                logger.warning(f"Domain {domain} does not exist")
                break
            except Exception as e:
                logger.debug(f"DNS query failed for {record_type}: {e}")
        
        # Log summary
        total_records = sum(len(v) if isinstance(v, list) else 1 for v in records.values())
        logger.info(f"✅ DNS Analysis: Extracted {total_records} records across {len(records)} types")
        
        return records
    
    def extract_emails_from_dns(self, records: Dict) -> List[str]:
        """
        Extract potential email addresses from DNS records.
        Often found in SOA and TXT records.
        """
        emails = []
        
        # From SOA records
        if 'soa' in records:
            for soa in records['soa']:
                if isinstance(soa, dict) and 'rname' in soa:
                    # SOA rname format: hostmaster.example.com -> hostmaster@example.com
                    rname = soa['rname'].replace('.', '@', 1)
                    emails.append(rname)
        
        # From TXT records (sometimes contain contact info)
        if 'txt' in records:
            for txt in records['txt']:
                # Look for email patterns in TXT records
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                found_emails = re.findall(email_pattern, txt)
                emails.extend(found_emails)
        
        return list(set(emails))  # Remove duplicates
