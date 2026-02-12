import imaplib
import email
from email.header import decode_header, Header
from email.utils import parsedate_to_datetime
import yaml
import re
import sys
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load Environment Variables
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

# Load Config
try:
    with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print("Error: config.yaml not found.")
    sys.exit(1)

# VIP List
VIPS = [
    "rolf.helmes@rib-software.com",
    "arthur.berganski@rib-software.com",
    "tim.laine@rib-software.com",
    "han.che@rib-software.com",
    "beate.kasper@rib-software.com",
    "reinhardt.fraunhoffer@rib-software.com",
    "julien.seroi@rib-software.com",
    "anke.vera@hotmail.de"
]

# Rules
COMMON_RULES = [
    (r"(newsletter|marketing|update|no-reply|noreply|promotions|digest|linkedin|facebook|instagram|social|bestbuy|aldi|rewe|academia|nvidia|job|recruiter|shop|store|angebot|deal|sale|discount|off|save|coupon|youtube|pinterest|tiktok|quora|xing)", "Newsletters"),
    (r"(invoice|receipt|payment|bill|rechnung|order|bestellung|fatura|comprovante|recibo)", "Finance"),
    (r"(security|alert|verify|login|signin|code|auth|segurança|alerta)", "Security"),
    (r"(steam|epic|game|playstation|xbox|twitch|discord)", "Gaming"),
    (r"(amazon|paypal|delivery|versand|dhl|ups|tracking|entrega|rastreio|shopee|mercadolivre)", "Shopping"),
    (r"(flight|hotel|booking|airbnb|uber|train|bahn|voo|reserva|viagem)", "Travel"),
]

# Personal BR Rules
PERSONAL_BR_RULES = [
    # Shopping & E-commerce
    (r"(promo|oferta|desconto|frete gratis|frete grátis|liquidação|black friday|cyber monday|mercado livre|americanas|magazine luiza|shopee|amazon\.br|casas bahia|extra|ponto frio|kabum| Magazine Luiza)", "Shopping"),
    # Banking & Finance
    (r"(nubank|caixa|santander|it[áa]u|banco do brasil|fatura|extrato|extrato financeiro|carteirinha|cartão|card|boleto|pagamento|parcelamento)", "Finance"),
    # Utilities & Phone
    (r"(claro|vivo|tim|oi|recarga|conta|promoção|plano|控)", "Utilities"),
    # Health & Pharma
    (r"(drogaraia|drogapoca|ultrafarma|farmácia|medicamento|receita|consulta|doctor|saúde)", "Health"),
    # Food & Delivery
    (r"(ifood|rappi|uber eats|delivery|rapido|loggi|james|connery|pedido|restaurante|picpay)", "Food/Delivery"),
    # Events & Tickets
    (r"(ingresso\.com|sympla|eventim|cultural|show|ingresso|bilhete)", "Events"),
]

WORK_RULES = [
    (r"(hr|vacation|pto|sick|krank|urlaub|workday|personnel)", "HR"),
    (r"(sales|contract|vertrieb|crm|lead|deal)", "Sales"),
    (r"(vendor|supplier|lieiferant)", "Vendors"),
    (r"(it support|helpdesk|service|admin)", "Admin"),
    (r"(accepted|angenommen|declined|abgelehnt|tentative|mit vorbehalt|reaction|digest|ooo|out of office|abwesend|automatic reply|automatische antwort)", "Archive"),
]

SYSTEM_RULES = [
    (r"(cron|job|task|backup|log|error|warning)", "Logs"),
    (r"(alert|critical|failure|down)", "Alerts"),
]

# Dynamic Rule: Releases
# Captures: "Release 26.1", "26.1.0", "v25.3"
RELEASE_REGEX = r"(release|version|v)\s?(\d{2}\.\d)" 

def get_password(acc):
    env_key = acc.get('password_env')
    if env_key:
        return os.getenv(env_key)
    return acc.get('password')

def connect_to_account(acc):
    password = get_password(acc)
    if not password: return None
    try:
        if acc['provider'] == 'davmail':
            host = acc.get('host', CONFIG['defaults']['davmail_host'])
            port = acc.get('port', CONFIG['defaults']['davmail_port'])
            mail = imaplib.IMAP4(host, port)
        elif acc['provider'] == 'gmail':
            host = acc.get('host', CONFIG['defaults']['gmail_host'])
            port = acc.get('port', CONFIG['defaults']['gmail_port'])
            mail = imaplib.IMAP4_SSL(host, port)
        else:
            return None
        mail.login(acc['user'], password)
        return mail
    except Exception as e:
        print(f"[{acc['name']}] Connection Failed: {e}")
        return None

def clean_header(header_value):
    if not header_value: return ""
    if isinstance(header_value, Header): header_value = str(header_value)
    try:
        decoded_list = decode_header(header_value)
    except:
        return str(header_value)
    parts = []
    for content, encoding in decoded_list:
        if isinstance(content, bytes):
            if encoding:
                if encoding.lower() in ['unknown-8bit', 'unknown']: encoding = 'utf-8'
                try: parts.append(content.decode(encoding, errors="replace"))
                except: parts.append(content.decode('utf-8', errors="replace"))
            else:
                parts.append(content.decode('utf-8', errors="replace"))
        else:
            parts.append(str(content))
    return "".join(parts)

def ensure_folder(mail, folder_name):
    try:
        mail.create(folder_name)
    except:
        pass

def process_account(acc):
    print(f"\n🔵 Connecting to: {acc['name']} ({acc['user']})...")
    mail = connect_to_account(acc)
    if not mail: return

    try:
        mail.select("Inbox")
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        total = len(email_ids)
        print(f"[{acc['name']}] Found {total} total messages.")
        
        active_rules = COMMON_RULES.copy()
        if acc['role'] == 'work': active_rules.extend(WORK_RULES)
        if acc['role'] == 'system': active_rules.extend(SYSTEM_RULES)
        if acc['role'] == 'personal': active_rules.extend(PERSONAL_BR_RULES)
        
        cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)
        cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Scan last 1000 items (Deep Scan requested via chat)
        count = 0
        moved = 0
        
        for e_id in reversed(email_ids[-1000:]):
            count += 1
            if count % 100 == 0: print(f"[{acc['name']}] Scanned {count}...", flush=True)

            try:
                res, msg_data = mail.fetch(e_id, "(RFC822.HEADER)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = clean_header(msg.get("Subject"))
                        sender = clean_header(msg.get("From"))
                        date_str = msg.get("Date")
                        
                        email_date = None
                        if date_str:
                            try:
                                email_date = parsedate_to_datetime(date_str)
                                if email_date.tzinfo is None:
                                    email_date = email_date.replace(tzinfo=timezone.utc)
                            except: pass
                        
                        is_vip = any(vip in sender.lower() for vip in VIPS)
                        target_folder = None
                        action = "move"

                        # 1. Release Folders (Dynamic) - WORK ONLY
                        if acc['role'] == 'work':
                            match = re.search(RELEASE_REGEX, subject, re.IGNORECASE)
                            if match:
                                version_short = match.group(2) # e.g. "26.1"
                                # Assume Year based on version or current year?
                                # Version 26.x = 2026. Version 25.x = 2025.
                                # Heuristic: "20" + version_major
                                year_prefix = "20" + version_short.split('.')[0]
                                target_folder = f"Releases/{year_prefix}.{version_short.split('.')[1]}"
                                ensure_folder(mail, "Releases") # Ensure parent
                                ensure_folder(mail, target_folder)

                        # 2. Logs / Automation
                        if not target_folder and acc['role'] == 'work':
                            if "automation" in sender.lower() or "no-reply" in sender.lower():
                                target_folder = "Logs"
                                ensure_folder(mail, "Logs")

                        # 3. Standard Rules
                        if not target_folder:
                             for pattern, folder in active_rules:
                                if re.search(pattern, subject, re.IGNORECASE) or re.search(pattern, sender, re.IGNORECASE):
                                    target_folder = folder
                                    break
                                    
                        # 4. Graymail / Old Archive
                        if not target_folder and email_date and email_date < cutoff_30d:
                            target_folder = "Archive"

                        # EXECUTE
                        if target_folder:
                            try:
                                res = mail.copy(e_id, target_folder)
                                if res[0] == 'OK':
                                    mail.store(e_id, "+FLAGS", "\\Deleted")
                                    moved += 1
                            except: pass
            except: pass

        mail.expunge()
        mail.logout()
        print(f"[{acc['name']}] Finished. Moved {moved} messages.")
        
    except Exception as e:
        print(f"[{acc['name']}] Operations Failed: {e}")

def main():
    for acc in CONFIG['accounts']:
        if acc.get('active', False):
            process_account(acc)

if __name__ == "__main__":
    main()
