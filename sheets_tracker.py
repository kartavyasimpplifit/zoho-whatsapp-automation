"""
Google Sheets Tracker Module
Tracks all WhatsApp messages sent in Google Sheets
"""

import logging
from datetime import datetime
from typing import List, Dict
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger(__name__)


class SheetsTracker:
    """Handle Google Sheets tracking operations"""
    
    def __init__(self, credentials_json: str, spreadsheet_url: str):
        """
        Initialize Sheets tracker
        
        Args:
            credentials_json: JSON string of service account credentials
            spreadsheet_url: Google Sheets URL
        """
        
        # Parse credentials
        creds_dict = json.loads(credentials_json)
        
        # Setup credentials
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        
        # Authorize and open sheet
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_url(spreadsheet_url)
        
        # Initialize worksheets
        self._initialize_sheets()
    
    def _initialize_sheets(self):
        """Create necessary worksheets if they don't exist"""
        
        try:
            # Message Log sheet
            try:
                self.message_log = self.spreadsheet.worksheet("Message Log")
            except:
                self.message_log = self.spreadsheet.add_worksheet("Message Log", 1000, 15)
                headers = [
                    "Timestamp", "Lead ID", "Name", "Phone", "Lead Status",
                    "Lead Source", "Template", "Message Count", "Result",
                    "Campaign Type", "Notes"
                ]
                self.message_log.append_row(headers)
            
            # Summary sheet
            try:
                self.summary = self.spreadsheet.worksheet("Summary")
            except:
                self.summary = self.spreadsheet.add_worksheet("Summary", 100, 10)
                headers = [
                    "Date", "Total Sent", "Success", "Failed", "New Leads",
                    "Follow-ups", "Campaign Type"
                ]
                self.summary.append_row(headers)
            
            logger.info("Sheets initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing sheets: {e}")
            raise
    
    def log_message(self,
                   lead_id: str,
                   name: str,
                   phone: str,
                   status: str,
                   source: str,
                   template: str,
                   message_count: int,
                   result: str,
                   campaign_type: str = "manual",
                   notes: str = "") -> bool:
        """
        Log a message to the tracking sheet
        
        Args:
            lead_id: Zoho lead ID
            name: Customer name
            phone: Phone number
            status: Lead status
            source: Lead source
            template: Template name used
            message_count: Message number for this lead (1, 2, 3, etc.)
            result: 'success' or 'failed'
            campaign_type: 'auto' or 'manual'
            notes: Additional notes
            
        Returns:
            Success status
        """
        
        try:
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                lead_id,
                name,
                phone,
                status,
                source,
                template,
                message_count,
                result,
                campaign_type,
                notes
            ]
            
            self.message_log.append_row(row)
            logger.info(f"Message logged for lead {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging message: {e}")
            return False
    
    def get_all_messages(self) -> List[Dict]:
        """
        Get all messages from the log
        
        Returns:
            List of message records
        """
        
        try:
            records = self.message_log.get_all_records()
            return records
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def get_message_count(self, lead_id: str) -> int:
        """
        Get message count for a specific lead
        
        Args:
            lead_id: Zoho lead ID
            
        Returns:
            Number of messages sent to this lead
        """
        
        try:
            records = self.get_all_messages()
            count = sum(1 for r in records if str(r.get('Lead ID')) == str(lead_id))
            return count
            
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            return 0
    
    def update_daily_summary(self, 
                            total_sent: int,
                            success: int,
                            failed: int,
                            new_leads: int,
                            follow_ups: int,
                            campaign_type: str) -> bool:
        """
        Update daily summary
        
        Args:
            total_sent: Total messages sent today
            success: Successful sends
            failed: Failed sends
            new_leads: Messages to new leads
            follow_ups: Follow-up messages
            campaign_type: Type of campaign
            
        Returns:
            Success status
        """
        
        try:
            row = [
                datetime.now().strftime("%Y-%m-%d"),
                total_sent,
                success,
                failed,
                new_leads,
                follow_ups,
                campaign_type
            ]
            
            self.summary.append_row(row)
            logger.info("Daily summary updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating summary: {e}")
            return False
