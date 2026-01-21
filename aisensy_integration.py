"""
AiSensy WhatsApp Integration Module
Handles all WhatsApp message sending via AiSensy API
"""

import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AiSensyIntegration:
    """Handle AiSensy WhatsApp API operations"""
    
    def __init__(self, api_key: str, campaign_name: str):
        self.api_key = api_key
        self.campaign_name = campaign_name
        self.base_url = "https://backend.aisensy.com/campaign/t1/api/v2"
    
    def send_message(self, 
                    phone: str,
                    name: str,
                    template_params: List[str] = None,
                    tags: List[str] = None,
                    attributes: Dict = None) -> Dict:
        """
        Send WhatsApp message via AiSensy
        
        Args:
            phone: Phone number with country code
            name: Customer name
            template_params: Template parameter values
            tags: Tags to add to contact
            attributes: Custom attributes
            
        Returns:
            Result dictionary with success status
        """
        
        # Ensure phone has country code
        if not phone.startswith('+'):
            if phone.startswith('91'):
                phone = '+' + phone
            elif len(phone) == 10:
                phone = '+91' + phone
        
        payload = {
            "apiKey": self.api_key,
            "campaignName": self.campaign_name,
            "destination": phone,
            "userName": name,
            "source": "Zoho CRM Automation"
        }
        
        if template_params:
            payload["templateParams"] = template_params
        
        if tags:
            payload["tags"] = tags
        
        if attributes:
            payload["attributes"] = attributes
        
        try:
            response = requests.post(
                self.base_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"WhatsApp sent successfully to {phone}")
                return {
                    "success": True,
                    "phone": phone,
                    "name": name
                }
            else:
                logger.error(f"Failed to send WhatsApp to {phone}: {response.text}")
                return {
                    "success": False,
                    "phone": phone,
                    "name": name,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp to {phone}: {e}")
            return {
                "success": False,
                "phone": phone,
                "name": name,
                "error": str(e)
            }
