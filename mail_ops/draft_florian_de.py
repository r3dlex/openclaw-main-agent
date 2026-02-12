import imaplib
import email
from email.message import EmailMessage
import os
import time
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

USER = "andre.burgstahler@rib-software.com"
PASS = "REDACTED_PASSWORD"
TO = "Florian.Haag@rib-software.com"
SUBJECT = "Re: Meeting Minutes: Sync on AI Efforts"

BODY = """Hallo Florian,

danke für deine Rückmeldung. Das Thema ist keinesfalls untergegangen, sondern implizit Teil der Verantwortung von Tim als Technical Lead. Um das aber klarzustellen und Missverständnisse zu vermeiden:

1. **AI Framework:** Das bleibt ganz klar in der Verantwortung der **TA**. Wir wollen hier eine saubere, generische Schnittstelle und keine "Bastellösungen".
2. **Priyanka / Schnittstellen:** Tim wird als zentraler Ansprechpartner diesen Punkt mit Priyanka treiben, damit wir die nötigen Definitionen für die Endpunkte bekommen.
3. **PLM:** Jignasa behält hier den Hut auf für die fachliche Seite (Use Cases).

Tim hat den Auftrag, genau diese architektonische Sauberkeit sicherzustellen und die Brücke zwischen den Teams zu schlagen.

Wir können gerne kurz dazu sprechen, falls du noch Bedenken hast.

Beste Grüße,
Andre"""

try:
    mail = imaplib.IMAP4("localhost", 1143)
    mail.login(USER, PASS)
    
    msg = EmailMessage()
    msg["From"] = USER
    msg["To"] = TO
    msg["Subject"] = SUBJECT
    msg.set_content(BODY)
    
    mail.append("Drafts", "\\Draft", imaplib.Time2Internaldate(time.time()), str(msg).encode("utf-8"))
    mail.logout()
    print("Draft saved.")
except Exception as e:
    print(f"Error: {e}")
