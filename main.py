import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
#from config import Config
from database import is_authorized, add_user, set_channel_db, get_channel_db

logging.basicConfig(level=logging.INFO)

# User Account Session (Terminal par OTP maangega)
app = Client(
    "arya_userbot_session", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH
)

@app.on_message(filters.command("index", prefixes="/") & filters.me)
async def bulk_index(client, message):
    if len(message.command) < 3:
        return await message.edit("❌ **Usage:** `/index [Source_ID] [Dest_ID]`")

    source_chat = int(message.command[1])
    dest_chat = int(message.command[2])

    await set_channel_db("xy_channel", source_chat)
    await set_channel_db("xy2_channel", dest_chat)

    await message.edit("⏳ **Indexing Shuru Ho Rahi Hai...**")
    count = 0
    me = await client.get_me()
    user_link = f"https://t.me/{me.username}" if me.username else f"tg://user?id={me.id}"

    try:
        async for msg in client.get_chat_history(source_chat):
            if msg.video or msg.document:
                count += 1
                title = msg.caption.split('\n')[0] if msg.caption else f"Lecture {count}"
                
                btn = InlineKeyboardMarkup([[
                    InlineKeyboardButton("Watch Online 🎥", url=f"{user_link}?start={msg.id}")
                ]])

                await client.send_message(
                    chat_id=dest_chat,
                    text=f"📂 **{title}**\n\n✅ *Userbot Protected Content*",
                    reply_markup=btn,
                    parse_mode=enums.ParseMode.HTML
                )
                
                if count % 15 == 0:
                    await message.edit(f"🔄 **Processed {count} videos...**")
                    await asyncio.sleep(2)

        await message.edit(f"🎊 **Indexing Poori Ho Gayi!**\nTotal: `{count}` files indexed.")
    except Exception as e:
        await message.edit(f"❌ **Error:** `{e}`")

@app.on_message(filters.command("auth", prefixes="/") & filters.me)
async def auth_handler(client, message):
    if len(message.command) > 1:
        user_id = int(message.command[1])
        await add_user(user_id)
        await message.edit(f"✅ User `{user_id}` authorized!")
    else:
        await message.edit("Usage: `/auth [USER_ID]`")

@app.on_message(filters.command("start", prefixes="/") & filters.private)
async def start_handler(client, message):
    if not await is_authorized(message.from_user.id):
        return await message.reply_text("❌ Aap authorized nahi hain.")

    if len(message.command) > 1:
        try:
            msg_id = int(message.command[1])
            source_id = await get_channel_db("xy_channel")
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=source_id,
                message_id=msg_id,
                protect_content=True # Screen record/Forward block
            )
        except Exception:
            await message.reply_text("❌ File nahi mili.")
    else:
        await message.reply_text("👋 Welcome! Course access karne ke liye index channel check karein.")

print("🚀 Userbot Starting... Terminal par Phone/OTP check karein.")
app.run()
