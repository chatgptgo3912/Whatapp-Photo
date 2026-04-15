import os
import asyncio
import telebot
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

# ১. রেন্ডারকে জাগিয়ে রাখার জন্য Flask
app = Flask('')
@app.route('/')
def home(): return "WhatsApp QR Bot is Active!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

TOKEN = '8651423664:AAEQu1P-mWgsCYRtW_TMBDoGStWjMTEJAv4'
bot = telebot.TeleBot(TOKEN)

# সেশন সেভ করার ফোল্ডার (রেন্ডারে এটা সাময়িক হবে)
SESSION_DIR = "user_data"

async def get_qr_and_login(chat_id):
    async with async_playwright() as p:
        # সেশন ডাটা ধরে রাখার জন্য launch_persistent_context ব্যবহার করা হয়েছে
        context = await p.chromium.launch_persistent_context(
            SESSION_DIR,
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await context.new_page()
        
        try:
            await page.goto("https://web.whatsapp.com", wait_until="networkidle")
            
            # কিউআর কোড আসার জন্য অপেক্ষা
            bot.send_message(chat_id, "⏳ কিউআর কোড জেনারেট হচ্ছে, একটু দাঁড়াও...")
            await asyncio.sleep(10)
            
            # কিউআর কোডের স্ক্রিনশট নেওয়া
            await page.screenshot(path="qr.png")
            with open("qr.png", "rb") as qr:
                bot.send_photo(chat_id, qr, caption="📸 ভাই, তোমার হোয়াটসঅ্যাপ দিয়ে এই কোডটি স্ক্যান করো।\n(Linked Devices এ গিয়ে স্ক্যান করো)")
            
            # লগইন হওয়া পর্যন্ত অপেক্ষা (৬০ সেকেন্ড সময় পাবে)
            bot.send_message(chat_id, "🕒 তোমার কাছে ৬০ সেকেন্ড সময় আছে স্ক্যান করার জন্য...")
            await asyncio.sleep(60)
            
            await context.close()
            bot.send_message(chat_id, "✅ লগইন প্রসেস শেষ! এখন তুমি নাম্বার পাঠাতে পারো।")
        except Exception as e:
            bot.send_message(chat_id, f"❌ এরর: {str(e)}")

async def fetch_pfp(phone, chat_id):
    async with async_playwright() as p:
        # আগের সেভ করা সেশন দিয়ে ব্রাউজার খোলা
        context = await p.chromium.launch_persistent_context(
            SESSION_DIR,
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await context.new_page()
        try:
            url = f"https://web.whatsapp.com/send?phone={phone}"
            await page.goto(url, wait_until="networkidle")
            await asyncio.sleep(15) # প্রোফাইল লোড হতে সময় লাগে
            
            img_selector = 'header img'
            await page.wait_for_selector(img_selector, timeout=20000)
            img_url = await page.get_attribute(img_selector, "src")
            
            if img_url:
                bot.send_photo(chat_id, img_url, caption=f"✅ {phone} এর ছবি পাওয়া গেছে।")
            else:
                bot.send_message(chat_id, "❌ ছবি পাওয়া যায়নি।")
        except:
            bot.send_message(chat_id, "⚠️ সেশন কাজ করছে না বা ছবি লক করা। আবার /login করো।")
        finally:
            await context.close()

@bot.message_handler(commands=['login'])
def login_command(message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(get_qr_and_login(message.chat.id))

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    phone = "".join(filter(str.isdigit, message.text))
    if len(phone) >= 10:
        bot.reply_to(message, "🔍 ছবি খোঁজা হচ্ছে...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(fetch_pfp(phone, message.chat.id))
    else:
        bot.reply_to(message, "❌ সঠিক নাম্বার দাও ভাই।")

if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
