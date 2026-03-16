"""
Alert Orchestrator
CyberShield Video Analytics System

Coordinates multi-channel alert delivery:
- Twilio (Voice + SMS)
- Telegram Bot
- Email (SMTP)
- In-app dashboard (simulated)
"""

import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)


class AlertOrchestrator:
    """Coordinates multi-channel alert delivery"""

    def __init__(self, config=None):
        self.config = config
        self.twilio_client = None
        self.telegram_bot = None
        self._setup_twilio()
        self._setup_telegram()

    def _setup_twilio(self):
        try:
            from twilio.rest import Client
            sid = getattr(self.config, "TWILIO_ACCOUNT_SID", "") if self.config else ""
            token = getattr(self.config, "TWILIO_AUTH_TOKEN", "") if self.config else ""
            if sid and token and sid != "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
                self.twilio_client = Client(sid, token)
                logger.info("✅ Twilio client initialized")
            else:
                logger.info("⚠️ Twilio credentials not configured — SMS/Call alerts disabled")
        except ImportError:
            logger.warning("⚠️ twilio not installed — SMS/Call alerts disabled")
        except Exception as e:
            logger.warning(f"⚠️ Twilio setup error: {e}")

    def _setup_telegram(self):
        try:
            import telegram
            token = getattr(self.config, "TELEGRAM_BOT_TOKEN", "") if self.config else ""
            if token:
                self.telegram_bot = telegram.Bot(token=token)
                logger.info("✅ Telegram bot initialized")
            else:
                logger.info("⚠️ Telegram token not configured — Telegram alerts disabled")
        except ImportError:
            logger.warning("⚠️ python-telegram-bot not installed — Telegram alerts disabled")
        except Exception as e:
            logger.warning(f"⚠️ Telegram setup error: {e}")

    def send_violence_alert(self, incident_data: dict, officers: list) -> dict:
        """
        Send multi-channel violence alert to area officers.
        """
        results = {"sms": [], "call": [], "telegram": [], "email": [], "dashboard": True}

        message = (
            f"🚨 CRITICAL ALERT: Violence detected at {incident_data.get('location', 'Unknown')}. "
            f"Camera: {incident_data.get('camera_name', 'Unknown')}. "
            f"Area: {incident_data.get('area_name', 'Unknown')}. "
            f"Persons involved: {incident_data.get('persons_involved', '?')}. "
            f"Confidence: {incident_data.get('confidence', 0)*100:.0f}%. "
            f"Immediate response required."
        )

        for officer in officers:
            phone = officer.get("phone_number") or officer.get("phone", "")
            email = officer.get("email", "")
            telegram_id = officer.get("telegram_chat_id", "")

            # SMS
            if self.twilio_client and phone:
                try:
                    msg = self.twilio_client.messages.create(
                        body=message,
                        from_=getattr(self.config, "TWILIO_PHONE_NUMBER", ""),
                        to=phone,
                    )
                    results["sms"].append({"officer": officer.get("name"), "status": "sent", "sid": msg.sid})
                except Exception as e:
                    results["sms"].append({"officer": officer.get("name"), "status": "failed", "error": str(e)})
            else:
                results["sms"].append({"officer": officer.get("name"), "status": "simulated"})

            # Telegram
            if self.telegram_bot and telegram_id:
                try:
                    import asyncio
                    asyncio.get_event_loop().run_until_complete(
                        self.telegram_bot.send_message(chat_id=telegram_id, text=message)
                    )
                    results["telegram"].append({"officer": officer.get("name"), "status": "sent"})
                except Exception as e:
                    results["telegram"].append({"officer": officer.get("name"), "status": "failed", "error": str(e)})
            else:
                results["telegram"].append({"officer": officer.get("name"), "status": "simulated"})

            # Email
            if email:
                email_result = self._send_email(
                    to=email,
                    subject="🚨 CRITICAL: Violence Detection Alert",
                    body=self._build_incident_email(incident_data),
                )
                results["email"].append({"officer": officer.get("name"), **email_result})

        logger.info(f"Violence alert sent to {len(officers)} officers via multiple channels")
        return results

    def send_traffic_alert(self, incident_data: dict, officers: list) -> dict:
        """Send high-traffic alert to traffic officers"""
        results = {"sms": [], "telegram": [], "dashboard": True}

        message = (
            f"🚦 Traffic Alert: High congestion at {incident_data.get('location', 'Unknown')}. "
            f"Signal: {incident_data.get('signal', 'Unknown')}. "
            f"Avg: {incident_data.get('vehicle_count', 0)} vehicles/min. "
            f"Deploy traffic police immediately."
        )

        for officer in officers:
            phone = officer.get("phone_number") or officer.get("phone", "")
            telegram_id = officer.get("telegram_chat_id", "")

            if self.twilio_client and phone:
                try:
                    self.twilio_client.messages.create(
                        body=message,
                        from_=getattr(self.config, "TWILIO_PHONE_NUMBER", ""),
                        to=phone,
                    )
                    results["sms"].append({"officer": officer.get("name"), "status": "sent"})
                except Exception as e:
                    results["sms"].append({"officer": officer.get("name"), "status": "failed"})
            else:
                results["sms"].append({"officer": officer.get("name"), "status": "simulated"})

        return results

    def send_watchlist_alert(self, incident_data: dict, officers: list) -> dict:
        """Send watchlist face match alert"""
        results = {"sms": [], "call": [], "telegram": [], "email": [], "dashboard": True}

        message = (
            f"🔴 WATCHLIST MATCH: {incident_data.get('person_name', 'Unknown')} detected at "
            f"{incident_data.get('camera_name', 'Unknown')}. "
            f"Area: {incident_data.get('area_name', 'Unknown')}. "
            f"Match confidence: {incident_data.get('confidence', 0)*100:.0f}%. "
            f"Case type: {incident_data.get('case_type', 'Unknown')}."
        )

        for officer in officers:
            results["sms"].append({"officer": officer.get("name"), "status": "simulated"})
            results["telegram"].append({"officer": officer.get("name"), "status": "simulated"})
            results["email"].append({"officer": officer.get("name"), "status": "simulated"})

        logger.info(f"Watchlist alert sent for person: {incident_data.get('person_name')}")
        return results

    def _send_email(self, to: str, subject: str, body: str) -> dict:
        """Send email via SMTP"""
        try:
            smtp_user = getattr(self.config, "SMTP_USER", "") if self.config else ""
            smtp_pass = getattr(self.config, "SMTP_PASSWORD", "") if self.config else ""
            smtp_host = getattr(self.config, "SMTP_HOST", "smtp.gmail.com") if self.config else "smtp.gmail.com"
            smtp_port = getattr(self.config, "SMTP_PORT", 587) if self.config else 587

            if not smtp_user or not smtp_pass:
                return {"status": "simulated"}

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = to
            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, to, msg.as_string())

            return {"status": "sent"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    def _build_incident_email(self, incident_data: dict) -> str:
        """Build HTML email body for incident report"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #0d0d0d; color: #ffffff; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #1a1a2e; border-radius: 12px; padding: 30px; border: 1px solid #ff4b4b;">
                <h1 style="color: #ff4b4b; margin-bottom: 20px;">🚨 CRITICAL ALERT: CyberShield</h1>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px; border-bottom: 1px solid #333; color: #aaa;">Incident Type</td>
                        <td style="padding: 8px; border-bottom: 1px solid #333; color: #ff4b4b; font-weight: bold;">
                            {incident_data.get('incident_type', 'Unknown').upper().replace('_', ' ')}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #333; color: #aaa;">Location</td>
                        <td style="padding: 8px; border-bottom: 1px solid #333;">{incident_data.get('location', 'Unknown')}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #333; color: #aaa;">Camera</td>
                        <td style="padding: 8px; border-bottom: 1px solid #333;">{incident_data.get('camera_name', 'Unknown')}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #333; color: #aaa;">Area</td>
                        <td style="padding: 8px; border-bottom: 1px solid #333;">{incident_data.get('area_name', 'Unknown')}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #333; color: #aaa;">Confidence</td>
                        <td style="padding: 8px; border-bottom: 1px solid #333;">{incident_data.get('confidence', 0)*100:.0f}%</td></tr>
                    <tr><td style="padding: 8px; color: #aaa;">Timestamp</td>
                        <td style="padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                </table>
                <p style="color: #ff9900; margin-top: 20px; font-weight: bold;">
                    Immediate response required. Please check the CyberShield dashboard for live feed.
                </p>
            </div>
        </body>
        </html>
        """
