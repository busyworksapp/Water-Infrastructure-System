from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime
import json
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models.system import NotificationChannel, NotificationChannelType
from ..models.alert import Alert
from ..models.user import User

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.retry_config = {
            'stop': stop_after_attempt(3),
            'wait': wait_exponential(multiplier=1, min=2, max=10)
        }
    
    def send_alert_notification(self, alert: Alert):
        """Send alert through all configured channels with retry logic"""
        channels = self.db.query(NotificationChannel).filter(
            NotificationChannel.municipality_id == alert.municipality_id,
            NotificationChannel.is_active == True
        ).all()
        
        if not channels:
            logger.warning(f"No active notification channels for municipality {alert.municipality_id}")
            return
        
        success_count = 0
        for channel in channels:
            try:
                if channel.channel_type == NotificationChannelType.EMAIL:
                    self._send_email_with_retry(channel, alert)
                elif channel.channel_type == NotificationChannelType.SMS:
                    self._send_sms_with_retry(channel, alert)
                elif channel.channel_type == NotificationChannelType.WEBHOOK:
                    self._send_webhook_with_retry(channel, alert)
                elif channel.channel_type == NotificationChannelType.SLACK:
                    self._send_slack_with_retry(channel, alert)
                elif channel.channel_type == NotificationChannelType.PUSH:
                    self._send_push_notification(channel, alert)
                success_count += 1
            except Exception as e:
                logger.error(f"Notification failed for channel {channel.id} ({channel.channel_type.value}): {e}")
        
        logger.info(f"Alert {alert.id} sent to {success_count}/{len(channels)} channels")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _send_email_with_retry(self, channel: NotificationChannel, alert: Alert):
        self._send_email(channel, alert)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _send_sms_with_retry(self, channel: NotificationChannel, alert: Alert):
        self._send_sms(channel, alert)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _send_webhook_with_retry(self, channel: NotificationChannel, alert: Alert):
        self._send_webhook(channel, alert)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _send_slack_with_retry(self, channel: NotificationChannel, alert: Alert):
        self._send_slack(channel, alert)
    
    def _send_email(self, channel: NotificationChannel, alert: Alert):
        """Send email notification with HTML template"""
        config = channel.config
        
        if not all(k in config for k in ['smtp_host', 'from_email', 'to_email']):
            raise ValueError("Missing required email configuration")
        
        msg = MIMEMultipart('alternative')
        msg['From'] = config['from_email']
        msg['To'] = config['to_email']
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        msg['X-Priority'] = '1' if alert.severity.value in ['critical', 'high'] else '3'
        
        # Plain text version
        text = f"""
Water Infrastructure Alert

Alert: {alert.title}
Severity: {alert.severity.value.upper()}
Type: {alert.alert_type.value}
Description: {alert.description}
Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
Location: {alert.location or 'N/A'}

Please check the control room for details.

This is an automated message from the National Water Infrastructure Monitoring System.
        """
        
        # HTML version
        severity_color = {
            'critical': '#d32f2f',
            'high': '#f57c00',
            'medium': '#fbc02d',
            'low': '#388e3c',
            'info': '#1976d2'
        }.get(alert.severity.value, '#757575')
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
              <h2 style="color: {severity_color}; border-bottom: 2px solid {severity_color}; padding-bottom: 10px;">
                🚨 Water Infrastructure Alert
              </h2>
              <table style="width: 100%; border-collapse: collapse;">
                <tr>
                  <td style="padding: 8px; font-weight: bold; width: 120px;">Alert:</td>
                  <td style="padding: 8px;">{alert.title}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                  <td style="padding: 8px; font-weight: bold;">Severity:</td>
                  <td style="padding: 8px; color: {severity_color}; font-weight: bold;">{alert.severity.value.upper()}</td>
                </tr>
                <tr>
                  <td style="padding: 8px; font-weight: bold;">Type:</td>
                  <td style="padding: 8px;">{alert.alert_type.value}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                  <td style="padding: 8px; font-weight: bold;">Description:</td>
                  <td style="padding: 8px;">{alert.description}</td>
                </tr>
                <tr>
                  <td style="padding: 8px; font-weight: bold;">Time:</td>
                  <td style="padding: 8px;">{alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                  <td style="padding: 8px; font-weight: bold;">Location:</td>
                  <td style="padding: 8px;">{alert.location or 'N/A'}</td>
                </tr>
              </table>
              <p style="margin-top: 20px; padding: 15px; background-color: #e3f2fd; border-left: 4px solid #1976d2;">
                Please check the control room for detailed information and take appropriate action.
              </p>
              <p style="font-size: 12px; color: #757575; margin-top: 20px; border-top: 1px solid #ddd; padding-top: 10px;">
                This is an automated message from the National Water Infrastructure Monitoring System.
              </p>
            </div>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        
        smtp_port = int(config.get('smtp_port', 587))
        use_tls = config.get('use_tls', True)
        
        with smtplib.SMTP(config['smtp_host'], smtp_port, timeout=30) as server:
            if use_tls:
                server.starttls()
            if config.get('username') and config.get('password'):
                server.login(config['username'], config['password'])
            server.send_message(msg)
        
        logger.info(f"Email sent for alert {alert.id} to {config['to_email']}")
    
    def _send_sms(self, channel: NotificationChannel, alert: Alert):
        """Send SMS notification via Twilio or Africa's Talking"""
        config = channel.config
        provider = config.get('provider', 'twilio').lower()
        
        message = f"[{alert.severity.value.upper()}] {alert.title}: {alert.description[:100]}"
        
        if provider == 'twilio':
            if not all(k in config for k in ['account_sid', 'auth_token', 'from_number', 'to_number']):
                raise ValueError("Missing Twilio configuration")
            
            response = requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{config['account_sid']}/Messages.json",
                auth=(config['account_sid'], config['auth_token']),
                data={
                    'To': config['to_number'],
                    'From': config['from_number'],
                    'Body': message
                },
                timeout=30
            )
            
            if response.status_code == 201:
                logger.info(f"SMS sent via Twilio for alert {alert.id}")
            else:
                raise Exception(f"Twilio API error: {response.status_code} - {response.text}")
        
        elif provider == 'africas_talking':
            if not all(k in config for k in ['api_key', 'username', 'from_number', 'to_number']):
                raise ValueError("Missing Africa's Talking configuration")
            
            response = requests.post(
                'https://api.africastalking.com/version1/messaging',
                headers={
                    'apiKey': config['api_key'],
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                data={
                    'username': config['username'],
                    'to': config['to_number'],
                    'from': config.get('from_number'),
                    'message': message
                },
                timeout=30
            )
            
            if response.status_code == 201:
                logger.info(f"SMS sent via Africa's Talking for alert {alert.id}")
            else:
                raise Exception(f"Africa's Talking API error: {response.status_code}")
        
        else:
            raise ValueError(f"Unsupported SMS provider: {provider}")
    
    def _send_webhook(self, channel: NotificationChannel, alert: Alert):
        """Send webhook notification with signature verification"""
        config = channel.config
        
        if not config.get('url'):
            raise ValueError("Webhook URL not configured")
        
        payload = {
            'event': 'alert.created',
            'alert_id': str(alert.id),
            'title': alert.title,
            'severity': alert.severity.value,
            'type': alert.alert_type.value,
            'description': alert.description,
            'timestamp': alert.created_at.isoformat(),
            'municipality_id': str(alert.municipality_id),
            'sensor_id': str(alert.sensor_id) if alert.sensor_id else None,
            'pipeline_id': str(alert.pipeline_id) if alert.pipeline_id else None,
            'location': alert.location,
            'metadata': alert.metadata_json
        }
        
        headers = config.get('headers', {}).copy()
        headers['Content-Type'] = 'application/json'
        headers['User-Agent'] = 'WaterMonitoring/2.0'
        
        # Add HMAC signature if secret is configured
        if config.get('secret'):
            import hmac
            import hashlib
            signature = hmac.new(
                config['secret'].encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = f"sha256={signature}"
        
        response = requests.post(
            config['url'],
            json=payload,
            headers=headers,
            timeout=30,
            verify=config.get('verify_ssl', True)
        )
        
        if response.status_code in [200, 201, 202, 204]:
            logger.info(f"Webhook sent for alert {alert.id} to {config['url']}")
        else:
            raise Exception(f"Webhook failed: {response.status_code} - {response.text}")
    
    def _send_slack(self, channel: NotificationChannel, alert: Alert):
        """Send Slack notification with rich formatting"""
        config = channel.config
        
        if not config.get('webhook_url'):
            raise ValueError("Slack webhook URL not configured")
        
        color = {
            'critical': 'danger',
            'high': 'warning',
            'medium': '#ffeb3b',
            'low': 'good',
            'info': '#2196f3'
        }.get(alert.severity.value, 'good')
        
        emoji = {
            'critical': ':rotating_light:',
            'high': ':warning:',
            'medium': ':large_orange_diamond:',
            'low': ':information_source:',
            'info': ':bulb:'
        }.get(alert.severity.value, ':bell:')
        
        payload = {
            'username': 'Water Monitoring System',
            'icon_emoji': ':droplet:',
            'attachments': [{
                'color': color,
                'title': f"{emoji} {alert.title}",
                'text': alert.description,
                'fields': [
                    {'title': 'Severity', 'value': alert.severity.value.upper(), 'short': True},
                    {'title': 'Type', 'value': alert.alert_type.value.replace('_', ' ').title(), 'short': True},
                    {'title': 'Location', 'value': alert.location or 'N/A', 'short': True},
                    {'title': 'Time', 'value': alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'), 'short': True}
                ],
                'footer': 'National Water Infrastructure Monitoring',
                'footer_icon': 'https://platform.slack-edge.com/img/default_application_icon.png',
                'ts': int(alert.created_at.timestamp())
            }]
        }
        
        response = requests.post(
            config['webhook_url'],
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Slack notification sent for alert {alert.id}")
        else:
            raise Exception(f"Slack webhook failed: {response.status_code} - {response.text}")
    
    def _send_push_notification(self, channel: NotificationChannel, alert: Alert):
        """Send push notification to mobile devices"""
        config = channel.config
        
        if not config.get('expo_push_tokens'):
            logger.warning("No Expo push tokens configured")
            return
        
        tokens = config['expo_push_tokens']
        if isinstance(tokens, str):
            tokens = [tokens]
        
        messages = []
        for token in tokens:
            messages.append({
                'to': token,
                'sound': 'default',
                'title': f"{alert.severity.value.upper()}: {alert.title}",
                'body': alert.description[:100],
                'data': {
                    'alert_id': str(alert.id),
                    'severity': alert.severity.value,
                    'type': alert.alert_type.value
                },
                'priority': 'high' if alert.severity.value in ['critical', 'high'] else 'default'
            })
        
        response = requests.post(
            'https://exp.host/--/api/v2/push/send',
            json=messages,
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Push notifications sent for alert {alert.id} to {len(tokens)} devices")
        else:
            raise Exception(f"Expo push failed: {response.status_code}")
    
    def send_report_notification(self, municipality_id: str, report: Dict):
        """Send scheduled report notification"""
        channels = self.db.query(NotificationChannel).filter(
            NotificationChannel.municipality_id == municipality_id,
            NotificationChannel.is_active == True,
            NotificationChannel.channel_type == NotificationChannelType.EMAIL
        ).all()
        
        for channel in channels:
            try:
                self._send_report_email(channel, report)
            except Exception as e:
                logger.error(f"Report notification failed: {e}")
    
    def _send_report_email(self, channel: NotificationChannel, report: Dict):
        """Send report via email"""
        config = channel.config
        
        msg = MIMEMultipart('alternative')
        msg['From'] = config['from_email']
        msg['To'] = config['to_email']
        msg['Subject'] = f"Daily Water Infrastructure Report - {report.get('date', datetime.now().date())}"
        
        text = f"""
Daily Water Infrastructure Report

Date: {report.get('date')}
Total Readings: {report.get('total_readings', 0)}
Anomalies Detected: {report.get('anomalies', 0)}
Alerts Generated: {report.get('alerts', 0)}

Please check the control room for detailed analytics.
        """
        
        msg.attach(MIMEText(text, 'plain'))
        
        with smtplib.SMTP(config['smtp_host'], int(config.get('smtp_port', 587)), timeout=30) as server:
            if config.get('use_tls', True):
                server.starttls()
            if config.get('username') and config.get('password'):
                server.login(config['username'], config['password'])
            server.send_message(msg)
        
        logger.info(f"Report email sent to {config['to_email']}")


def get_notification_service(db: Session) -> NotificationService:
    return NotificationService(db)
