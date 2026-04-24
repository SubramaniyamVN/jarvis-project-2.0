"""
jarvis_messages.py — Phase 5: Email & WhatsApp
Send/read emails via Gmail SMTP and send WhatsApp via pywhatkit.
"""

import smtplib
import imaplib
import email
import re
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jarvis_engine import speak, take_command

# ── CONFIG ────────────────────────────────────────────────────────────────────
# Use App Password (not your real Gmail password)
# Steps: Google Account → Security → 2-Step Verification → App passwords
GMAIL_USER     = "your_email@gmail.com"
GMAIL_PASSWORD = "your_app_password_here"   # 16-char App Password

# WhatsApp: country code + number (no + sign)
DEFAULT_WA_NUMBER = "919876543210"   # India: 91 + 10 digit number

# Contact book — add your contacts here
CONTACTS = {
    "mom":    "mom@gmail.com",
    "dad":    "dad@gmail.com",
    "boss":   "boss@company.com",
    "rahul":  "rahul@gmail.com",
    "office": "office@company.com",
}

WA_CONTACTS = {
    "mom":   "919000000001",
    "dad":   "919000000002",
    "rahul": "919000000003",
}


# ── EMAIL: SEND ───────────────────────────────────────────────────────────────
def send_email(to_name_or_email, subject, body):
    """Send email to a contact name or direct email address."""
    # Resolve contact name to email
    to_email = CONTACTS.get(to_name_or_email.lower(), to_name_or_email)
    if "@" not in to_email:
        speak(f"I don't have an email address for {to_name_or_email}.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From']    = GMAIL_USER
        msg['To']      = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())

        speak(f"Email sent to {to_name_or_email} successfully.")
        return True

    except smtplib.SMTPAuthenticationError:
        speak("Email authentication failed. Please check your Gmail App Password.")
        return False
    except Exception as e:
        speak(f"Could not send email. Error: {str(e)[:60]}")
        return False


# ── EMAIL: READ ───────────────────────────────────────────────────────────────
def read_emails(count=5, folder="INBOX"):
    """Read the latest unread emails."""
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_USER, GMAIL_PASSWORD)
        mail.select(folder)

        _, data = mail.search(None, 'UNSEEN')
        mail_ids = data[0].split()

        if not mail_ids:
            speak("You have no unread emails.")
            return

        recent = mail_ids[-count:]
        speak(f"You have {len(mail_ids)} unread emails. Reading the latest {min(count, len(recent))}.")

        for mail_id in reversed(recent):
            _, msg_data = mail.fetch(mail_id, '(RFC822)')
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            sender  = msg.get('From', 'Unknown')
            subject = msg.get('Subject', 'No subject')
            date    = msg.get('Date', '')

            # Extract plain text body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

            speak(f"Email from {sender}. Subject: {subject}. Message: {body[:200]}")
            time.sleep(0.5)

        mail.close()
        mail.logout()

    except imaplib.IMAP4.error:
        speak("Could not connect to Gmail. Check credentials.")
    except Exception as e:
        speak(f"Email read error: {str(e)[:60]}")


# ── WHATSAPP: SEND ────────────────────────────────────────────────────────────
def send_whatsapp(to_name_or_number, message, hour=None, minute=None):
    """
    Send WhatsApp message.
    If hour/minute not given, sends in 1 minute (pywhatkit limitation).
    """
    try:
        import pywhatkit

        number = WA_CONTACTS.get(to_name_or_number.lower(),
                                  to_name_or_number)
        if not number.startswith("+"):
            number = "+" + number

        now = time.localtime()
        if hour is None:
            hour   = now.tm_hour
            minute = now.tm_min + 2   # minimum 2 minutes ahead
            if minute >= 60:
                hour   += 1
                minute -= 60

        speak(f"Sending WhatsApp message to {to_name_or_number}.")
        pywhatkit.sendwhatmsg(number, message, hour, minute,
                               wait_time=15, tab_close=True)
        speak("WhatsApp message scheduled successfully.")
        return True

    except ImportError:
        speak("pywhatkit not installed. Run: pip install pywhatkit")
        return False
    except Exception as e:
        speak(f"WhatsApp error: {str(e)[:60]}")
        return False


# ── VOICE-DRIVEN EMAIL COMPOSE ────────────────────────────────────────────────
def compose_email_by_voice():
    """Walk the user through composing an email using voice."""
    speak("Who should I send the email to?")
    to = take_command()
    if not to:
        speak("No recipient specified.")
        return

    speak(f"What is the subject?")
    subject = take_command()
    if not subject:
        subject = "Message from Jarvis"

    speak("What is the message?")
    body = take_command()
    if not body:
        speak("No message content. Cancelled.")
        return

    speak(f"Sending email to {to} with subject: {subject}. Shall I proceed? Say yes or no.")
    confirm = take_command()
    if "yes" in confirm.lower():
        send_email(to, subject, body)
    else:
        speak("Email cancelled.")


# ── COMMAND ROUTER ────────────────────────────────────────────────────────────
def handle_messages(query):
    q = query.lower()

    if "send email" in q or "compose email" in q or "write email" in q:
        # Try to parse: "send email to rahul meeting at 3pm"
        match = re.search(r'(?:send email to|email to)\s+(\w+)\s*(.*)', q)
        if match:
            to      = match.group(1)
            content = match.group(2).strip()
            subject = content[:50] if content else "Message"
            body    = content if content else "Sent via Jarvis"
            send_email(to, subject, body)
        else:
            compose_email_by_voice()

    elif "read email" in q or "check email" in q or "check inbox" in q:
        count = 3
        nums = re.findall(r'\d+', q)
        if nums:
            count = int(nums[0])
        read_emails(count)

    elif "whatsapp" in q or "send message" in q:
        match = re.search(r'(?:whatsapp|message)\s+(\w+)\s*(.*)', q)
        if match:
            to  = match.group(1)
            msg = match.group(2).strip() or "Message sent via Jarvis"
            send_whatsapp(to, msg)
        else:
            speak("Who should I send the WhatsApp message to?")
            to  = take_command()
            speak("What is the message?")
            msg = take_command()
            if to and msg:
                send_whatsapp(to, msg)

    else:
        speak("Message command not recognized. Try: send email to name / check email / whatsapp name message")


if __name__ == "__main__":
    print("Phase 5 — Email & WhatsApp module")
    print("Commands: send email / check email / whatsapp")
    handle_messages(input("Command: "))