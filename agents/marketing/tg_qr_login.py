"""
tg_qr_login.py — QR code login + creare canal + adaugare bot admin.
Salvează QR code ca imagine și o deschide automat.
"""
import asyncio, os, sys, subprocess
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from pathlib import Path

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION = str(Path(__file__).parent / "tg_user_session")

BOT_TOKEN = "8689101992:AAHQiYpZOcGgINSWfQBWfY5XScSfpS43E2s"
BOT_USERNAME = "Ghidulreducerilorbot"
CHANNEL_USERNAME = "ghidulreducerilor"
CHANNEL_TITLE = "Ghidul Reducerilor"
CHANNEL_ABOUT = "Top reduceri zilnice din Romania. Site: https://ghidulreducerilor.ro"
QR_PATH = str(Path(__file__).parent / "tg_qr.png")


async def main():
    from telethon import TelegramClient
    from telethon.tl.functions.channels import CreateChannelRequest, EditAdminRequest, UpdateUsernameRequest
    from telethon.tl.types import ChatAdminRights
    import qrcode, requests

    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("Generez QR code...")
        qr_login = await client.qr_login()

        # Salvez QR ca PNG
        img = qrcode.make(qr_login.url)
        img.save(QR_PATH)
        print(f"QR salvat: {QR_PATH}")

        # Deschid imaginea automat
        subprocess.Popen(["explorer", QR_PATH])
        print()
        print("=" * 55)
        print("  SCANEAZĂ QR CODE DIN TELEGRAM APP:")
        print("  Setări → Dispozitive → Conectare dispozitiv nou")
        print("=" * 55)
        print("Aștept scanarea (60 secunde)...")

        try:
            await asyncio.wait_for(qr_login.wait(), timeout=60)
            print("Login reusit!")
        except asyncio.TimeoutError:
            # Regenerez QR daca a expirat
            await qr_login.recreate()
            img = qrcode.make(qr_login.url)
            img.save(QR_PATH)
            subprocess.Popen(["explorer", QR_PATH])
            print("QR expirat — QR nou generat. Scanează din nou!")
            try:
                await asyncio.wait_for(qr_login.wait(), timeout=60)
                print("Login reusit!")
            except Exception as e:
                print(f"Login esuat: {e}")
                await client.disconnect()
                return
    else:
        me = await client.get_me()
        print(f"Deja autentificat: {me.first_name} (@{me.username})")

    # Creare canal
    print(f"\nCreez canalul @{CHANNEL_USERNAME}...")
    try:
        result = await client(CreateChannelRequest(
            title=CHANNEL_TITLE,
            about=CHANNEL_ABOUT,
            megagroup=False,
        ))
        channel = result.chats[0]
        print(f"Canal creat: ID={channel.id}")

        # Username public
        await client(UpdateUsernameRequest(channel, CHANNEL_USERNAME))
        print(f"Username: @{CHANNEL_USERNAME} -> t.me/{CHANNEL_USERNAME}")

    except Exception as e:
        if "USERNAME_OCCUPIED" in str(e):
            print(f"@{CHANNEL_USERNAME} ocupat, folosesc varianta alternativa...")
            CHANNEL_USERNAME_ALT = "ghidul_reducerilor_ro"
            result = await client(CreateChannelRequest(
                title=CHANNEL_TITLE, about=CHANNEL_ABOUT, megagroup=False))
            channel = result.chats[0]
            await client(UpdateUsernameRequest(channel, CHANNEL_USERNAME_ALT))
            CHANNEL_USERNAME = CHANNEL_USERNAME_ALT
            print(f"Canal creat cu @{CHANNEL_USERNAME}")
        else:
            print(f"Eroare canal: {e}")
            await client.disconnect()
            return

    # Adaug botul ca admin
    print(f"\nAdaug @{BOT_USERNAME} ca admin...")
    try:
        bot_entity = await client.get_entity(f"@{BOT_USERNAME}")
        await client(EditAdminRequest(
            channel=channel,
            user_id=bot_entity,
            admin_rights=ChatAdminRights(
                post_messages=True,
                edit_messages=True,
                delete_messages=False,
                change_info=False,
                invite_users=False,
                pin_messages=False,
            ),
            rank="Bot"
        ))
        print(f"Bot @{BOT_USERNAME} adaugat ca admin!")
    except Exception as e:
        print(f"Eroare adaugare bot: {e}")

    # Trimit mesaj de bun venit via Bot API
    import time, requests as req
    time.sleep(2)
    r = req.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": f"@{CHANNEL_USERNAME}",
            "text": "Ghidul Reducerilor este acum live! Reduceri zilnice din Romania. Site: https://ghidulreducerilor.ro",
            "disable_web_page_preview": False,
        }, timeout=15
    ).json()
    if r.get("ok"):
        print(f"Mesaj test trimis pe @{CHANNEL_USERNAME}!")
    else:
        print(f"Mesaj test: {r}")

    # Actualizeaza .env
    env_path = Path(__file__).parent.parent.parent / ".env"
    content = env_path.read_text(encoding="utf-8")
    content = content.replace("TELEGRAM_CHANNEL_ID=@ghidulreducerilor",
                              f"TELEGRAM_CHANNEL_ID=@{CHANNEL_USERNAME}")
    env_path.write_text(content, encoding="utf-8")

    print("\n" + "="*55)
    print(f"  SETUP COMPLET!")
    print(f"  Canal: t.me/{CHANNEL_USERNAME}")
    print(f"  Bot: @{BOT_USERNAME}")
    print(f"  Test: python telegram_agent.py")
    print("="*55)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
