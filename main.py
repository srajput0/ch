import asyncio
import logging
import re
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait

# --- CONFIGURATION ---
# Get these from https://my.telegram.org
API_ID = 27343489  # REPLACE THIS
API_HASH = "bb6da47b900d646484f58a5d19d64a68"  # REPLACE THIS
BOT_TOKEN = "8207099625:AAF6DDZCZziiGUYrcETHiubC3SI4P0IecAs"  # REPLACE THIS

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- INITIALIZE CLIENT ---
app = Client(
    "smart_accept_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# This filter catches any command that looks like /accept_NUMBER or /accept_all
@app.on_message(filters.regex(r"^/accept_(all|\d+)$") & (filters.group | filters.channel))
async def targeted_approve(client, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # 1. Check Admin Permissions
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]:
            await message.reply_text("❌ Access Denied: Admin only.")
            return
    except Exception:
        await message.reply_text("❌ Error: I cannot verify your admin status.")
        return

    # 2. Parse the command to find the limit
    # The message text will be like "/accept_50"
    command_text = message.text.lower()
    match = re.search(r"^/accept_(all|\d+)", command_text)
    
    if not match:
        return

    argument = match.group(1) # This will be "200", "10", or "all"
    
    if argument == "all":
        limit = float('inf') # Infinite
        status_text = "Processing **ALL** requests..."
    else:
        limit = int(argument)
        status_text = f"Processing **{limit}** requests..."

    # Send initial status
    status_msg = await message.reply_text(f"⏳ {status_text}")
    
    count = 0
    
    try:
        # 3. Iterate through pending requests
        async for request in client.get_chat_join_requests(chat_id):
            
            # Check if we reached the limit
            if count >= limit:
                break
                
            try:
                await client.approve_chat_join_request(chat_id, request.user.id)
                count += 1
                
                # Update log every 20 users so we don't spam the console
                if count % 20 == 0:
                    logger.info(f"Approved {count}/{argument}...")
                    # Update the Telegram message every 50 users to show progress
                    if count % 50 == 0:
                        try:
                            await status_msg.edit_text(f"⏳ Progress: Approved {count} users...")
                        except:
                            pass

            except FloodWait as e:
                # If Telegram says "Too Fast", we wait
                wait_time = e.value + 1
                logger.warning(f"Rate limit hit! Sleeping for {wait_time} seconds.")
                await status_msg.edit_text(f"⚠️ Telegram Rate Limit hit. Pausing for {wait_time}s...")
                await asyncio.sleep(wait_time)
                # After sleeping, we try to approve this user again (loop continues)
                
            except Exception as e:
                logger.error(f"Failed to approve user: {e}")

        # 4. Final Report
        await status_msg.edit_text(f"✅ **Task Completed**\n\nSuccessfully approved: {count} members.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error occurred: {str(e)}")

print("Bot Started. Use commands like /accept_10 or /accept_all")
app.run()
