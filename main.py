#!/usr/bin/env python3
"""
Zoho CRM to WhatsApp Automation - Main Application
Handles webhooks, scheduled tasks, and orchestration
"""

from flask import Flask, request, jsonify
import os
import logging
from datetime import datetime, timedelta
import threading
import time

from zoho_integration import ZohoIntegration
from aisensy_integration import AiSensyIntegration
from sheets_tracker import SheetsTracker
from email_reports import EmailReporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize integrations
zoho = ZohoIntegration(
    client_id=os.getenv('ZOHO_CLIENT_ID'),
    client_secret=os.getenv('ZOHO_CLIENT_SECRET'),
    refresh_token=os.getenv('ZOHO_REFRESH_TOKEN'),
    domain=os.getenv('ZOHO_DOMAIN', 'zoho.in')
)

aisensy = AiSensyIntegration(
    api_key=os.getenv('AISENSY_API_KEY'),
    campaign_name=os.getenv('AISENSY_CAMPAIGN_NAME')
)

sheets = SheetsTracker(
    credentials_json=os.getenv('GOOGLE_CREDENTIALS_JSON'),
    spreadsheet_url=os.getenv('GOOGLE_SHEET_URL')
)

email_reporter = EmailReporter(
    recipient_email=os.getenv('REPORT_EMAIL'),
    approval_base_url=os.getenv('APPROVAL_BASE_URL')
)


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Zoho-WhatsApp Automation'
    })


@app.route('/check-new-leads', methods=['GET', 'POST'])
def check_new_leads():
    """Check for new leads and send WhatsApp (Polling Mode)"""
    try:
        logger.info("Checking for new leads...")
        
        # Get all leads
        all_leads = zoho.get_all_leads()
        
        # Get message history
        message_history = sheets.get_all_messages()
        messaged_lead_ids = set(str(msg.get('Lead ID')) for msg in message_history if msg.get('Lead ID'))
        
        # Find new leads (not yet messaged)
        new_leads = [lead for lead in all_leads if str(lead.get('id')) not in messaged_lead_ids]
        
        results = {
            'checked': len(all_leads),
            'new_found': len(new_leads),
            'sent': 0,
            'failed': 0
        }
        
        template_name = os.getenv('NEW_LEAD_TEMPLATE')
        
        if not template_name:
            logger.warning("NEW_LEAD_TEMPLATE not configured")
            return jsonify({'status': 'success', 'message': 'Template not configured', 'results': results}), 200
        
        # Process new leads (limit to 10 per check)
        for lead in new_leads[:10]:
            lead_id = lead.get('id')
            name = f"{lead.get('First_Name', '')} {lead.get('Last_Name', '')}".strip()
            phone = lead.get('Phone') or lead.get('Mobile')
            status = lead.get('Lead_Status', 'Unknown')
            source = lead.get('Lead_Source', 'Unknown')
            
            if not phone:
                logger.warning(f"Lead {lead_id} has no phone")
                results['failed'] += 1
                continue
            
            # Send WhatsApp
            result = aisensy.send_message(
                phone=phone,
                name=name,
                template_params=[],
                tags=['auto', status, source]
            )
            
            if result['success']:
                results['sent'] += 1
                
                # Track in sheets
                sheets.log_message(
                    lead_id=lead_id,
                    name=name,
                    phone=phone,
                    status=status,
                    source=source,
                    template=template_name,
                    message_count=1,
                    result='success',
                    campaign_type='auto'
                )
                
                # Update Zoho
                zoho.add_note(
                    lead_id=lead_id,
                    note_title="WhatsApp Sent - Auto",
                    note_content=f"Sent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nTemplate: {template_name}"
                )
                
                logger.info(f"WhatsApp sent to lead {lead_id}")
            else:
                results['failed'] += 1
                logger.error(f"Failed to send WhatsApp to lead {lead_id}")
            
            # Rate limiting
            time.sleep(2)
        
        logger.info(f"Check complete: {results}")
        return jsonify({'status': 'success', 'results': results}), 200
        
    except Exception as e:
        logger.error(f"Error checking new leads: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/webhook/zoho', methods=['POST'])
def zoho_webhook():
    """Webhook endpoint for Zoho CRM (if available)"""
    try:
        data = request.json
        logger.info(f"Received Zoho webhook: {data}")
        
        lead_id = data.get('id')
        lead_status = data.get('Lead_Status')
        lead_source = data.get('Lead_Source')
        
        process_new_lead(lead_id, lead_status, lead_source)
        
        return jsonify({'status': 'success', 'message': 'Lead processed'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def process_new_lead(lead_id, lead_status, lead_source):
    """Process a new lead from webhook"""
    try:
        logger.info(f"Processing new lead: {lead_id}")
        
        lead = zoho.get_lead_by_id(lead_id)
        
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return
        
        name = f"{lead.get('First_Name', '')} {lead.get('Last_Name', '')}".strip()
        phone = lead.get('Phone') or lead.get('Mobile')
        
        if not phone:
            logger.warning(f"Lead {lead_id} has no phone number")
            return
        
        template_name = os.getenv('NEW_LEAD_TEMPLATE')
        
        if not template_name:
            logger.warning("NEW_LEAD_TEMPLATE not configured")
            return
        
        result = aisensy.send_message(
            phone=phone,
            name=name,
            template_params=[],
            tags=['new_lead', lead_status, lead_source]
        )
        
        if result['success']:
            sheets.log_message(
                lead_id=lead_id,
                name=name,
                phone=phone,
                status=lead_status,
                source=lead_source,
                template=template_name,
                message_count=1,
                result='success',
                campaign_type='auto'
            )
            
            zoho.add_note(
                lead_id=lead_id,
                note_title="WhatsApp Sent - Auto",
                note_content=f"WhatsApp sent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nTemplate: {template_name}\nStatus: Delivered"
            )
            
            logger.info(f"Successfully processed lead {lead_id}")
        else:
            logger.error(f"Failed to send WhatsApp to lead {lead_id}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error processing new lead {lead_id}: {e}")


@app.route('/daily-report', methods=['POST'])
def trigger_daily_report():
    """Manually trigger daily report"""
    try:
        generate_daily_report()
        return jsonify({'status': 'success', 'message': 'Report generated'}), 200
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def generate_daily_report():
    """Generate and send daily cohort analysis report"""
    try:
        logger.info("Generating daily report...")
        
        leads = zoho.get_all_leads()
        message_history = sheets.get_all_messages()
        cohorts = analyze_cohorts(leads, message_history)
        email_reporter.send_daily_report(cohorts)
        
        logger.info("Daily report sent successfully")
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise


def analyze_cohorts(leads, message_history):
    """Analyze leads into cohorts"""
    cohorts = {
        'never_contacted': [],
        'first_message': [],
        'second_message': [],
        'third_plus_message': [],
        'by_status': {},
        'by_source': {},
        'high_potential': []
    }
    
    message_counts = {}
    for msg in message_history:
        lead_id = str(msg.get('Lead ID'))
        if lead_id:
            message_counts[lead_id] = message_counts.get(lead_id, 0) + 1
    
    for lead in leads:
        lead_id = str(lead.get('id'))
        count = message_counts.get(lead_id, 0)
        status = lead.get('Lead_Status', 'Unknown')
        source = lead.get('Lead_Source', 'Unknown')
        
        if count == 0:
            cohorts['never_contacted'].append(lead)
        elif count == 1:
            cohorts['first_message'].append(lead)
        elif count == 2:
            cohorts['second_message'].append(lead)
        else:
            cohorts['third_plus_message'].append(lead)
        
        if status not in cohorts['by_status']:
            cohorts['by_status'][status] = []
        cohorts['by_status'][status].append(lead)
        
        if source not in cohorts['by_source']:
            cohorts['by_source'][source] = []
        cohorts['by_source'][source].append(lead)
        
        if status in ['Contacted', 'Qualified'] and count < 2:
            cohorts['high_potential'].append(lead)
    
    return cohorts


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
