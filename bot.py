import os
import asyncio
import telebot
from playwright.async_api import async_playwright

# তোমার দেওয়া টেস্ট টোকেন
TOKEN = '8651423664:AAEQu1P-mWgsCYRtW_TMBDoGStWjMTEJAv4'
bot = telebot.TeleBot(TOKEN)

async def get_whatsapp_pfp(phone):
    async with async_playwright() as p:
        # রেন্ডারে চালানোর জন্য ব্রাউজার লঞ্চ সেটিংস
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        )
        
        # নোট: এখানে পরে তোমার সেশন ইনজেক্ট করা যাবে
        page = await context.new_page()
        
        try:
            # সরাসরি নাম্বারের চ্যাট লিঙ্কে যাওয়া
            url = f"https://web.whatsapp.com/send?phone={phone}"
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # হোয়াটসঅ্যাপ লোড হওয়ার জন্য সময় দিন
            await asyncio.sleep(20) 
            
            # প্রোফাইল পিকচারের এলিমেন্ট খোঁজা
            img_selector = 'header img'
            await page.wait_for_selector(img_selector, timeout=15000)
            img_url = await page.get_attribute(img_selector, "src")
            return img_url
        except Exception as e:
            print(f"Error fetching: {e}")
            return None
        finally:
            await browser.close()

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "ভাই, নাম্বার দাও (Country code সহ, যেমন: 88017...), আমি ছবি নিয়ে আসছি!")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    phone = message.text.strip()
    if not phone.isdigit():
        bot.reply_to(message, "❌ ভাই শুধু নাম্বার দাও।")
        return

    bot.reply_to(message, f"🔍 {phone} এর ছবি খোঁজা হচ্ছে, একটু সময় লাগবে...")
    
    # এসিনক্রোনাস রানার
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        photo_url = loop.run_until_complete(get_whatsapp_pfp(phone))
        loop.close()
        
        if photo_url:
            bot.send_photo(message.chat.id, photo_url, caption=f"✅ {phone} এর প্রোফাইল পিকচার")
        else:
            bot.reply_to(message, "❌ ছবি পাওয়া যায়নি। হয়তো নাম্বারটি ভুল বা হোয়াটসঅ্যাপে নেই।")
    except Exception as e:
        bot.reply_to(message, "⚠️ সার্ভারে সমস্যা হয়েছে, আবার ট্রাই করো।")

print("বট সচল আছে...")
bot.polling()
