import os
import asyncio
import telebot
from playwright.async_api import async_playwright
from flask import Flask
from threading import Thread

# ১. রেন্ডারের পোর্ট এরর (Port Scan Timeout) ফিক্স করার জন্য Flask সেটআপ
app = Flask('')

@app.route('/')
def home():
    return "I am alive and running!"

def run():
    # রেন্ডার থেকে অটোমেটিক পোর্ট নম্বর নেওয়ার জন্য os.environ ব্যবহার করা হয়েছে
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ২. তোমার টেলিগ্রাম বট সেটআপ (টেস্ট টোকেন সহ)
TOKEN = '8651423664:AAEQu1P-mWgsCYRtW_TMBDoGStWjMTEJAv4'
bot = telebot.TeleBot(TOKEN)

async def get_whatsapp_pfp(phone):
    async with async_playwright() as p:
        # রেন্ডার সার্ভারের জন্য ব্রাউজার লঞ্চ সেটিংস
        browser = await p.chromium.launch(
            headless=True, 
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # সরাসরি হোয়াটসঅ্যাপ চ্যাট লিঙ্কে যাওয়া
            url = f"https://web.whatsapp.com/send?phone={phone}"
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # হোয়াটসঅ্যাপ লোড হওয়ার জন্য ২০ সেকেন্ড অপেক্ষা
            await asyncio.sleep(20) 
            
            # প্রোফাইল পিকচার এলিমেন্ট খুঁজে বের করা
            img_selector = 'header img'
            await page.wait_for_selector(img_selector, timeout=15000)
            img_url = await page.get_attribute(img_selector, "src")
            return img_url
        except Exception as e:
            print(f"Error fetching PFP: {e}")
            return None
        finally:
            await browser.close()

@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.reply_to(message, "ভাই, নাম্বার দাও (Country Code সহ, যেমন: 88017...), আমি ছবি নিয়ে আসছি!")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    phone = message.text.strip()
    
    # শুধু নাম্বার কি না চেক করা
    if not phone.isdigit():
        bot.reply_to(message, "❌ ভাই শুধু নাম্বার দাও (কোনো স্পেস বা চিহ্ন ছাড়া)।")
        return

    bot.reply_to(message, f"🔍 {phone} এর ছবি খোঁজা হচ্ছে, একটু সময় দাও...")
    
    try:
        # এসিনক্রোনাস ফাংশনটি রান করা
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        photo_url = loop.run_until_complete(get_whatsapp_pfp(phone))
        loop.close()
        
        if photo_url:
            bot.send_photo(message.chat.id, photo_url, caption=f"✅ {phone} এর প্রোফাইল পিকচার")
        else:
            bot.reply_to(message, "❌ ছবি পাওয়া যায়নি। হয়তো নাম্বারটি ভুল বা হোয়াটসঅ্যাপে নেই অথবা প্রাইভেসি অন করা।")
    except Exception as e:
        bot.reply_to(message, f"⚠️ দুঃখিত ভাই, একটা সমস্যা হয়েছে। আবার চেষ্টা করো।")

# ৩. মেইন ফাংশন: ওয়েবসাইট এবং বট একসাথে চালু করা
if __name__ == "__main__":
    keep_alive() # এটা রেন্ডারকে শান্ত রাখবে
    print("বট সচল আছে...")
    # none_stop=True যাতে এরর আসলেও বট বন্ধ না হয়
    bot.polling(none_stop=True)
