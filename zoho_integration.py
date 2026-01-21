"""
Zoho CRM Integration Module
Handles all Zoho CRM API interactions
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ZohoIntegration:
    """Handle Zoho CRM API operations"""
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str, domain: str = "zoho.in"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.domain = domain
        self.access_token = None
        self.token_expiry = None
        
        # API endpoints
        self.auth_url = f"https://accounts.{domain}/oauth/v2/token"
        self.api_base = f"https://www.zohoapis.{domain}/crm/v3"
    
    def get_access_token(self) -> str:
        """Get or refresh access token"""
        
        # Check if existing token is still valid
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token
        
        # Get new access token
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        
        try:
            response = requests.post(self.auth_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                
                # Set expiry (usually 1 hour)
                expires_in = data.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                
                logger.info("Access token refreshed successfully")
                return self.access_token
            else:
                logger.error(f"Failed to get access token: {response.text}")
                raise Exception(f"Token refresh failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            raise
    
    def get_all_leads(self, fields: List[str] = None) -> List[Dict]:
        """
        Get all leads from Zoho CRM
        
        Args:
            fields: Specific fields to retrieve
            
        Returns:
            List of lead records
        """
        
        if fields is None:
            fields = ["First_Name", "Last_Name", "Phone", "Mobile", "Email",
                     "Lead_Status", "Lead_Source", "Company", "id"]
        
        return self._get_records("Leads", fields=fields)
    
    def get_lead_by_id(self, lead_id: str) -> Optional[Dict]:
        """
        Get a specific lead by ID
        
        Args:
            lead_id: Zoho lead ID
            
        Returns:
            Lead record or None
        """
        
        token = self.get_access_token()
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}"
        }
        
        url = f"{self.api_base}/Leads/{lead_id}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching lead {lead_id}: {e}")
            return None
    
    def _get_records(self, module: str, criteria: str = None, fields: List[str] = None) -> List[Dict]:
        """
        Generic method to get records from any Zoho module
        
        Args:
            module: Zoho module name (Leads, Contacts, Deals, etc.)
            criteria: Search criteria
            fields: Fields to retrieve
            
        Returns:
            List of records
        """
        
        token = self.get_access_token()
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}"
        }
        
        url = f"{self.api_base}/{module}"
        
        params = {}
        if criteria:
            params["criteria"] = criteria
        if fields:
            params["fields"] = ",".join(fields)
        
        all_records = []
        page = 1
        per_page = 200
        
        while True:
            params["page"] = page
            params["per_page"] = per_page
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "data" in data:
                        records = data["data"]
                        all_records.extend(records)
                        
                        # Check if more pages
                        if len(records) < per_page:
                            break
                        
                        page += 1
                    else:
                        break
                else:
                    logger.error(f"Error fetching {module}: {response.text}")
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching {module} page {page}: {e}")
                break
        
        logger.info(f"Fetched {len(all_records)} records from {module}")
        return all_records
    
    def add_note(self, lead_id: str, note_title: str, note_content: str) -> bool:
        """
        Add a note to a lead
        
        Args:
            lead_id: Lead ID
            note_title: Note title
            note_content: Note content
            
        Returns:
            Success status
        """
        
        token = self.get_access_token()
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_base}/Notes"
        
        payload = {
            "data": [{
                "Note_Title": note_title,
                "Note_Content": note_content,
                "Parent_Id": lead_id,
                "se_module": "Leads"
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"Note added to lead {lead_id}")
                return True
            else:
                logger.error(f"Failed to add note: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding note: {e}")
            return False
    
    def update_lead(self, lead_id: str, data: Dict) -> bool:
        """
        Update a lead record
        
        Args:
            lead_id: Lead ID
            data: Data to update
            
        Returns:
            Success status
        """
        
        token = self.get_access_token()
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_base}/Leads/{lead_id}"
        
        payload = {
            "data": [data]
        }
        
        try:
            response = requests.put(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Lead {lead_id} updated successfully")
                return True
            else:
                logger.error(f"Failed to update lead: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating lead: {e}")
            return False
