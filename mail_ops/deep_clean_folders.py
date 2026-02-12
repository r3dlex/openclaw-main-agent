import imaplib
import yaml
import os
import sys
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

try:
    with open(os.path.join(SCRIPT_DIR, "config.yaml"), "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print("Error: config.yaml not found.")
    sys.exit(1)

def get_pwd(acc):
    env_key = acc.get('password_env')
    if env_key:
        val = os.getenv(env_key)
        if val: return val
    return acc.get('password')

def connect(acc):
    pwd = get_pwd(acc)
    if not pwd: return None
    try:
        if acc['provider'] == 'davmail':
            print(f"Skipping RIB (DavMail): {acc['name']}")
            return None
        else:
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(acc['user'], pwd)
        return mail
    except Exception as e:
        print(f"[{acc['name']}] Error: {e}")
        return None

# Deep Mappings (Subfolder support)
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
    "Wichtig": "Important",
    "Entwürfe": "Drafts",
    "Gesendet": "Sent",
    "Papierkorb": "Trash",
    "SPAM": "Spam",
    # Portuguese
    "Redes Sociais": "Social",
    "Compras": "Shopping",
    "Promoções": "Shopping",
    "Ofertas": "Shopping",
    "Financeiro": "Finance",
    "Fatura": "Finance",
    "Notícias": "News",
    "Arquivo": "Archive",
    "Segurança": "Security",
    "Jogos": "Gaming",
    "Viagem": "Travel",
    "Férias": "Travel",
    "Food/Delivery": "Food Delivery",
    "Comida": "Food Delivery",
    "Entrega": "Food Delivery",
    "Importante": "Important",
    "Rascunhos": "Drafts",
    "Enviados": "Sent",
    "Lixeira": "Trash",
    "Lixo": "Spam",
    "Pessoal": "Personal", # Common root
    "UFSC": "Education",
    "Anúncios": "Newsletters",
    "An&APo-ncios": "Newsletters", # Encoded
    "Admin": "Admin",
    "NACS": "NACS",
    "NO-IP": "NOIP",
    "Turma da Pracinha": "Pracinha",
}

def deep_clean(mail, acc_name):
    status, folders = mail.list()
    if status != 'OK': return 0

    # Parse all folders
    all_folders = []
    for f in folders:
        try:
            s = f.decode('utf-8', errors='ignore')
            if '"' in s:
                parts = s.split('"')
                if len(parts) >= 4:
                    path = parts[-2]
                    all_folders.append(path)
        except: pass

    actions = 0
    print(f"\n🔵 {acc_name}: Scanning {len(all_folders)} folders...")

    # Sort by depth (longest first) to avoid partial renames
    all_folders.sort(key=len, reverse=True)

    for old in all_folders:
        # 1. Check exact match (Top level)
        matched = False
        for non_en, en in RENAMES.items():
            if old.lower() == non_en.lower():
                try:
                    print(f"  Renaming '{old}' -> '{en}'")
                    mail.rename(old, en)
                    actions += 1
                    matched = True
                    break
                except Exception as e:
                    print(f"    Failed: {e}")
        if matched:
            continue

        # 2. Check parts (Subfolders)
        # Example: "Pessoal/Familia" -> Check if "Pessoal" matches
        if "/" in old:
            parts = old.split("/")
            root = parts[0]
            sub = "/".join(parts[1:])

            for non_en, en in RENAMES.items():
                if root.lower() == non_en.lower():
                    # Build new path
                    new_path = f"{en}/{sub}"
                    try:
                        print(f"  Renaming '{old}' -> '{new_path}'")
                        mail.rename(old, new_path)
                        actions += 1
                        matched = True
                        break
                    except Exception as e:
                        print(f"    Failed: {e}")
            if matched:
                continue

    return actions

def main():
    total = 0
    for acc in CONFIG['accounts']:
        if not acc.get('active'): continue
        if acc['provider'] == 'davmail': continue # SKIP RIB
        m = connect(acc)
        if m:
            total += deep_clean(m, acc['name'])
            m.logout()
    print(f"\n✅ Done. Total actions: {total}")

if __name__ == "__main__":
    main()
