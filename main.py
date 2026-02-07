import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

# --- CONFIGURATION ---
# Apne credentials yahan dalein
API_ID = 27343489       # Aapka wahi ID
API_HASH = "bb6da47b900d646484f58a5d19d64a68" # Aapka wahi Hash
BOT_TOKEN = "8207099625:AAF6DDZCZziiGUYrcETHiubC3SI4P0IecAs" # 🔴 Yahan BotFather wala Token dalein

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- INITIALIZE CLIENT (BOT MODE) ---
# Yahan hum bot_token use kar rahe hain, isliye OTP nahi mangega
app = Client(
    "approval_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("accept", prefixes="/") & (filters.group | filters.channel | filters.private))
async def targeted_approve(client, message):
    # Command format: /accept 10  ya  /accept all
    
    chat_id = message.chat.id
    
    # --- PARSE COMMAND ---
    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply_text("❌ Sahi tarika: `/accept 10` ya `/accept all`", quote=True)
            return
            
        argument = command_parts[1].lower()
    except:
        return

    # Limit set karna
    if argument == "all":
        limit = float('inf')
        status_text = "**SABHI (All)** requests process ho rahi hain..."
    elif argument.isdigit():
        limit = int(argument)
        status_text = f"**{limit}** requests process ho rahi hain..."
    else:
        await message.reply_text("❌ Galat number hai.", quote=True)
        return

    # Status Message bhejna
    try:
        status_msg = await message.reply_text(f"⏳ {status_text}", quote=True)
    except Exception as e:
        logger.error(f"Reply nahi bhej paya: {e}")
        return
    
    count = 0
    
    try:
        # --- PROCESS REQUESTS ---
        # Bot API ke through pending requests fetch karna
        async for request in client.get_chat_join_requests(chat_id):
            
            if count >= limit:
                break
                
            try:
                # Request Approve karna
                await client.approve_chat_join_request(chat_id, request.user.id)
                count += 1
                
                # Console mein log karna
                if count % 20 == 0:
                    logger.info(f"Approved {count} users...")
                    
                # Message update karna (har 50 users ke baad taaki flood na ho)
                if count % 50 == 0:
                    try:
                        await status_msg.edit_text(f"⏳ Progress: Abhi tak {count} users approve kiye...")
                    except:
                        pass

            except FloodWait as e:
                # Agar Telegram rok laga de (FloodWait)
                wait_time = e.value + 5
                logger.warning(f"Sleeping for {wait_time}s due to FloodWait...")
                await status_msg.edit_text(f"⚠️ Telegram Limit Hit. {wait_time}s ke liye ruk raha hoon...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"User approve nahi ho paya: {e}")

        await status_msg.edit_text(f"✅ **Kaam Khatam!**\n\nTotal approved: {count} members.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}\n\nMake sure Bot is Admin!")

print("🤖 Bot Started!")
print("1. Bot ko apne Channel/Group mein ADMIN banayein.")
print("2. Command use karein: /accept 50")
app.run()
