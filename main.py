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


@app.route('/webhook/zoho', methods=['POST'])
def zoho_webhook():
    """
    Webhook endpoint for Zoho CRM
    Triggered when new lead is created
    """
    try:
        data = request.json
        logger.info(f"Received Zoho webhook: {data}")
        
        # Extract lead data
        lead_id = data.get('id')
        lead_status = data.get('Lead_Status')
        lead_source = data.get('Lead_Source')
        
        # Process new lead
        process_new_lead(lead_id, lead_status, lead_source)
        
        return jsonify({'status': 'success', 'message': 'Lead processed'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


def process_new_lead(lead_id, lead_status, lead_source):
    """Process a new lead from webhook"""
    try:
        logger.info(f"Processing new lead: {lead_id}")
        
        # Get full lead details from Zoho
        lead = zoho.get_lead_by_id(lead_id)
        
        if not lead:
            logger.error(f"Lead {lead_id} not found")
            return
        
        # Extract details
        name = f"{lead.get('First_Name', '')} {lead.get('Last_Name', '')}".strip()
        phone = lead.get('Phone') or lead.get('Mobile')
        
        if not phone:
            logger.warning(f"Lead {lead_id} has no phone number")
            return
        
        # Check if lead should receive WhatsApp
        template_name = os.getenv('NEW_LEAD_TEMPLATE')
        
        if not template_name:
            logger.warning("NEW_LEAD_TEMPLATE not configured")
            return
        
        # Send WhatsApp
        result = aisensy.send_message(
            phone=phone,
            name=name,
            template_params=[],  # Add template params if needed
            tags=['new_lead', lead_status, lead_source]
        )
        
        if result['success']:
            # Update tracking
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
            
            # Update Zoho with note
            zoho.add_note(
                lead_id=lead_id,
                note_title="WhatsApp Sent - Auto",
                note_content=f"WhatsApp message sent automatically on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nTemplate: {template_name}\nStatus: Delivered"
            )
            
            logger.info(f"Successfully processed lead {lead_id}")
        else:
            logger.error(f"Failed to send WhatsApp to lead {lead_id}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error processing new lead {lead_id}: {e}")


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
        new_leads = [lead for lead in all_leads 
                    if str(lead.get('id')) not in messaged_lead_ids]
        
        results = {
            'checked': len(all_leads),
            'new_found': len(new_leads),
            'sent': 0,
            'failed': 0
        }
        
        template_name = os.getenv('NEW_LEAD_TEMPLATE')
        
        if not template_name:
            logger.warning("NEW_LEAD_TEMPLATE not configured")
            return jsonify({'status': 'error', 'message': 'Template not configured', 'results': results}), 200
        
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


@app.route('/daily-report', methods=['POST'])
def trigger_daily_report():
    """Manually trigger daily report (also runs on schedule)"""
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
        
        # Get all leads from Zoho
        leads = zoho.get_all_leads()
        
        # Get message history from Sheets
        message_history = sheets.get_all_messages()
        
        # Perform cohort analysis
        cohorts = analyze_cohorts(leads, message_history)
        
        # Generate and send report
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
    
    # Create message count lookup
    message_counts = {}
    for msg in message_history:
        lead_id = str(msg.get('Lead ID'))
        if lead_id:
            message_counts[lead_id] = message_counts.get(lead_id, 0) + 1
    
    # Categorize leads
    for lead in leads:
        lead_id = str(lead.get('id'))
        count = message_counts.get(lead_id, 0)
        status = lead.get('Lead_Status', 'Unknown')
        source = lead.get('Lead_Source', 'Unknown')
        
        # Add to count cohorts
        if count == 0:
            cohorts['never_contacted'].append(lead)
        elif count == 1:
            cohorts['first_message'].append(lead)
        elif count == 2:
            cohorts['second_message'].append(lead)
        else:
            cohorts['third_plus_message'].append(lead)
        
        # Add to status cohorts
        if status not in cohorts['by_status']:
            cohorts['by_status'][status] = []
        cohorts['by_status'][status].append(lead)
        
        # Add to source cohorts
        if source not in cohorts['by_source']:
            cohorts['by_source'][source] = []
        cohorts['by_source'][source].append(lead)
        
        # Identify high potential (customize logic)
        if status in ['Contacted', 'Qualified'] and count < 2:
            cohorts['high_potential'].append(lead)
    
    return cohorts


@app.route('/approve-campaign', methods=['GET'])
def approve_campaign():
    """Handle campaign approval from email link"""
    try:
        campaign_id = request.args.get('campaign_id')
        segment = request.args.get('segment')
        template = request.args.get('template')
        
        if not all([campaign_id, segment, template]):
            return jsonify({'error': 'Missing parameters'}), 400
        
        # Execute approved campaign
        execute_campaign(segment, template)
        
        return """
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: green;">✅ Campaign Approved!</h1>
            <p>Your WhatsApp campaign is being sent now.</p>
            <p>You'll receive a summary email shortly.</p>
        </body>
        </html>
        """
        
    except Exception as e:
        logger.error(f"Approval error: {e}")
        return f"<html><body><h1>Error: {e}</h1></body></html>", 500


def execute_campaign(segment, template):
    """Execute an approved campaign"""
    try:
        logger.info(f"Executing campaign for segment: {segment}, template: {template}")
        
        # Get leads for segment
        leads = get_leads_for_segment(segment)
        
        results = {
            'total': len(leads),
            'success': 0,
            'failed': 0
        }
        
        for lead in leads:
            lead_id = lead.get('id')
            name = f"{lead.get('First_Name', '')} {lead.get('Last_Name', '')}".strip()
            phone = lead.get('Phone') or lead.get('Mobile')
            
            if not phone:
                results['failed'] += 1
                continue
            
            # Send message
            result = aisensy.send_message(
                phone=phone,
                name=name,
                template_params=[],
                tags=['campaign', segment]
            )
            
            if result['success']:
                results['success'] += 1
                
                # Get current message count
                current_count = sheets.get_message_count(lead_id) + 1
                
                # Track in sheets
                sheets.log_message(
                    lead_id=lead_id,
                    name=name,
                    phone=phone,
                    status=lead.get('Lead_Status'),
                    source=lead.get('Lead_Source'),
                    template=template,
                    message_count=current_count,
                    result='success',
                    campaign_type='manual'
                )
                
                # Update Zoho
                zoho.add_note(
                    lead_id=lead_id,
                    note_title=f"WhatsApp Campaign - Message #{current_count}",
                    note_content=f"Campaign sent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nTemplate: {template}\nSegment: {segment}"
                )
            else:
                results['failed'] += 1
            
            # Rate limiting
            time.sleep(1.5)
        
        logger.info(f"Campaign complete: {results}")
        
        # Send summary email
        email_reporter.send_campaign_summary(segment, template, results)
        
    except Exception as e:
        logger.error(f"Campaign execution error: {e}")
        raise


def get_leads_for_segment(segment):
    """Get leads matching segment criteria"""
    all_leads = zoho.get_all_leads()
    message_history = sheets.get_all_messages()
    
    message_counts = {}
    for msg in message_history:
        lead_id = str(msg.get('Lead ID'))
        if lead_id:
            message_counts[lead_id] = message_counts.get(lead_id, 0) + 1
    
    if segment == 'never_contacted':
        return [l for l in all_leads if message_counts.get(str(l.get('id')), 0) == 0]
    elif segment == 'first_message':
        return [l for l in all_leads if message_counts.get(str(l.get('id')), 0) == 1]
    elif segment.startswith('status:'):
        status = segment.split(':')[1]
        return [l for l in all_leads if l.get('Lead_Status') == status]
    elif segment.startswith('source:'):
        source = segment.split(':')[1]
        return [l for l in all_leads if l.get('Lead_Source') == source]
    else:
        return []


def scheduled_tasks():
    """Background thread for scheduled tasks"""
    while True:
        try:
            # Get current time
            now = datetime.now()
            
            # Run daily report at 9 AM
            if now.hour == 9 and now.minute == 0:
                logger.info("Running scheduled daily report...")
                generate_daily_report()
                time.sleep(60)  # Prevent multiple runs in same minute
            
            # Sleep for 60 seconds before next check
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"Scheduled task error: {e}")
            time.sleep(60)


if __name__ == '__main__':
    # Start background scheduler in separate thread
    scheduler_thread = threading.Thread(target=scheduled_tasks, daemon=True)
    scheduler_thread.start()
    
    # Run Flask app
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
