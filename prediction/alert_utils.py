# prediction/alert_utils.py
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.html import strip_tags
import requests
import logging

logger = logging.getLogger(__name__)

def send_email_alert(region, risk_level, rainfall, temperature, user_email=None):
    """Send email alert about flood risk"""
    
    subject = f"🚨 FLOOD ALERT: {risk_level} Risk in {region}"
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .alert-box {{ 
                background-color: {'#dc2626' if risk_level == 'Critical' else '#f59e0b' if risk_level == 'High' else '#eab308'};
                color: white;
                padding: 20px;
                border-radius: 10px;
            }}
            .info {{ background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin-top: 15px; }}
            .button {{ 
                display: inline-block; 
                background-color: #3b82f6; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 5px;
                margin-top: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="alert-box">
            <h2>⚠️ Flood Alert: {region}</h2>
            <p><strong>Risk Level:</strong> {risk_level}</p>
            <p><strong>Rainfall:</strong> {rainfall} mm</p>
            <p><strong>Temperature:</strong> {temperature}°C</p>
        </div>
        
        <div class="info">
            <h3>What to do:</h3>
            <ul>
                <li>Move to higher ground immediately if in low-lying areas</li>
                <li>Prepare emergency supplies (water, food, medications)</li>
                <li>Keep phones charged and stay tuned to weather updates</li>
                <li>Follow evacuation orders if issued</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>Emergency Contacts:</h3>
            <p>🚨 Emergency Number: <strong>112</strong></p>
            <p>🏥 Red Cross: <strong>119</strong></p>
        </div>
        
        <a href="https://your-domain.com/emergency/" class="button">View Emergency Center</a>
        
        <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
            This is an automated alert from FloodGuard Tanzania AI System.<br>
            For updates, visit your dashboard.
        </p>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    recipients = [user_email] if user_email else []
    
    # Get all staff/admin emails if no specific recipient
    if not recipients:
        admin_users = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
        recipients = [user.email for user in admin_users if user.email]
    
    if recipients:
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Email alert sent to {recipients}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    return False


def send_sms_alert(region, risk_level, rainfall, phone_number=None):
    """Send SMS alert using Africa's Talking API"""
    
    # Format message based on risk level
    if risk_level in ['Critical', 'High']:
        message = f"🚨 FLOOD ALERT! {region}: {risk_level} flood risk! {rainfall}mm rainfall. Move to higher ground. Call 112 for help. - FloodGuard"
    else:
        message = f"⚠️ Flood Watch: {region} has {risk_level} flood risk ({rainfall}mm). Stay alert and monitor updates. - FloodGuard"
    
    # Use Africa's Talking API
    username = getattr(settings, 'AFRICASTALKING_USERNAME', 'sandbox')
    api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')
    
    if not api_key:
        logger.warning("SMS not sent: API key not configured")
        return False
    
    # Format phone number (ensure it starts with 255 for Tanzania)
    if phone_number:
        if phone_number.startswith('0'):
            phone_number = '255' + phone_number[1:]
        elif not phone_number.startswith('255'):
            phone_number = '255' + phone_number
    
    # For multiple recipients, you can store user phone numbers in UserProfile
    # For now, we'll use a list of admin phone numbers
    phone_numbers = [phone_number] if phone_number else []
    
    # Get phone numbers from users (if you add phone field to User model)
    # phone_numbers = UserProfile.objects.filter(notify_sms=True).values_list('phone', flat=True)
    
    if not phone_numbers:
        logger.info("No phone numbers to send SMS to")
        return False
    
    # Africa's Talking API endpoint
    url = "https://api.africastalking.com/version1/messaging"
    
    headers = {
        "ApiKey": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    success = True
    for number in phone_numbers:
        data = {
            "username": username,
            "to": number,
            "message": message,
            "from": getattr(settings, 'AFRICASTALKING_SENDER_ID', 'FloodGuard')
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 201:
                logger.info(f"SMS sent to {number}")
            else:
                logger.error(f"SMS failed to {number}: {response.text}")
                success = False
        except Exception as e:
            logger.error(f"SMS error: {e}")
            success = False
    
    return success


def send_telegram_alert(region, risk_level, rainfall):
    """Send Telegram alert (alternative to SMS)"""
    
    # Create a Telegram bot via @BotFather on Telegram
    bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '')
    
    if not bot_token or not chat_id:
        logger.warning("Telegram not configured")
        return False
    
    message = f"""
🚨 *FLOOD ALERT - {region}*
    
⚠️ *Risk Level:* {risk_level}
🌧️ *Rainfall:* {rainfall} mm
📊 *Confidence:* High
    
*Actions:*
• Move to higher ground
• Prepare emergency kit
• Call 112 for help
    
_FloodGuard AI Early Warning System_
    """
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=data)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False