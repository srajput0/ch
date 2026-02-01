import asyncio
import logging
import re
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait

# --- CONFIGURATION ---
API_ID = 27343489
API_HASH = "bb6da47b900d646484f58a5d19d64a68"
# NOTE: BOT_TOKEN is REMOVED. We must log in as a User to see old requests.

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- INITIALIZE CLIENT (USER MODE) ---
# When you run this, check your TERMINAL/CONSOLE. 
# It will ask for your Phone Number and OTP Code.
app = Client(
    "my_user_account",
    api_id=API_ID,
    api_hash=API_HASH
)

@app.on_message(filters.command("accept", prefixes="/") & (filters.group | filters.channel | filters.private))
async def targeted_approve(client, message):
    # This block handles the command: /accept 10  or  /accept all
    
    chat_id = message.chat.id
    
    # --- PARSE COMMAND ---
    # Expected format: /accept 10  or /accept all
    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply_text("❌ Usage: `/accept 10` or `/accept all`", quote=True)
            return
            
        argument = command_parts[1].lower()
    except:
        return

    if argument == "all":
        limit = float('inf')
        status_text = "Processing **ALL** pending requests..."
    elif argument.isdigit():
        limit = int(argument)
        status_text = f"Processing **{limit}** requests..."
    else:
        await message.reply_text("❌ Invalid number.", quote=True)
        return

    # Send status message
    try:
        status_msg = await message.reply_text(f"⏳ {status_text}", quote=True)
    except Exception as e:
        logger.error(f"Could not send reply: {e}")
        return
    
    count = 0
    
    try:
        # --- PROCESS REQUESTS ---
        # As a User, you CAN see the list!
        async for request in client.get_chat_join_requests(chat_id):
            
            if count >= limit:
                break
                
            try:
                await client.approve_chat_join_request(chat_id, request.user.id)
                count += 1
                
                # Log progress
                if count % 20 == 0:
                    logger.info(f"Approved {count} users...")
                    
                # Update Message every 50 users
                if count % 50 == 0:
                    try:
                        await status_msg.edit_text(f"⏳ Progress: Approved {count} users...")
                    except:
                        pass

            except FloodWait as e:
                wait_time = e.value + 5
                logger.warning(f"Sleeping for {wait_time}s due to FloodWait...")
                await status_msg.edit_text(f"⚠️ Telegram Limit Hit. Pausing for {wait_time}s...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Failed to approve user: {e}")

        await status_msg.edit_text(f"✅ **Task Completed**\n\nSuccessfully approved: {count} members.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

print("Bot Started in USER MODE.")
print("1. Enter your Phone Number (with country code, e.g., +91...) when asked.")
print("2. Enter the Code you receive on Telegram.")
print("3. Go to your channel and type: /accept 50")
app.run()
