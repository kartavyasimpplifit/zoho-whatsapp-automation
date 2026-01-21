"""
Email Reporting Module
Sends daily reports and campaign approvals via email
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List
import os

logger = logging.getLogger(__name__)


class EmailReporter:
    """Handle email reporting and approvals"""
    
    def __init__(self, recipient_email: str, approval_base_url: str):
        """
        Initialize email reporter
        
        Args:
            recipient_email: Email to send reports to
            approval_base_url: Base URL for approval links
        """
        
        self.recipient_email = recipient_email
        self.approval_base_url = approval_base_url
        
        # Gmail SMTP settings (can be customized)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@automation.com')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
    
    def send_daily_report(self, cohorts: Dict) -> bool:
        """
        Send daily cohort analysis report with approval links
        
        Args:
            cohorts: Dictionary containing cohort analysis
            
        Returns:
            Success status
        """
        
        try:
            subject = f"📊 Daily WhatsApp Campaign Report - {datetime.now().strftime('%B %d, %Y')}"
            
            # Build HTML email
            html_content = self._build_daily_report_html(cohorts)
            
            # Send email
            return self._send_email(subject, html_content)
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
            return False
    
    def _build_daily_report_html(self, cohorts: Dict) -> str:
        """Build HTML content for daily report"""
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #1a73e8; }}
                h2 {{ color: #34a853; margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .btn {{ background-color: #1a73e8; color: white; padding: 12px 24px; 
                       text-decoration: none; border-radius: 4px; display: inline-block; 
                       margin: 10px 5px; }}
                .section {{ background-color: #f9f9f9; padding: 15px; margin: 15px 0; 
                          border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>📊 Daily WhatsApp Campaign Report</h1>
            <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
            
            <div class="section">
                <h2>📈 Lead Cohort Summary</h2>
                <table>
                    <tr>
                        <th>Cohort</th>
                        <th>Count</th>
                        <th>Action</th>
                    </tr>
                    <tr>
                        <td>Never Contacted</td>
                        <td>{len(cohorts.get('never_contacted', []))}</td>
                        <td><a href="{self.approval_base_url}/approve-campaign?segment=never_contacted&template=welcome" class="btn">Send Welcome</a></td>
                    </tr>
                    <tr>
                        <td>Received 1st Message</td>
                        <td>{len(cohorts.get('first_message', []))}</td>
                        <td><a href="{self.approval_base_url}/approve-campaign?segment=first_message&template=followup" class="btn">Send Follow-up</a></td>
                    </tr>
                    <tr>
                        <td>Received 2nd Message</td>
                        <td>{len(cohorts.get('second_message', []))}</td>
                        <td><a href="{self.approval_base_url}/approve-campaign?segment=second_message&template=offer" class="btn">Send Offer</a></td>
                    </tr>
                    <tr>
                        <td>Received 3+ Messages</td>
                        <td>{len(cohorts.get('third_plus_message', []))}</td>
                        <td>-</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <h2>📊 By Lead Status</h2>
                <table>
                    <tr>
                        <th>Status</th>
                        <th>Count</th>
                    </tr>
        """
        
        for status, leads in cohorts.get('by_status', {}).items():
            html += f"""
                    <tr>
                        <td>{status}</td>
                        <td>{len(leads)}</td>
                    </tr>
            """
        
        html += """
                </table>
            </div>
            
            <div class="section">
                <h2>🎯 By Lead Source</h2>
                <table>
                    <tr>
                        <th>Source</th>
                        <th>Count</th>
                    </tr>
        """
        
        for source, leads in cohorts.get('by_source', {}).items():
            html += f"""
                    <tr>
                        <td>{source}</td>
                        <td>{len(leads)}</td>
                    </tr>
            """
        
        html += f"""
                </table>
            </div>
            
            <div class="section">
                <h2>⭐ High Potential Leads</h2>
                <p>{len(cohorts.get('high_potential', []))} leads identified as high potential (Contacted/Qualified with less than 2 messages)</p>
                <a href="{self.approval_base_url}/approve-campaign?segment=high_potential&template=priority" class="btn">Send Priority Message</a>
            </div>
            
            <hr style="margin: 40px 0;">
            
            <p style="color: #666; font-size: 14px;">
                Click any button above to approve and send that campaign.<br>
                You'll receive a summary email after the campaign completes.
            </p>
            
            <p style="color: #999; font-size: 12px;">
                Generated by Zoho-WhatsApp Automation System<br>
                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </body>
        </html>
        """
        
        return html
    
    def send_campaign_summary(self, segment: str, template: str, results: Dict) -> bool:
        """
        Send campaign completion summary
        
        Args:
            segment: Segment targeted
            template: Template used
            results: Campaign results
            
        Returns:
            Success status
        """
        
        try:
            subject = f"✅ Campaign Complete: {segment}"
            
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #34a853; }}
                    .stat {{ background-color: #f9f9f9; padding: 15px; margin: 10px 0; 
                            border-radius: 5px; display: inline-block; width: 45%; }}
                    .stat-label {{ color: #666; font-size: 14px; }}
                    .stat-value {{ font-size: 32px; font-weight: bold; color: #1a73e8; }}
                </style>
            </head>
            <body>
                <h1>✅ Campaign Completed Successfully!</h1>
                
                <p><strong>Segment:</strong> {segment}</p>
                <p><strong>Template:</strong> {template}</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <hr>
                
                <div class="stat">
                    <div class="stat-label">Total Sent</div>
                    <div class="stat-value">{results.get('total', 0)}</div>
                </div>
                
                <div class="stat">
                    <div class="stat-label">Successful</div>
                    <div class="stat-value" style="color: #34a853;">{results.get('success', 0)}</div>
                </div>
                
                <div class="stat">
                    <div class="stat-label">Failed</div>
                    <div class="stat-value" style="color: #ea4335;">{results.get('failed', 0)}</div>
                </div>
                
                <div class="stat">
                    <div class="stat-label">Success Rate</div>
                    <div class="stat-value">{round(results.get('success', 0) / max(results.get('total', 1), 1) * 100, 1)}%</div>
                </div>
                
                <hr style="margin: 30px 0;">
                
                <p style="color: #666;">
                    All successful sends have been tracked in Google Sheets and updated in Zoho CRM with notes.
                </p>
                
                <p style="color: #999; font-size: 12px;">
                    Zoho-WhatsApp Automation System
                </p>
            </body>
            </html>
            """
            
            return self._send_email(subject, html)
            
        except Exception as e:
            logger.error(f"Error sending campaign summary: {e}")
            return False
    
    def _send_email(self, subject: str, html_content: str) -> bool:
        """
        Send an email
        
        Args:
            subject: Email subject
            html_content: HTML email body
            
        Returns:
            Success status
        """
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.sender_password:
                    server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {self.recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            # Log but don't fail - email is not critical
            return False
