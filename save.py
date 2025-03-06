import telethon
from telethon import TelegramClient, events, Button
import re
import asyncio
from datetime import datetime
import json
import os
from telethon.sessions import StringSession
from telethon.errors import PhoneCodeExpiredError, SessionPasswordNeededError


# إعداد بيانات الاعتماد الخاصة بك
API_ID = os.getenv("API_ID") 
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME") # اسم المستخدم لقناتك

# تعريف المتغيرات العالمية
user_accounts = {}  # معجم لتخزين بيانات المستخدمين
developer_id = int(os.getenv("developer_id"))  # معرف المطور
broadcast_state = {}  # حالة الإذاعة
maintenance_mode = False  # حالة الصيانة
maintenance_message = ""  # الرسالة التي تظهر أثناء الصيانة
language = {}  # تخزين لغة المستخدم
user_states = {}  # حالة المستخدمين

# تحميل أو إنشاء ملف المستخدمين
def load_users():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data():
    with open('users.json', 'w') as f:
        json.dump(user_accounts, f, ensure_ascii=False, indent=4)

# تحميل بيانات المستخدمين عند بدء التشغيل
user_accounts = load_users()

# إنشاء عميل Telethon
client = TelegramClient('bot_session', API_ID, API_HASH)

# التحقق من اشتراك المستخدم في القناة
async def check_subscription(user_id):
    try:
        participant = await client(telethon.tl.functions.channels.GetParticipantRequest(
            channel=CHANNEL_USERNAME,
            participant=user_id
        ))
        return True
    except telethon.errors.rpcerrorlist.UserNotParticipantError:
        return False

# إرسال رسالة الاشتراك الإجباري
async def send_subscription_prompt(event):
    sender = await event.get_sender()
    full_name = f"{sender.first_name} {sender.last_name or ''}".strip()
    buttons = [
        [Button.url("⦗ Python tools ⦘", f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [Button.inline("تحقق", b'verify')]
    ]
    await event.reply(
        f"**• عـذراً .. عـزيـزي {full_name} 🤷🏻‍♀**\n"
        f"**• لـ إستخـدام البـوت 👨🏻‍💻**\n"
        f"**• عليك الإشتـراك في قناة البـوت الرسمية 🌐**\n"
        f"**• You must subscribe to the bot channel.**",
        buttons=buttons
    )

# وظيفة عد تنازلي لتحديث الرسالة كل 10 ثوانٍ
async def countdown(event, info_response, delay, date, views):
    for i in range(delay, 0, -10):
        try:
            await info_response.edit(f"""
            ↯︙تاريخ النشر ↫ ⦗ {date} ⦘
            ↯︙عدد المشاهدات ↫ ⦗ {views} ⦘
            ↯︙سيتم حذف المحتوى بعد ↫ ⦗ {i} ⦘ ثانية
            ↯︙قم بحفظه او اعادة التوجيه
            """, parse_mode='html')
            await asyncio.sleep(10)
        except:
            break  # الخروج إذا حدث خطأ مثل حذف الرسالة بالفعل

# وظيفة لحذف الرسائل بعد فترة معينة
async def delete_messages_later(chat_id, message_ids, delay=60):  
    await asyncio.sleep(delay)
    await client.delete_messages(chat_id, message_ids, revoke=True)

# وظيفة لعرض إحصائيات البوت
async def show_bot_stats(event):
    users = load_users()
    user_count = len(users)
    
    stats_message = f"📊 <b>إحصائيات البوت:</b>\n\n👥 <b>عدد المستخدمين:</b> {user_count}\n\n"
    
    for index, (user_id, user_data) in enumerate(users.items(), start=1):
        # التحقق من وجود البيانات قبل الوصول إليها
        name = user_data.get('name', 'غير معروف')
        username = user_data.get('username', 'بدون يوزر')
        stats_message += f"{index}. {name} (@{username}) - ID: {user_id}\n"
    
    # إضافة زر الرجوع
    buttons = [
        [Button.inline("رجوع ↩️", b'back_to_main')]
    ]
    await event.edit(stats_message, parse_mode='html', buttons=buttons)

# إرسال رسالة الأوامر الخاصة بالمطور
async def send_developer_commands(event):
    buttons = [
        [Button.inline("إذاعة 📢", b'broadcast')],  # زر الإذاعة في الأعلى
        [Button.inline("تفعيل الصيانه", b'enable_maintenance'), Button.inline("إيقاف الصيانه", b'disable_maintenance')],  # زر تفعيل وإيقاف الصيانه بجانب بعضهما
        [Button.inline("📊 إحصائيات البوت", b'stats')]  # زر الإحصائيات في الأسفل
    ]
    await event.reply(
        "<b>• مرحبا عزيزي المطور يمكنك في اوامر البوت الخاص بك عن طريق الازرار التالية 🦾</b>",
        parse_mode='html',
        buttons=buttons
    )

# تغيير لغة البوت
async def change_language(event):
    global language
    user_id = event.sender_id
    
    # تغيير اللغة
    if user_id in language and language[user_id] == "en":
        language[user_id] = "ar"
    else:
        language[user_id] = "en"
    
    # إعادة إرسال رسالة الترحيب بناءً على اللغة الجديدة
    await send_welcome_message(event)

# إرسال رسالة الترحيب بناءً على اللغة
async def send_welcome_message(event):
    user_id = event.sender_id
    sender = await event.get_sender()
    
    if user_id in language and language[user_id] == "en":
        welcome_message = f"""
👋 Hello {sender.first_name},

I am a bot designed to save restricted content. I can save files from restricted channels and groups.

Press /help to learn more.
"""
        buttons = [
            [Button.inline("Change language 🇸🇦", b'change_language')],
            [Button.url("Developer", "https://t.me/PP2P6"), Button.url("Bot channel", f"https://t.me/{CHANNEL_USERNAME[1:]}")]
        ]
    else:
        welcome_message = f"""
👋 مرحبًا {sender.first_name},

أنا بوت حفظ المحتويات المقيدة، يمكنني حفظ ملفات القنوات المقيدة بالإضافة إلى المجموعة.

اضغط على /help لمعرفة المزيد.
        """
        buttons = [
            [Button.inline("Change language 🇺🇸", b'change_language')],
            [Button.url("المطور", "https://t.me/PP2P6"), Button.url("قناة البوت", f"https://t.me/{CHANNEL_USERNAME[1:]}")]
        ]
    
    try:
        # تعديل الرسالة الحالية
        await event.edit(welcome_message, parse_mode='html', buttons=buttons, link_preview=False)
    except telethon.errors.rpcerrorlist.MessageIdInvalidError:
        # إذا فشل التعديل، إرسال رسالة جديدة
        await event.reply(welcome_message, parse_mode='html', buttons=buttons, link_preview=False)

# إرسال رسالة التعليمات بناءً على اللغة
async def send_help_message(event):
    user_id = event.sender_id
    if user_id in language and language[user_id] == "en":
        help_message = """
- /start command to restart the bot.
- /login command to save content from restricted channels without an invite link by logging into your account in the channel from which you want to save the content.
- /logout command to log out of your account.
        """
    else:
        help_message = """
- /start لإعادة تشغيل البوت.
- /login لحفظ المحتوى من القنوات المقيدة دون الحاجة إلى رابط دعوة عن طريق تسجيل الدخول إلى حسابك في القناة التي تريد حفظ المحتوى منها.
- /logout لتسجيل الخروج من حسابك.
        """
    
    try:
        # تعديل الرسالة الحالية
        await event.edit(help_message, parse_mode='html')
    except telethon.errors.rpcerrorlist.MessageIdInvalidError:
        # إذا فشل التعديل، إرسال رسالة جديدة
        await event.reply(help_message, parse_mode='html')

# تسجيل الدخول إلى حساب المستخدم
async def login(event):
    sender_id = event.sender_id
    user_states[sender_id] = "in_login"

    async with client.conversation(event.sender_id) as conv:
        try:
            await conv.send_message("- حسنـا قم بـ إرسـال كـود الـ (آيبي ايدي - ᴀᴩɪ_ɪᴅ) الان 🏷\n\n- او اضغط /skip لـ المواصلـه عبـر ايبيات البـوت التلقائيـه 🪁")
            api_id_msg = await conv.get_response()
            if api_id_msg.text == '/skip':
                api_id = '24028902'
                api_hash = 'b103ee23d3f642b59db3cfa8d7769557'
            else:
                api_id = api_id_msg.text
                await conv.send_message("- حسنـا قم بـ إرسـال كـود الـ (آيبي هاش - ᴀᴩɪ_ʜᴀsʜ) الان 🏷\n\n- او اضغط /cancel لـ الالغـاء")
                api_hash_msg = await conv.get_response()
                if api_hash_msg.text == '/cancel':
                    await conv.send_message("» تم الالغـاء ...\n» ارسـل  /start  لـ البـدء مـن جديـد")
                    del user_states[sender_id]  # إزالة حالة المستخدم
                    return
                api_hash = api_hash_msg.text

            # إرسال رسالة مع زر لإرسال جهة الاتصال
            contact_button = [[Button.request_phone("إرسال جهة الاتصال", resize=True, single_use=True)]]
            await conv.send_message("- قم بالضغـط ع زر ارسـال جهـة الاتصـال\n- او إرسـال رقـم الهاتـف مع مفتـاح الدولـة\n- مثال : +967777117888", buttons=contact_button)
            phone_number_msg = await conv.get_response()
            if phone_number_msg.text == '/cancel':
                await conv.send_message("» تم الالغـاء ...\n» ارسـل  /start  لـ البـدء مـن جديـد")
                del user_states[sender_id]  # إزالة حالة المستخدم
                return
            phone_number = phone_number_msg.text if not phone_number_msg.contact else phone_number_msg.contact.phone_number

            # إرسال رسالة "جاري إرسال كود الدخول ⎙...."
            sending_code_msg = await conv.send_message("**جـاري ارسـال كـود الدخـول ⎙....**")

            # بدء عملية تسجيل الدخول
            user_client = TelegramClient(StringSession(), api_id, api_hash)
            await user_client.connect()
            if not await user_client.is_user_authorized():
                await user_client.send_code_request(phone_number)
                await sending_code_msg.delete()  # حذف الرسالة بعد إرسال الكود
                code_message = await conv.send_message("- قم بـ ارسـال الكود الذي وصل اليك من الشركة\n\n- اضغـط الـزر بالاسفـل لـ الذهاب لـ اشعـارات Telegram", buttons=[[Button.url("إضغط هنا", "tg://openmessage?user_id=777000")]])
                verification_code_msg = await conv.get_response()
                if verification_code_msg.text == '/cancel':
                    await conv.send_message("» تم الالغـاء ...\n» ارسـل  /start  لـ البـدء مـن جديـد")
                    del user_states[sender_id]  # إزالة حالة المستخدم
                    return
                verification_code = verification_code_msg.text

                try:
                    await user_client.sign_in(phone_number, verification_code)
                except PhoneCodeExpiredError:
                    await conv.send_message("☆ ✖️ انتهت صلاحية الكود. حاول مرة أخرى.")
                    del user_states[sender_id]  # إزالة حالة المستخدم
                    return
                except SessionPasswordNeededError:
                    await conv.send_message("- قـم بادخـال كلمـة مـرور حسابـك ( التحقق بـ خطوتين ).\n- بــدون مســافـات")
                    password_msg = await conv.get_response()
                    if password_msg.text == '/cancel':
                        await conv.send_message("» تم الالغـاء ...\n» ارسـل  /start  لـ البـدء مـن جديـد")
                        del user_states[sender_id]  # إزالة حالة المستخدم
                        return
                    password = password_msg.text
                    try:
                        await user_client.sign_in(password=password)
                    except Exception as e:
                        await conv.send_message(f"❌ حدث خطأ أثناء تسجيل الدخول: {e}")
                        del user_states[sender_id]  # إزالة حالة المستخدم
                        return
                except Exception as e:
                    await conv.send_message(f"❌ حدث خطأ غير متوقع: {e}")
                    del user_states[sender_id]  # إزالة حالة المستخدم
                    return

            # حفظ الجلسة واسم المستخدم
            session_str = user_client.session.save()
            user = await user_client.get_me()  # الحصول على معلومات الحساب

            # التحقق من أن الحساب غير مضاف مسبقًا
            if any(str(user.id) in account for account in user_accounts[sender_id]["users"]):
                await conv.send_message(f"❌ الحساب {user.first_name} مضاف مسبقًا.")
                return

            user_accounts[sender_id]["sessions"].append(session_str)
            user_accounts[sender_id]["users"].append(f"{user.id} - {user.first_name}")  # حفظ ID واسم المستخدم

            # تخزين الجلسات في قاعدة البيانات
            save_data()

            await conv.send_message(f"✔️ تم إضافة الحساب بنجاح: {user.first_name} 🎉")

            # إزالة حالة المستخدم بعد الانتهاء
            del user_states[sender_id]

            # طلب من المستخدم إرسال رابط المنشور
            await conv.send_message("**ارسل رابط المنشور الذي تريد حفظه من القناة الخاصة بك.**")

            # الانتظار لاستقبال الرابط
            post_link_msg = await conv.get_response()
            post_link = post_link_msg.text

            # البحث عن المنشور في الحساب الخاص بالمستخدم
            try:
                match = re.match(r'https://t.me/(c/\d+)/(\d+)', post_link)
                if match:
                    channel_id = match.group(1)
                    post_id = match.group(2)

                    post = await user_client.get_messages(int(channel_id.replace('c/', '')), ids=int(post_id))
                    message_text = post.message
                    views = post.views or "غير معروف"
                    date = post.date.strftime('%Y-%m-%d %H:%M:%S') if post.date else "تاريخ غير معروف"

                    if post.media:
                        message_response = await client.send_file(event.chat_id, post.media, caption=message_text)
                    else:
                        message_response = await event.reply(message_text)

                    info_message = f"""
                    ↯︙تاريخ النشر ↫ ⦗ {date} ⦘
                    ↯︙عدد المشاهدات ↫ ⦗ {views} ⦘
                    ↯︙سيتم حذف المحتوى بعد ↫ ⦗ 1 ⦘ دقيقة
                    ↯︙قم بحفظه او اعادة التوجيه
                    """
                    info_response = await event.reply(info_message, parse_mode='html')

                    asyncio.create_task(countdown(event, info_response, delay=60, date=date, views=views))

                    await delete_messages_later(event.chat_id, [event.id, message_response.id, info_response.id], delay=60)

                    # إرسال رسالة مع أزرار "نعم" و "لا"
                    buttons = [
                        [Button.inline("نعم", b'yes_save_another'), Button.inline("لا", b'no_logout')]
                    ]
                    await conv.send_message("هل تريد حفظ منشور آخر؟", buttons=buttons)

            except telethon.errors.rpcerrorlist.ChannelPrivateError:
                await conv.send_message("❌ <b>لا يمكن الوصول إلى هذه القناة لأنها خاصة.</b>", parse_mode='html')
            except telethon.errors.rpcerrorlist.MessageIdInvalidError:
                await conv.send_message("❌ <b>معرف المنشور غير صالح أو تم حذفه.</b>", parse_mode='html')
            except Exception as e:
                await conv.send_message(f"❌ <b>حدث خطأ غير متوقع:</b> {e}", parse_mode='html')

        except asyncio.TimeoutError:
            await event.reply("**عـذراً .. لقـد انتهـى الوقت**\n**ارسـل  /start  لـ البـدء مـن جديـد**")
            if sender_id in user_states:
                del user_states[sender_id]
        except Exception as e:
            await conv.send_message(f"**☆ ❌ حدث خطأ**")
            if sender_id in user_states:
                del user_states[sender_id]  # إزالة حالة المستخدم في حالة حدوث خطأ

# تسجيل الخروج من الحساب
async def logout(event):
    sender_id = event.sender_id
    if sender_id in user_accounts:
        user_accounts[sender_id]["sessions"] = []  # حذف الجلسات
        user_accounts[sender_id]["users"] = []  # حذف الحسابات
        save_data()  # حفظ التغييرات
        await event.reply("✔️ تم تسجيل الخروج بنجاح.")
    else:
        await event.reply("❌ لم يتم تسجيل الدخول مسبقًا.")

# معالجة الأمر /cancel
@client.on(events.NewMessage(pattern='/cancel'))
async def cancel_handler(event):
    try:
        sender = await event.get_sender()
        sender_id = str(sender.id)

        # التحقق إذا كان المستخدم في عملية تسجيل الدخول
        if sender_id in user_states and user_states[sender_id] == "in_login":
            # التحقق من الرسالة الأخيرة التي أرسلها البوت
            last_message = await client.get_messages(sender_id, limit=1)
            if last_message and "حسنـا قم بـ إرسـال كـود الـ (آيبي هاش - ᴀᴩɪ_ʜᴀsʜ) الان 🏷" in last_message[0].message:
                await event.reply("» تم الالغـاء ...\n» ارسـل  /start  لـ البـدء مـن جديـد")
                del user_states[sender_id]  # إزالة حالة المستخدم
    except Exception as e:
        pass  # تجاهل الأخطاء

# التعامل مع الرسائل
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender = await event.get_sender()
    sender_id = str(sender.id)  # تحويل إلى نص لضمان الاتساق
    username = sender.username or "بدون يوزر"
    full_name = f"{sender.first_name} {sender.last_name or ''}".strip()

    # التحقق إذا كان المستخدم مسجلًا بالفعل
    if sender_id not in user_accounts:
        # تسجيل المستخدم الجديد مع تخزين الاسم واليوزر
        user_accounts[sender_id] = {
            "name": full_name,
            "username": username,
            "sessions": [],
            "users": []
        }
        save_data()  # حفظ البيانات إلى ملف

        # إرسال رسالة للمطور عند دخول عضو جديد
        total_users = len(user_accounts)  # إجمالي عدد المستخدمين
        message = (
            f"**☑️| انضم عضو جديد**\n"
            f"━━━━━━━━━━━━━\n"
            f"👤 **الاسم:** {full_name}\n"
            f"🔗 **المعرف:** @{username if username != 'بدون يوزر' else 'بدون يوزر'}\n"
            f"🆔 **الآي دي:** `{sender_id}`\n"
            f"━━━━━━━━━━━━━\n"
            f"📊 **إجمالي الأعضاء:** {total_users}\n"
        )
        await client.send_message(developer_id, message)

    # التحقق من اشتراك المستخدم في القناة
    if not await check_subscription(sender.id):
        await send_subscription_prompt(event)
        return

    # التحقق من حالة الصيانة
    global maintenance_mode, maintenance_message
    if maintenance_mode and sender.id != developer_id:
        await event.reply(maintenance_message, parse_mode='html')
        return

    # إرسال رسالة الترحيب
    await send_welcome_message(event)

    # إرسال رسالة الأوامر الخاصة بالمطور إذا كان المستخدم مطورًا
    if sender.id == developer_id:
        await send_developer_commands(event)

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    await send_help_message(event)

@client.on(events.NewMessage(pattern='/login'))
async def login_command(event):
    await login(event)

@client.on(events.NewMessage(pattern='/logout'))
async def logout_command(event):
    await logout(event)

@client.on(events.CallbackQuery)
async def callback_handler(event):
    global maintenance_mode, maintenance_message
    if event.data == b'stats':
        if event.sender_id == developer_id:
            await show_bot_stats(event)
        else:
            await event.answer("❌ ليس لديك صلاحية الوصول إلى هذه الميزة.", alert=True)
    elif event.data == b'verify':
        if await check_subscription(event.sender_id):
            await event.answer("تم التحقق ✔️", alert=True)
            await event.delete()
            await start(event)
        else:
            await event.answer("❌ لم تشترك في القناة بعد.", alert=True)
    elif event.data == b'broadcast':
        if event.sender_id == developer_id:
            # وضع المستخدم في حالة إذاعة
            broadcast_state[event.chat_id] = True

            # تعديل الرسالة الحالية لعرض النص المطلوب وزر الرجوع
            buttons = [
                [Button.inline("رجوع ↩️", b'back_to_main')]
            ]
            await event.edit(
                "<b>• أرسل الآن الكليشة ( النص أو جميع الوسائط )</b>\n"
                "<b>• يمكنك استخدام كود جاهز في الإذاعة أو يمكنك استخدام الماركدوان</b>",
                parse_mode='html',
                buttons=buttons
            )
        else:
            await event.answer("❌ ليس لديك صلاحية الوصول إلى هذه الميزة.", alert=True)
    elif event.data == b'enable_maintenance':
        if event.sender_id == developer_id:
            # وضع المستخدم في حالة تفعيل الصيانة
            await event.answer("أرسل الآن الرسالة التي تريد أن تظهر للمستخدمين أثناء الصيانة:", alert=True)
            await event.edit(
                "<b>• أرسل الآن الرسالة التي تريد أن تظهر للمستخدمين أثناء الصيانة:</b>",
                parse_mode='html'
            )
            # وضع المستخدم في حالة انتظار الرسالة
            broadcast_state[event.chat_id] = 'waiting_for_maintenance_message'
        else:
            await event.answer("❌ ليس لديك صلاحية الوصول إلى هذه الميزة.", alert=True)
    elif event.data == b'disable_maintenance':
        if event.sender_id == developer_id:
            # إيقاف حالة الصيانة
            maintenance_mode = False
            maintenance_message = ""
            await event.answer("تم إيقاف الصيانة بنجاح ✅", alert=True)
            await send_developer_commands(event)
        else:
            await event.answer("❌ ليس لديك صلاحية الوصول إلى هذه الميزة.", alert=True)
    elif event.data == b'back_to_main':
        if event.sender_id == developer_id:
            # إعادة تعيين حالة الإذاعة
            broadcast_state[event.chat_id] = False

            # إعادة إرسال رسالة الأوامر الخاصة بالمطور في نفس الرسالة
            buttons = [
                [Button.inline("إذاعة 📢", b'broadcast')],
                [Button.inline("تفعيل الصيانه", b'enable_maintenance'), Button.inline("إيقاف الصيانه", b'disable_maintenance')],
                [Button.inline("📊 إحصائيات البوت", b'stats')]
            ]
            await event.edit(
                "<b>• مرحبا عزيزي المطور يمكنك في اوامر البوت الخاص بك عن طريق الازرار التالية 🦾</b>",
                parse_mode='html',
                buttons=buttons
            )
        else:
            await event.answer("❌ ليس لديك صلاحية الوصول إلى هذه الميزة.", alert=True)
    elif event.data == b'change_language':
        await change_language(event)
    elif event.data == b'yes_save_another':
        await event.answer("ارسل رابط المنشور الذي تريد حفظه.", alert=True)
    elif event.data == b'no_logout':
        await logout(event)
        await event.answer("تم تسجيل الخروج بنجاح ✅", alert=True)

# التعامل مع الرسائل أثناء حالة الإذاعة أو الصيانة
@client.on(events.NewMessage())
async def handler(event):
    global maintenance_mode, maintenance_message
    
    # تجاهل الرسائل التي تبدأ بشرطة مائلة (الأوامر)
    if event.message.message.startswith('/'):
        return

    # تجاهل الرسائل التي لا تبدأ بـ https://t.me/
    if not event.message.message.strip().startswith('https://t.me/'):
        return  # تجاهل الرسالة تمامًا

    # التحقق من حالة الصيانة
    if maintenance_mode and event.sender_id != developer_id:
        await event.reply(maintenance_message, parse_mode='html')
        return

    # التحقق من حالة الإذاعة
    if event.chat_id in broadcast_state and broadcast_state[event.chat_id] == 'waiting_for_maintenance_message':
        maintenance_mode = True
        maintenance_message = event.message.message
        await event.reply("<b>تم تفعيل وضع الصيانة بنجاح ✅</b>", parse_mode='html')
        broadcast_state[event.chat_id] = False
        await send_developer_commands(event)
        return

    if event.chat_id in broadcast_state and broadcast_state[event.chat_id]:
        # إرسال الرسالة إلى جميع المستخدمين
        users = load_users()
        for user_id in users:
            try:
                await client.send_message(int(user_id), event.message)
            except Exception as e:
                print(f"Error sending broadcast to user {user_id}: {e}")

        # إعادة تعيين حالة الإذاعة
        broadcast_state[event.chat_id] = False

        # إرسال رسالة تأكيد
        await event.reply("<b>تم إرسال الإذاعة بنجاح ✅</b>", parse_mode='html')

        # إعادة إرسال رسالة الأوامر الخاصة بالمطور
        await send_developer_commands(event)
        return

    # التحقق من اشتراك المستخدم في القناة
    if not await check_subscription(event.sender_id):
        await send_subscription_prompt(event)
        return

    links = event.message.message.strip().split()

    for link in links:
        if not re.match(r'https://t.me/([^/]+)/(\d+)', link):
            await event.reply("⚠️ <b>الرابط غير صالح. تأكد من إدخال رابط من قناة تليجرام.</b>", parse_mode='html')
            continue

        match = re.match(r'https://t.me/([^/]+)/(\d+)', link)
        if match:
            channel_username = match.group(1)
            post_id = match.group(2)

            try:
                post = await client.get_messages(channel_username, ids=int(post_id))
                message_text = post.message
                views = post.views or "غير معروف"
                date = post.date.strftime('%Y-%m-%d %H:%M:%S') if post.date else "تاريخ غير معروف"

                if post.media:
                    message_response = await client.send_file(event.chat_id, post.media, caption=message_text)
                else:
                    message_response = await event.reply(message_text)

                info_message = f"""
                ↯︙تاريخ النشر ↫ ⦗ {date} ⦘
                ↯︙عدد المشاهدات ↫ ⦗ {views} ⦘
                ↯︙سيتم حذف المحتوى بعد ↫ ⦗ 1 ⦘ دقيقة
                ↯︙قم بحفظه او اعادة التوجيه
                """
                info_response = await event.reply(info_message, parse_mode='html')

                asyncio.create_task(countdown(event, info_response, delay=60, date=date, views=views))

                await delete_messages_later(event.chat_id, [event.id, message_response.id, info_response.id], delay=60)

            except telethon.errors.rpcerrorlist.ChannelPrivateError:
                await event.reply("❌ <b>لا يمكن الوصول إلى هذه القناة لأنها خاصة.</b>", parse_mode='html')
            except telethon.errors.rpcerrorlist.MessageIdInvalidError:
                await event.reply("❌ <b>معرف المنشور غير صالح أو تم حذفه.</b>", parse_mode='html')
            except Exception as e:
                await event.reply(f"❌ <b>حدث خطأ غير متوقع:</b> {e}", parse_mode='html')

        else:
            await event.reply("⚠️ <b>يرجى إدخال رابط صحيح لمنشور من قناة مقيدة.</b>", parse_mode='html')


# بدء تشغيل البوت
while True:
    try:
        client.start(bot_token=BOT_TOKEN)
        print("Bot started successfully")
        client.run_until_disconnected()
    except Exception as e:
        print(f"Error occurred: {e}")
        continue