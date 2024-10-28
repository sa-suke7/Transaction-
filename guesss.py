import time
import os
import telebot
from telebot import types
from bs4 import BeautifulSoup
import httpx
import urllib
import asyncio
import http.server
import socketserver
from telebot import TeleBot, types

API_TOKEN = os.getenv('API_TOKEN')

CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')

developer_id = int(os.getenv('developer_id'))  

bot = telebot.TeleBot(API_TOKEN)

headers = {
    'Host': 'ar.akinator.com',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://ar.akinator.com/game',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
}

async def fetch_game_data():
    async with httpx.AsyncClient(http2=True, timeout=httpx.Timeout(10.0)) as client:
        try:
            response = await client.post("https://ar.akinator.com/game", headers=headers, data="cm=false&sid=1")
            soup = BeautifulSoup(response.text, 'html.parser')

            p_element = soup.find('p', id='question-label')
            if not p_element:
                return None, None, None
            question = p_element.get_text()

            form_element = soup.find('form', id='askSoundlike')
            if not form_element:
                return None, None, None
            session = form_element.find('input', id='session')['value']
            signature = form_element.find('input', id='signature')['value']

            return question, session, signature

        except httpx.ReadTimeout:
            return None, None, None  # تعيد القيمة None عند حدوث timeout

# تعريف welcome_text كمتغير عام
welcome_text = "- أهـلاً بك عزيزي <a href='http://t.me/{username}'>{name}</a> انا اكيـنـاتـور                     \n \n" \
               "• عليك التفكير بشخصية حقيقية أو خيالية.          \n" \
               "• وأنا سأحاول معرفة الشخصية التي فكرت بها."

@bot.message_handler(commands=['start'])
def start_game(message):
    chat_id = message.chat.id
    # التحقق من الاشتراك في القناة
    check_subscription(chat_id, message)

def check_subscription(chat_id, message):
    time.sleep(1)  # تأخير بسيط للسماح بتحديث حالة الاشتراك
    
    chat_member = bot.get_chat_member(CHANNEL_USERNAME, chat_id)
    if chat_member.status in ['member', 'administrator', 'creator']:
        # الترحيب بالمستخدم إذا كان مشتركًا
        formatted_text = welcome_text.format(username=message.from_user.username, name=message.from_user.first_name)
        markup = create_start_markup()
        bot.send_message(chat_id, formatted_text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
    else:
        # إذا لم يكن المستخدم مشتركًا، إظهار رسالة الاشتراك
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⦗ Python tools ⦘", url="https://t.me/EREN_PYTHON"))
        markup.add(types.InlineKeyboardButton("تحقق", callback_data='verify'))
        
        bot.send_message(chat_id, 
                         "عذرا عزيزي... يجب الإشتراك في قناة البوت الرسمية حتى تتمكن من إستخدام البوت...🙋‍♂\n"
                         "إشترك هنا ⏬⏬ ثم إضغط /start 👉", 
                         reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'verify')
def verify_subscription(call):
    chat_id = call.message.chat.id
    time.sleep(1)  # تأخير بسيط قبل إعادة التحقق

    chat_member = bot.get_chat_member(CHANNEL_USERNAME, chat_id)
    if chat_member.status in ['member', 'administrator', 'creator']:
        # إظهار رسالة تحقق منبثقة للمستخدم
        bot.answer_callback_query(call.id, "تم التحقق ✔️", show_alert=True)
        
        # حذف الرسالة الأصلية بعد التحقق
        bot.delete_message(chat_id, call.message.message_id)             
        
        # إرسال رسالة الترحيب
        formatted_text = welcome_text.format(username=call.from_user.username, name=call.from_user.first_name)
        markup = create_start_markup()
        bot.send_message(chat_id, formatted_text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
    else:
        # إظهار رسالة عدم الاشتراك للمستخدم في نافذة منبثقة
        bot.answer_callback_query(call.id, "عذراً، لم تشترك في القناة بعد.", show_alert=True)

def create_start_markup():
    markup = types.InlineKeyboardMarkup()
    start_button = types.InlineKeyboardButton("- بدء اللعب . ", callback_data='start_game')
    dev_button = types.InlineKeyboardButton("- Developer .", url="t.me/PP2P6")
    share_button = types.InlineKeyboardButton("- شارك البوت .", switch_inline_query="")
    world_button = types.InlineKeyboardButton("⦗ WORLD EREN ⦘", url="https://t.me/ERENYA0")
    markup.row(start_button)
    markup.row(dev_button, share_button)
    markup.add(world_button)
    return markup


    markup = create_start_markup()
    bot.send_message(chat_id, welcome_text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
def create_start_markup():
    markup = types.InlineKeyboardMarkup()
    start_button = types.InlineKeyboardButton("- بدء اللعب . ", callback_data='start_game')
    dev_button = types.InlineKeyboardButton("- Developer .", url="t.me/PP2P6")
    share_button = types.InlineKeyboardButton("- شارك البوت .", switch_inline_query="")
    world_button = types.InlineKeyboardButton("⦗ WORLD EREN ⦘", url="https://t.me/ERENYA0")
    markup.row(start_button)
    markup.row(dev_button, share_button)
    markup.add(world_button)
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'start_game')
def handle_start_game(call):
    chat_id = call.message.chat.id
    bot.edit_message_text("• جاري التحميل...", chat_id=chat_id, message_id=call.message.message_id)
    asyncio.run(init_game(chat_id, call.message.message_id))

async def init_game(chat_id, message_id):
    question, session, signature = await fetch_game_data()
    if question:
        send_question_with_options(chat_id, question, session, signature, message_id)
    else:
        await asyncio.sleep(2)  # انتظر قليلاً قبل إعادة المحاولة
        await init_game(chat_id, message_id)  # إعادة المحاولة بدون رسالة

def send_question_with_options(chat_id, question, session, signature, message_id):
    markup = create_answer_markup()
    bot.session_data[chat_id] = {'session': session, 'signature': signature, 'step': 0, 'progression': 0.0}
    formatted_question = format_question(question, bot.session_data[chat_id]['step'], bot.session_data[chat_id]['progression'])
    bot.edit_message_text(formatted_question, chat_id=chat_id, message_id=message_id, reply_markup=markup, parse_mode='HTML')

def create_answer_markup():
    markup = types.InlineKeyboardMarkup()
    maybe_button = types.InlineKeyboardButton("من الممكن", callback_data="من الممكن")
    likely_not_button = types.InlineKeyboardButton("الظاهر لا", callback_data="الظاهر لا")
    yes_button = types.InlineKeyboardButton("نعم", callback_data="نعم")
    idk_button = types.InlineKeyboardButton("أنا لا أعلم", callback_data="أنا لا أعلم")
    no_button = types.InlineKeyboardButton("لا", callback_data="لا")
    back_button = types.InlineKeyboardButton("• رجوع •", callback_data="رجوع")
    markup.row(maybe_button, likely_not_button)
    markup.row(yes_button, idk_button, no_button)
    markup.add(back_button)
    return markup

def format_question(question, step, progression):
    progress_bar = "▓" * int(progression / 10) + "░" * (10 - int(progression / 10))
    return f"• السؤال #{step + 1 }\n➖➖➖➖➖\n<b>{question}</b>\n➖➖➖➖➖\n• نسبة الوصول إلى النتيجة: {progress_bar} {progression:.1f}%"

@bot.callback_query_handler(func=lambda call: call.data in ["نعم", "لا", "أنا لا أعلم", "من الممكن", "الظاهر لا"])
def handle_answer(call):
    chat_id = call.message.chat.id
    bot.edit_message_text("• جاري التحميل...", chat_id=chat_id, message_id=call.message.message_id)
    asyncio.run(process_answer(chat_id, call))

async def process_answer(chat_id, call):
    answer_mapping = {
        "نعم": 0,
        "لا": 1,
        "أنا لا أعلم": 2,
        "من الممكن": 3,
        "الظاهر لا": 4
    }
    answer = answer_mapping[call.data]
    session_data = bot.session_data.get(chat_id)

    if not session_data:
        bot.send_message(chat_id, "لقد انتهت الجلسة ابدأ اللعبه من جديد /start ")
        return

    data = f"step={session_data['step']}&progression={session_data['progression']:.5f}&sid=NaN&cm=false&answer={answer}&session={urllib.parse.quote(session_data['session'])}&signature={urllib.parse.quote(session_data['signature'])}"

    async with httpx.AsyncClient(http2=True, timeout=httpx.Timeout(10.0)) as client:
        try:
            response = await client.post("https://ar.akinator.com/answer", headers=headers, data=data)
            re_json = response.json()

            if 'question' in re_json:
                new_question = re_json['question']
                progression = float(re_json['progression'])
                step = int(re_json['step'])

                session_data['step'] = step
                session_data['progression'] = progression

                formatted_question = format_question(new_question, step, progression)
                bot.edit_message_text(formatted_question, chat_id=chat_id, message_id=call.message.message_id, reply_markup=create_answer_markup(), parse_mode='HTML')
            elif 'description_proposition' in re_json:
                text = f"• أنت تفكر في: <b>{re_json['name_proposition']}</b> ( {re_json['description_proposition']} ) 😇"
                photo_url = re_json.get('photo')
                
                bot.delete_message(chat_id, call.message.message_id)  # حذف رسالة "جاري التحميل..."
                if photo_url:
                    bot.send_photo(chat_id=chat_id, photo=photo_url, caption=text, parse_mode='HTML')
                else:
                    bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')

        except httpx.ReadTimeout:
            await asyncio.sleep(2)  # انتظر قليلاً قبل إعادة المحاولة
            await process_answer(chat_id, call)  # إعادة المحاولة

@bot.callback_query_handler(func=lambda call: call.data == "رجوع")
def handle_back(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # حذف بيانات الجلسة الحالية
    bot.session_data.pop(chat_id, None)
    
    # حذف الرسالة الحالية
    bot.delete_message(chat_id, message_id)
    
    # إعادة المستخدم إلى القائمة الرئيسية مع عرض اسمه ومعرفه بشكل صحيح
    welcome_text = f"- أهـلاً بك عزيزي <a href='http://t.me/{call.from_user.username}'>{call.from_user.first_name}</a> انا اكيـنـاتـور                     \n \n" \
                   "• عليك التفكير بشخصية حقيقية أو خيالية.          \n" \
                   "• وأنا سأحاول معرفة الشخصية التي فكرت بها."

    markup = create_start_markup()
    bot.send_message(chat_id, welcome_text, parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)

@bot.message_handler(commands=['id'])
def send_user_id(message):
    user_id = message.from_user.id
    bot.send_message(message.chat.id, f"ID: `{user_id}`", parse_mode='Markdown')

bot.session_data = {}


def run_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", 8000), handler) as httpd:
        print("Serving on port 8000")
        httpd.serve_forever()

while True:
    try:
        bot.polling()
    except Exception as e:
        print(f"حدث خطأ: {e}. سيتم إعادة تشغيل البوت بعد 5 ثواني...")
        time.sleep(5)
