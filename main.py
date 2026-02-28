import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait

# --- CONFIGURATION ---
API_ID = 27343489
API_HASH = "bb6da47b900d646484f58a5d19d64a68"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- GLOBAL VARIABLES ---
active_tasks = {}

# --- INITIALIZE CLIENT ---
app = Client("public_worker_account", api_id=API_ID, api_hash=API_HASH)

# --- HELPER: OFFICIAL MESSAGE TEXT ---
def get_help_text():
    return (
        "🛡️ <b>Join Request Manager</b>\n\n"
        "ℹ️ <b>How to Use:</b>\n"
        "1. Is User ID ko apne Channel/Group mein <b>Admin</b> banayein.\n"
        "2. <b>'Invite Users via Link'</b> ki permission ON rakhein.\n"
        "3. Neeche diye gaye commands use karein.\n\n"
        "⚙️ <b>Commands:</b>\n"
        "• <code>/accept 100</code> » Sirf 100 users accept karein.\n"
        "• <code>/accept all</code> » Saari pending requests accept karein.\n"
        "• <code>/cancel</code> » Process ko beech mein rokein."
    )

# --- 1. START COMMAND ---
@app.on_message(filters.command("start", prefixes="/") & filters.private)
async def start_handler(client, message):
    # Professional HTML Message
    await message.reply_text(
        get_help_text(),
        quote=True,
        parse_mode=enums.ParseMode.HTML
    )

# --- 2. ACCEPT COMMAND ---
# FIX: 'filters.supergroup' hata diya hai, ab ye perfectly chalega
@app.on_message(filters.command("accept", prefixes="/") & (filters.channel | filters.group))
async def approve_requests(client, message):
    chat_id = message.chat.id
    
    # --- CHECK ADMIN RIGHTS ---
    # Check karein ki command dene wala admin hai ya nahi
    try:
        if message.from_user:
            member = await client.get_chat_member(chat_id, message.from_user.id)
            if member.status not in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]:
                return 
    except:
        pass 

    # --- PARSE COMMAND ---
    args = message.command
    # Agar user ne sirf /accept likha hai, toh usse Help Message dikhao
    if len(args) < 2:
        await message.reply_text(
            get_help_text(),
            quote=True,
            parse_mode=enums.ParseMode.HTML
        )
        return
        
    arg = args[1].lower()
    limit = float('inf') if arg == "all" else (int(arg) if arg.isdigit() else None)
    
    if limit is None:
        await message.reply_text("❌ <b>Error:</b> Kripya sahi number daalein ya <code>all</code> likhein.", parse_mode=enums.ParseMode.HTML)
        return

    # --- PROCESS START ---
    active_tasks[chat_id] = True
    
    # Official Status Message
    status_msg = await message.reply_text(
        f"⏳ <b>Processing Started...</b>\nTarget: <code>{arg.upper()}</code> Members\n\n<i>Rokne ke liye /cancel dabayein.</i>",
        parse_mode=enums.ParseMode.HTML
    )
    
    count = 0
    try:
        async for request in client.get_chat_join_requests(chat_id):
            # Check Cancel
            if not active_tasks.get(chat_id, False):
                await status_msg.edit_text(
                    f"🛑 <b>Process Cancelled!</b>\nApproved: <b>{count}</b> users.",
                    parse_mode=enums.ParseMode.HTML
                )
                return

            if count >= limit:
                break

            try:
                await client.approve_chat_join_request(chat_id, request.user.id)
                count += 1
                
                # Update Status (Every 20 users)
                if count % 20 == 0:
                    try:
                        await status_msg.edit_text(
                            f"🔄 <b>Working...</b>\nApproved: <b>{count}</b> users\n\n<i>Type /cancel to stop.</i>",
                            parse_mode=enums.ParseMode.HTML
                        )
                    except:
                        pass
                await asyncio.sleep(0.3) 

            except FloodWait as e:
                await status_msg.edit_text(f"😴 <b>Telegram Limit Hit:</b> {e.value}s wait kar raha hoon...", parse_mode=enums.ParseMode.HTML)
                await asyncio.sleep(e.value + 2)
            except Exception as e:
                logger.error(f"Error: {e}")

        # --- COMPLETED MESSAGE ---
        await status_msg.edit_text(
            f"✅ <b>Task Completed Successfully!</b>\n\n👥 Total Approved: <b>{count}</b> members.",
            parse_mode=enums.ParseMode.HTML
        )

    except Exception as e:
        await status_msg.edit_text(
            f"❌ <b>Error Occurred:</b>\n<code>{e}</code>\n\n<i>Make sure mujhe Admin banaya hai!</i>",
            parse_mode=enums.ParseMode.HTML
        )
    
    active_tasks[chat_id] = False

# --- 3. CANCEL COMMAND ---
# FIX: Yahan bhi fix kar diya hai
@app.on_message(filters.command("cancel", prefixes="/") & (filters.channel | filters.group))
async def cancel_handler(client, message):
    chat_id = message.chat.id
    if active_tasks.get(chat_id):
        active_tasks[chat_id] = False
        await message.reply_text("🛑 <b>Stopping...</b>", parse_mode=enums.ParseMode.HTML)
    else:
        await message.reply_text("ℹ️ Koi active process nahi chal raha.", quote=True)

# --- RUN ---
print("✅ Official Userbot Started (Fixed Version)...")
app.run()
