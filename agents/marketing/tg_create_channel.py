import sys, asyncio
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION = "tg_user_session"
CHANNEL_USERNAME = "ghidulreducerilor"
CHANNEL_TITLE = "Ghidul Reducerilor"
CHANNEL_ABOUT = "Top reduceri zilnice din Romania. Site: https://ghidulreducerilor.ro"
BOT_USERNAME = "Ghidulreducerilorbot"
BOT_TOKEN = "8689101992:AAHQiYpZOcGgINSWfQBWfY5XScSfpS43E2s"

async def main():
    from telethon import TelegramClient
    from telethon.tl.functions.channels import CreateChannelRequest, EditAdminRequest, UpdateUsernameRequest
    from telethon.tl.types import ChatAdminRights
    import requests, time

    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("Nu esti autentificat! Ruleaza mai intai tg_qr_login.py")
        await client.disconnect()
        return

    me = await client.get_me()
    print(f"Autentificat: {me.first_name} (@{me.username})")

    # Incerc sa gasesc canalul daca exista deja
    channel = None
    try:
        existing = await client.get_entity(f"@{CHANNEL_USERNAME}")
        print(f"Canal gasit deja: @{CHANNEL_USERNAME}")
        channel = existing
    except Exception:
        pass

    ch_username = CHANNEL_USERNAME
    if channel is None:
        print(f"Creez canal nou @{ch_username}...")
        try:
            result = await client(CreateChannelRequest(
                title=CHANNEL_TITLE, about=CHANNEL_ABOUT, megagroup=False))
            channel = result.chats[0]
            print(f"Canal creat: ID={channel.id}")
            try:
                await client(UpdateUsernameRequest(channel, ch_username))
                print(f"Username setat: @{ch_username} -> t.me/{ch_username}")
            except Exception as e2:
                print(f"Username eroare: {e2}")
                ch_username = "ghidul_reducerilor_ro"
                await client(UpdateUsernameRequest(channel, ch_username))
                print(f"Username alternativ: @{ch_username}")
        except Exception as e:
            print(f"Eroare creare canal: {type(e).__name__}: {e}")
            await client.disconnect()
            return

    # Adaug bot ca admin
    print(f"\nAdaug @{BOT_USERNAME} ca admin...")
    try:
        bot_entity = await client.get_entity(f"@{BOT_USERNAME}")
        await client(EditAdminRequest(
            channel=channel,
            user_id=bot_entity,
            admin_rights=ChatAdminRights(
                post_messages=True, edit_messages=True, delete_messages=False,
                change_info=False, invite_users=False, pin_messages=False),
            rank="Bot"
        ))
        print(f"Bot @{BOT_USERNAME} adaugat ca admin!")
    except Exception as e:
        print(f"Eroare bot admin: {type(e).__name__}: {e}")

    # Test post via Bot API
    print("\nTrimet mesaj test via Bot API...")
    time.sleep(2)
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": f"@{ch_username}",
            "text": (
                "Ghidul Reducerilor este acum LIVE!\n\n"
                "Reduceri zilnice din Romania, verificate si selectate automat.\n\n"
                "Site: https://ghidulreducerilor.ro"
            )
        },
        timeout=15
    ).json()
    if r.get("ok"):
        print(f"Mesaj test OK! Link: t.me/{ch_username}")
    else:
        print(f"Mesaj test eroare: {r.get('description', r)}")

    # Actualizeaza .env
    from pathlib import Path
    env_path = Path(__file__).parent.parent.parent / ".env"
    content = env_path.read_text(encoding="utf-8")
    content = content.replace("TELEGRAM_CHANNEL_ID=@ghidulreducerilor",
                              f"TELEGRAM_CHANNEL_ID=@{ch_username}")
    env_path.write_text(content, encoding="utf-8")
    print(f".env actualizat: TELEGRAM_CHANNEL_ID=@{ch_username}")

    await client.disconnect()
    print(f"\n=== SETUP COMPLET ===")
    print(f"Canal: t.me/{ch_username}")
    print(f"Bot admin: @{BOT_USERNAME}")
    print(f"Ruleaza acum: python telegram_agent.py")

asyncio.run(main())
