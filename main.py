import asyncio
import logging
import re
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait

# --- CONFIGURATION (Added as requested) ---
API_ID = 27343489
API_HASH = "bb6da47b900d646484f58a5d19d64a68"
BOT_TOKEN = "8207099625:AAF6DDZCZziiGUYrcETHiubC3SI4P0IecAs"

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

@app.on_message(filters.regex(r"^/accept_(all|\d+)$") & (filters.group | filters.channel))
async def targeted_approve(client, message):
    chat_id = message.chat.id
    
    # --- SECURITY CHECK (FIXED) ---
    # This block fixes the "NoneType object has no attribute id" error
    
    # Case 1: Standard User/Admin in a Group
    if message.from_user:
        user_id = message.from_user.id
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]:
                await message.reply_text("❌ Access Denied: Admin only.", quote=True)
                return
        except Exception as e:
            logger.error(f"Admin check failed: {e}")
            return

    # Case 2: Channel Post or Anonymous Admin (User is None)
    # If the message comes from the chat itself (sender_chat), it is valid.
    elif message.sender_chat:
        if message.sender_chat.id != chat_id:
            return
    else:
        # Unknown sender type, ignore
        return

    # --- PARSE COMMAND ---
    command_text = message.text.lower()
    match = re.search(r"^/accept_(all|\d+)", command_text)
    
    if not match:
        return

    argument = match.group(1) 
    
    if argument == "all":
        limit = float('inf')
        status_text = "Processing **ALL** requests..."
    else:
        limit = int(argument)
        status_text = f"Processing **{limit}** requests..."

    # Send status message
    try:
        status_msg = await message.reply_text(f"⏳ {status_text}", quote=True)
    except Exception as e:
        logger.error(f"Could not send reply: {e}")
        return
    
    count = 0
    
    try:
        # --- PROCESS REQUESTS ---
        async for request in client.get_chat_join_requests(chat_id):
            
            if count >= limit:
                break
                
            try:
                await client.approve_chat_join_request(chat_id, request.user.id)
                count += 1
                
                # Log progress
                if count % 20 == 0:
                    logger.info(f"Approved {count} users...")
                    
                # Update Message (Edit less frequently to avoid Rate Limits)
                if count % 50 == 0:
                    try:
                        await status_msg.edit_text(f"⏳ Progress: Approved {count} users...")
                    except:
                        pass

            except FloodWait as e:
                wait_time = e.value + 1
                logger.warning(f"Sleeping for {wait_time}s due to FloodWait...")
                await status_msg.edit_text(f"⚠️ Rate Limit Hit. Pausing for {wait_time}s...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Failed to approve user: {e}")

        await status_msg.edit_text(f"✅ **Task Completed**\n\nSuccessfully approved: {count} members.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

print("Bot Started. Send command in Channel.")
app.run()
