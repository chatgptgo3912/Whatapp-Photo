import os
import asyncio
import telebot
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

# রেন্ডারকে খুশি রাখার জন্য
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

# তোমার সেই টেস্ট টোকেন
TOKEN = '8651423664:AAEQu1P-mWgsCYRtW_TMBDoGStWjMTEJAv4'
bot = telebot.TeleBot(TOKEN)
SESSION_DIR = "user_session" # এখানে তোমার লগইন ডাটা সেভ থাকবে

async def login_process(chat_id):
    async with async_playwright() as p:
        bot.send_message(chat_id, "⏳ ব্রাউজার ওপেন হচ্ছে... কিউআর কোড আসার পর তোমাকে ছবি পাঠাবো।")
        
        # সেশন সেভ রাখার জন্য সলিড মেথড
        context = await p.chromium.launch_persistent_context(
            SESSION_DIR, 
            headless=True, 
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await context.new_page()
        
        try:
            await page.goto("https://web.whatsapp.com", wait_until="networkidle", timeout=60000)
            await asyncio.sleep(10) # কিউআর লোড হওয়ার সময়
            
            # কিউআর কোডের স্ক্রিনশট
            await page.screenshot(path="qr.png")
            with open("qr.png", "rb") as qr:
                bot.send_photo(chat_id, qr, caption="📸 ভাই, এই কোডটা তোমার ফোন দিয়ে স্ক্যান করো।\n(Linked Devices-এ গিয়ে স্ক্যান করো)")
            
            # স্ক্যান করার জন্য ১ মিনিট সময় দেওয়া হলো
            await asyncio.sleep(60) 
            await context.close()
            bot.send_message(chat_id, "✅ প্রসেস শেষ! এখন নাম্বার পাঠাও, তোমার লগইন করা সেশন দিয়ে ছবি আনবো।")
        except Exception as e:
            bot.send_message(chat_id, f"❌ সমস্যা: {str(e)}")

async def fetch_photo(phone, chat_id):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            SESSION_DIR, headless=True, args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await context.new_page()
        try:
            await page.goto(f"https://web.whatsapp.com/send?phone={phone}", wait_until="networkidle", timeout=60000)
            await asyncio.sleep(15) # হোয়াটসঅ্যাপের ভেতরে ঢোকার সময়
            
            img_selector = 'header img'
            await page.wait_for_selector(img_selector, timeout=15000)
            img_url = await page.get_attribute(img_selector, "src")
            
            if img_url:
                bot.send_photo(chat_id, img_url, caption=f"✅ {phone} এর প্রোফাইল পিকচার।")
            else:
                bot.send_message(chat_id, "❌ প্রোফাইল পিকচার খুঁজে পাওয়া যায়নি।")
        except:
            bot.send_message(chat_id, "⚠️ সেশন কাজ করছে না। আবার /login করে স্ক্যান করো।")
        finally:
            await context.close()

# কমান্ড হ্যান্ডলার
@bot.message_handler(commands=['login'])
def do_login(message):
    Thread(target=lambda: asyncio.run(login_process(message.chat.id))).start()

@bot.message_handler(func=lambda m: True)
def do_fetch(message):
    phone = "".join(filter(str.isdigit, message.text))
    if len(phone) >= 10:
        bot.reply_to(message, "🔍 ছবি খোঁজা হচ্ছে, একটু সময় দাও...")
        Thread(target=lambda: asyncio.run(fetch_photo(phone, message.chat.id))).start()
    else:
        bot.reply_to(message, "❌ ভাই সঠিক নাম্বার দাও অথবা /login লেখো।")

if __name__ == "__main__":
    keep_alive()
    print("বট চলছে...")
    bot.polling(none_stop=True)
