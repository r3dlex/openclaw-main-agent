import imaplib
import yaml
import os
import sys

# Load Config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print("Error: config.yaml not found.")
    sys.exit(1)

def get_password(acc):
    env_key = acc.get('password_env')
    if env_key:
        return os.getenv(env_key)
    return acc.get('password')

def connect(acc):
    password = get_password(acc)
    if not password: return None
    try:
        if acc['provider'] == 'davmail':
            host = acc.get('host', 'localhost')
            port = acc.get('port', 1143)
            mail = imaplib.IMAP4(host, port)
        else:
            host = 'imap.gmail.com'
            port = 993
            mail = imaplib.IMAP4_SSL(host, port)
        mail.login(acc['user'], password)
        return mail
    except Exception as e:
        print(f"[{acc['name']}] Connection Failed: {e}")
        return None

# Mappings
RENAMES = {
    # German
    "Einkaufen": "Shopping",
    "Kaufen": "Shopping",
    "Finanzen": "Finance",
    "Rechnungen": "Finance",
    "Nachrichten": "News",
    "Newsletter": "Newsletters",
    "Archiv": "Archive",
    "Soziales": "Social",
    "Sicherheit": "Security",
    "Spiele": "Gaming",
    "Reisen": "Travel",
    "Urlaub": "Travel",
    "Büro": "Office",
    # Portuguese
    "Compras": "Shopping",
    "Promoções": "Shopping",
    "Ofertas": "Shopping",
    "Financeiro": "Finance",
    "Fatura": "Finance",
    "Notícias": "News",
    "Arquivo": "Archive",
    "Social": "Social",
    "Segurança": "Security",
    "Jogos": "Gaming",
    "Viagem": "Travel",
    "Férias": "Travel",
    "Food/Delivery": "Food Delivery",
    "Comida": "Food Delivery",
    "Entrega": "Food Delivery",
}

def optimize_account(acc):
    print(f"\n🔵 Optimizing: {acc['name']} ({acc['user']})")
    mail = connect(acc)
    if not mail: return

    try:
        # List folders
        status, folders = mail.list()
        if status != 'OK': return

        folder_map = {}
        for f in folders:
            # Parse folder name
            name = f.decode('utf-8', errors='ignore')
            # Handle (has-children) etc.
            if '"' in name:
                parts = name.split('"')
                if len(parts) > 2:
                    name = parts[-2]
            name = name.strip()
            if name:
                folder_map[name] = name

        print(f"  Found {len(folder_map)} folders.")

        renames = 0
        merges = 0

        # 1. Renames
        for old in list(folder_map.keys()):
            # Check if it matches any DE/PT key
            matched = False
            for de_pt, en in RENAMES.items():
                if old.lower() == de_pt.lower() or old.lower() == en.lower():
                    continue # Skip if already English
                if de_pt.lower() in old.lower():
                    # Match found
                    print(f"  Renaming: '{old}' -> '{en}'")
                    try:
                        mail.rename(old, en)
                        folder_map[en] = folder_map.pop(old)
                        renames += 1
                        matched = True
                        break
                    except Exception as e:
                        print(f"    Failed to rename {old}: {e}")

            if matched:
                continue

            # 2. Consolidation (Merge logic)
            # Example: "Newsletters" and "Newsletter" -> "Newsletters"
            if old.lower().endswith("s") and old[:-1].lower() in [k[:-1].lower() for k in folder_map.keys()]:
                target = old
                source = old[:-1]
                if source in folder_map:
                    print(f"  Merging: '{source}' -> '{target}'")
                    try:
                        # Copy messages
                        typ, msgs = mail.select(source)
                        if typ == 'OK' and int(msgs[0]) > 0:
                            # Fetch all
                            typ, data = mail.search(None, 'ALL')
                            ids = data[0].split()
                            for msg_id in ids:
                                mail.copy(msg_id, target)
                                mail.store(msg_id, '+FLAGS', '\\Deleted')
                            mail.expunge()
                        # Delete source
                        mail.create(source) # Ensure exists (IMAP quirk)
                        # Actually delete source? IMAP RENAME is move. DEL is delete.
                        # Hard to delete without UID经验的累积.
                        # Let's stick to RENAME for now.
                        print(f"    (Merging requires manual copy usually. Skipping delete)")
                    except Exception as e:
                        print(f"    Merge failed: {e}")

        print(f"  Done. Renamed {renames}, Merges attempted {merges}.")

    except Exception as e:
        print(f"Error optimizing {acc['name']}: {e}")
    finally:
        try: mail.logout()
        except: pass

def main():
    for acc in CONFIG['accounts']:
        if acc.get('active', False):
            # Only do Gmail first
            if acc['provider'] == 'gmail':
                optimize_account(acc)
            elif acc['provider'] == 'davmail':
                print(f"\n🔵 Skipping DavMail (RIB) for now - needs manual review.")
                continue

if __name__ == "__main__":
    main()
