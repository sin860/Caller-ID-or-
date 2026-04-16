import json
import base64
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import telebot
from telebot import types
import io
#tele:@sin_php
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TOKEN = "token"
bot = telebot.TeleBot(TOKEN)
DYNAMIC_SEED = "dQqkLIEQXc9TBIkc"
URL = "https://apinb.numberbooksocial.com/Nbchat/search"
HEADERS = {
    'User-Agent': "okhttp/4.10.0",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'handset': "3",
    'imei': "L8qsWDDv7ZekjaVdNwkOVinTkNw2oOmgesrOuYwoaxg=",
    'osversion': "7rzKzOmHINIjYogKkS6auA==",
    'mnc': "e6zIuVQs/DoRa+uCLbGiZw==",
    'mcc': "KffVx4bqAxdUAihBCwXJ1w==",
    'imsi': "5HonKIhLjfWxn2Ouy6fJVQ==",
    'adsid': "wkziJtwnGGsLk3RrbkWtLnrlvfEy561CM/M4Rmda/TPTmvx5LtcdPlpySmSEHyvJ",
    'appversion1': "3.0",
    'pushid': "J8Db3jDuTWWwedQzlzhWqJcQM3f+u3xSKyPMqGQGGyqcM+d+WR/O763sHqFnwJy/dHVMUhBiYXtB2kuPk41+EEWbSRxoHmuaoNvnOUEr3FqrPYEHnn2bma6KouMs1ABpAGTYvbR2ytx2vr2uPee3JGQbRAYunq6b+KIVMn/qYDri62QlYWStmHQ42B/TnIaF",
    'hasvoip': "+y+18BHvSwgTEgiCdtXEPA==",
    'androidid': "L8qsWDDv7ZekjaVdNwkOVinTkNw2oOmgesrOuYwoaxg=",
    'mo': "FjpCtAxR5u5ro/jzJEfbLg==",
    'code': "sT/+0xUyZNX60INxcROHaQ==",
    'CodeS': "sT/+0xUyZNX60INxcROHaQ==",
    'activemnc': "KffVx4bqAxdUAihBCwXJ1w==",
    'appversion': "XM6ufL5C5QNDH/iYbcknsQ==",
    'device': "GcCJBbAsL6MURrB4xwbaGw==",
    'lang': "88hiyrHJ1+stpDRiX+2jQQ==",
    'idlang': "2",
    'Content-Language': "en-US",
    'Content-Type': "text/plain; charset=utf-8"
}

user_sessions = {}
def sin_encrypt(plaintext, seed):
    key = seed.encode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, key)
    return base64.b64encode(cipher.encrypt(pad(plaintext.encode('utf-8'), 16))).decode('utf-8')

def sin_decrypt(ciphertext, seed):
    try:
        key = seed.encode('utf-8')
        cipher = AES.new(key, AES.MODE_CBC, key)
        return unpad(cipher.decrypt(base64.b64decode(ciphertext)), 16).decode('utf-8')
    except: return None
def display_results(chat_id, data):
    if "profiles" in data and data["profiles"]:
        for p in data["profiles"]:
            name = p.get('name', 'N/A')
            mo = p['numbers'][0].get('mo') if p.get('numbers') else 'N/A'
            status = p.get('status') or 'غير متوفرة'
            pid = p.get('id', 'N/A')
            job = p.get('jobtitle') or 'N/A'
            
            info = (f"<b> الاسم الكامل:</b> {name}\n"
                    f"<b> الرقم:</b> {mo}\n"
                    f"<b> الحالة:</b> {status}\n"
                    f"<b> المعرف:</b> <code>{pid}</code>\n"
                    f"<b> الوظيفة:</b> {job}\n\n"
                    f"<b>dev : @SIN_PHP</b>")
            
            try:
                bot.send_message(chat_id, info, parse_mode="HTML")
            except:
                
                clean_info = info.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
                bot.send_message(chat_id, clean_info)
    else:
        bot.send_message(chat_id, " لم يتم العثور على أي معلومات لهذا الرقم.")
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "مرحبا ارسل الرقم بدون الصيغه الدوله وبدون الصفر ")

@bot.message_handler(func=lambda message: True)
def handle_request(message):
    target = message.text.strip().lstrip('0').replace('+964', '')
    if not target.isdigit():
        return

    user_sessions[message.chat.id] = target
    bot.reply_to(message, " جاري فحص الحماية والاتصال بالسيرفر...")

   
    search_json = f'{{"code":"964","iscallerid":"0","latitude":"","longitude":"","rowindex":0,"search":"{target}"}}'
    payload = sin_encrypt(search_json, DYNAMIC_SEED)

    try:
        res = requests.post(URL, data=payload, headers=HEADERS, verify=False, timeout=15)
        decoded = sin_decrypt(res.text, DYNAMIC_SEED)
        
        if decoded:
            data = json.loads(decoded)
            status = data.get("statuscode", {})
            captcha_b64 = status.get("captcha_b64", "0")
            
            
            if captcha_b64 != "0":
                img = base64.b64decode(captcha_b64)
                msg = bot.send_photo(message.chat.id, io.BytesIO(img), 
                                     caption="اكتب الارقام الموجوده في الصوره ")
                bot.register_next_step_handler(msg, solve_captcha)
            
            
            elif "profiles" in data and data["profiles"]:
                display_results(message.chat.id, data)
            else:
                bot.reply_to(message, " لم يتم العثور على نتائج.")
        else:
            bot.reply_to(message, " فشل فك التشفير. تأكد من الـ Seed بفريدا.")
    except Exception as e:
        bot.reply_to(message, f" خطأ في الاتصال: {str(e)}")

def solve_captcha(message):
    captcha_val = message.text.strip()
    chat_id = message.chat.id
    target = user_sessions.get(chat_id)

    if not captcha_val.isdigit():
        bot.send_message(chat_id, " حل الكابتشا غير صالح. أعد إرسال الرقم للبدء من جديد.")
        return

    bot.send_message(chat_id, " تم استلام الحل، جاري سحب البيانات النهائية...")

   
    final_json = f'{{"captchatext":"{captcha_val}","code":"964","iscallerid":"0","latitude":"","longitude":"","rowindex":0,"search":"{target}"}}'
    payload = sin_encrypt(final_json, DYNAMIC_SEED)

    try:
        res = requests.post(URL, data=payload, headers=HEADERS, verify=False, timeout=15)
        decoded = sin_decrypt(res.text, DYNAMIC_SEED)
        if decoded:
            display_results(chat_id, json.loads(decoded))
        else:
            bot.send_message(chat_id, " فشل استلام البيانات النهائية.")
    except Exception as e:
        bot.send_message(chat_id, f" حدث خطأ: {str(e)}")
bot.infinity_polling()