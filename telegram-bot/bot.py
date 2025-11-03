#!/usr/bin/env python3
import requests
import logging
import random
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import time
import re
import json

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "токен"

class CredentialsManager:
    def __init__(self):
        self.secret_key = b"(OMG6CKOPZab0QI7bnSAC)qoVHA4mhVt"
        
    def _get_cipher(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"schedule_parser_salt_2025",
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.secret_key))
        return Fernet(key)
    
    def get_credentials(self):
        try:
            encrypted_username = b'gAAAAABpCLIm5CKJuKEjEQfB9T6ef9GairZ1iY4XH5aw69VEaNoYUPU1h5AK2G3zCaw5bcOQfdlv1qh9U2zdy1glx0g8yrjAm7qHwaxt4BYNq5y2a5n53JA='
            encrypted_password = b'gAAAAABpCLImYu510x5Ks4maYN_xlbrPdCeWUq7Hd0XqYziXk7P8QSl7l5UsR_lIiWzCZBMHSAu9ha8qu5_oRuCwHHYeGb5pZg=='
            
            cipher = self._get_cipher()
            username = cipher.decrypt(encrypted_username).decode('utf-8')
            password = cipher.decrypt(encrypted_password).decode('utf-8')
            return username, password
        except Exception as e:
            logging.error(f"Ошибка дешифрования: {e}")
            return None, None

class ScheduleParser:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = 'https://api.kktmobile-app.ru'
        self.web_url = 'https://kktmobile-app.ru'
        self.group = 'И-232'
        self.token = None
        self.token_file = 'bot_token_cache.json'
        
    def find_auth_endpoint(self):
        try:
            response = self.session.get(f'{self.web_url}/login')
            js_files = re.findall(r'src="([^"]*\.js[^"]*)"', response.text)
            js_files.append('/static/js/bundle.js')
            
            for js_file in js_files:
                if not js_file.startswith('http'):
                    js_url = self.web_url + js_file if js_file.startswith('/') else self.web_url + '/' + js_file
                else:
                    js_url = js_file
                
                try:
                    js_response = self.session.get(js_url, timeout=10)
                    if js_response.status_code == 200:
                        auth_patterns = [
                            r'["\'](/auth[^"\']*)["\']',
                            r'["\'](/api/auth[^"\']*)["\']',
                            r'["\'](https://api\.kktmobile-app\.ru[^"\']*)["\']',
                        ]
                        
                        for pattern in auth_patterns:
                            matches = re.findall(pattern, js_response.text)
                            for match in matches:
                                if 'auth' in match.lower() or 'login' in match.lower():
                                    endpoint = self.base_url + match if match.startswith('/') else match
                                    return endpoint
                except:
                    continue
            
            return f'{self.base_url}/alogin'
            
        except Exception as e:
            logging.error(f"Ошибка поиска эндпоинта: {e}")
            return f'{self.base_url}/alogin'

    def get_auth_token(self):
        endpoint = self.find_auth_endpoint()
        cred_manager = CredentialsManager()
        username, password = cred_manager.get_credentials()
        
        if not username or not password:
            logging.error("Не удалось получить учетные данные")
            return None
        
        auth_data = {'username': username, 'password': password}
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': self.web_url,
            'Referer': f'{self.web_url}/login',
        }
        
        try:
            response = self.session.post(endpoint, json=auth_data, headers=headers, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
        except Exception as e:
            logging.error(f"Ошибка авторизации: {e}")
        
        return None

    def load_cached_token(self):
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    token = data.get('token')
                    timestamp = data.get('timestamp', 0)
                    
                    if token and time.time() - timestamp < 43200:
                        if self.test_token(token):
                            return token
        except:
            pass
        return None

    def save_token_to_cache(self, token):
        try:
            data = {'token': token, 'timestamp': time.time()}
            with open(self.token_file, 'w') as f:
                json.dump(data, f)
        except:
            pass

    def get_fresh_token(self):
        token = self.get_auth_token()
        if token:
            self.save_token_to_cache(token)
        return token

    def ensure_valid_token(self):
        cached_token = self.load_cached_token()
        if cached_token:
            self.token = cached_token
            return True
        
        new_token = self.get_fresh_token()
        if new_token:
            self.token = new_token
            return True
        
        return False

    def test_token(self, token):
        test_url = f'{self.base_url}/schedule/students/{self.group}/1'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept': 'application/json, text/plain, */*',
            'Authorization': f'Bearer {token}',
            'Origin': self.web_url,
            'Referer': f'{self.web_url}/',
        }
        
        try:
            response = self.session.get(test_url, headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False

    def get_schedule(self, day=None):
        if not self.ensure_valid_token():
            return None
        
        if day is None:
            day = datetime.now().isoweekday()
        
        url = f'{self.base_url}/schedule/students/{self.group}/{day}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept': 'application/json, text/plain, */*',
            'Authorization': f'Bearer {self.token}',
            'Origin': self.web_url,
            'Referer': f'{self.web_url}/',
        }
        
        try:
            response = self.session.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
                self.token = None
                return self.get_schedule(day)
                
        except Exception as e:
            logging.error(f"Ошибка получения расписания: {e}")
        
        return None

schedule_parser = ScheduleParser()

GACHI_PHRASES = [
    "♂️ BOY NEXT DOOR ♂️",
    "♂️ FUCK YOU ♂️", 
    "♂️ ASS WE CAN ♂️",
    "♂️ DEEP DARK FANTASY ♂️",
    "♂️ LEATHERMAN ♂️",
    "♂️ SIR ♂️",
    "♂️ BOSS OF THE GYM ♂️",
    "♂️ FUCKING MACHINE ♂️",
    "♂️ GACHIMUCHI ♂️",
    "♂️ THREE HUNDRED BUCKS ♂️"
]

def get_random_gachi():
    return random.choice(GACHI_PHRASES)

def get_day_name(day_num):
    days = {
        1: "понедельник", 2: "вторник", 3: "среда",
        4: "четверг", 5: "пятница", 6: "суббота", 7: "воскресенье"
    }
    return days.get(day_num, "день")

async def set_bot_commands(application):
    commands = [
        BotCommand("start", "♂️ Начать работу"),
        BotCommand("today", "📅 Расписание на сегодня"),
        BotCommand("tomorrow", "📆 Расписание на завтра"),
        BotCommand("week", "📚 Расписание на неделю"),
        BotCommand("gachi", "♂️ Случайная гачи-фраза"),
        BotCommand("help", "❓ Помощь по командам")
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    gachi_phrase = get_random_gachi()
    
    await update.message.reply_html(
        f"♂️ <b>WELCOME TO THE GYM, {user.first_name}! ♂️</b>\n\n"
        f"{gachi_phrase}\n\n"
        "🎓 <b>Бот расписания группы И-232</b>\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "/today - расписание на сегодня\n"
        "/tomorrow - расписание на завтра\n" 
        "/week - расписание на неделю\n"
        "/gachi - случайная гачи-фраза\n"
        "/help - список команд\n\n"
        "💡 <i>Начните вводить / чтобы увидеть все команды</i>\n\n"
        "♂️ <i>FUCKING SCHEDULE READY ♂️</i>"
    )

async def today(update: Update, context: CallbackContext):
    today_date = datetime.now()
    day_name = get_day_name(today_date.isoweekday())
    gachi_phrase = get_random_gachi()
    
    schedule = schedule_parser.get_schedule()
    
    if schedule and isinstance(schedule, list) and schedule:
        message = (
            f"📅 <b>♂️ РАСПИСАНИЕ НА СЕГОДНЯ ♂️</b>\n"
            f"📆 {today_date.strftime('%d.%m.%Y')}, {day_name}\n"
            f"🎯 Пар сегодня: {len(schedule)}\n\n"
        )
        
        for i, lesson in enumerate(schedule, 1):
            message += (
                f"<b>{i}. {lesson.get('subject', 'Предмет')}</b>\n"
                f"   ⏰ {lesson.get('start_time', '')} - {lesson.get('end_time', '')}\n"
                f"   👨‍🏫 {lesson.get('teacher_full_name', 'Преподаватель')}\n"
                f"   🏫 {lesson.get('room', 'Аудитория')}\n\n"
            )
        
        message += f"♂️ <i>{gachi_phrase}</i> ♂️"
    else:
        message = (
            f"🎉 <b>♂️ СЕГОДНЯ ПАР НЕТ! ♂️</b>\n"
            f"📆 {today_date.strftime('%d.%m.%Y')}, {day_name}\n\n"
            f"♂️ <i>{gachi_phrase}</i> ♂️"
        )
    
    await update.message.reply_html(message)

async def tomorrow(update: Update, context: CallbackContext):
    tomorrow_date = datetime.now().replace(day=datetime.now().day + 1)
    day_num = tomorrow_date.isoweekday()
    day_name = get_day_name(day_num)
    gachi_phrase = get_random_gachi()
    
    schedule = schedule_parser.get_schedule(day_num)
    
    if schedule and isinstance(schedule, list) and schedule:
        message = (
            f"📅 <b>♂️ РАСПИСАНИЕ НА ЗАВТРА ♂️</b>\n"
            f"📆 {tomorrow_date.strftime('%d.%m.%Y')}, {day_name}\n"
            f"🎯 Пар завтра: {len(schedule)}\n\n"
        )
        
        for i, lesson in enumerate(schedule, 1):
            message += (
                f"<b>{i}. {lesson.get('subject', 'Предмет')}</b>\n"
                f"   ⏰ {lesson.get('start_time', '')} - {lesson.get('end_time', '')}\n"
                f"   👨‍🏫 {lesson.get('teacher_full_name', 'Преподаватель')}\n"
                f"   🏫 {lesson.get('room', 'Аудитория')}\n\n"
            )
        
        message += f"♂️ <i>{gachi_phrase}</i> ♂️"
    else:
        message = (
            f"🎉 <b>♂️ ЗАВТРА ПАР НЕТ! ♂️</b>\n"
            f"📆 {tomorrow_date.strftime('%d.%m.%Y')}, {day_name}\n\n"
            f"♂️ <i>{gachi_phrase}</i> ♂️"
        )
    
    await update.message.reply_html(message)

async def week(update: Update, context: CallbackContext):
    gachi_phrase = get_random_gachi()
    
    message = "📅 <b>♂️ РАСПИСАНИЕ НА НЕДЕЛЮ ♂️</b>\n\n"
    
    days = {
        1: "Понедельник", 2: "Вторник", 3: "Среда", 
        4: "Четверг", 5: "Пятница", 6: "Суббота"
    }
    
    for day_num, day_name in days.items():
        schedule = schedule_parser.get_schedule(day_num)
        
        message += f"<b>📖 {day_name}:</b>\n"
        
        if schedule and isinstance(schedule, list) and schedule:
            for i, lesson in enumerate(schedule, 1):
                message += (
                    f"  {i}. <b>{lesson.get('subject', 'Предмет')}</b>\n"
                    f"     ⏰ {lesson.get('start_time', '')}-{lesson.get('end_time', '')}\n"
                    f"     🏫 {lesson.get('room', 'Аудитория')}\n"
                )
        else:
            message += "  🎉 Пар нет\n"
        
        message += "\n"
    
    message += f"♂️ <i>{gachi_phrase}</i> ♂️"
    await update.message.reply_html(message)

async def help_command(update: Update, context: CallbackContext):
    gachi_phrase = get_random_gachi()
    
    await update.message.reply_html(
        "📚 <b>♂️ ДОСТУПНЫЕ КОМАНДЫ ♂️</b>\n\n"
        "/start - начать работу\n"
        "/today - расписание на сегодня\n" 
        "/tomorrow - расписание на завтра\n"
        "/week - расписание на неделю\n"
        "/gachi - случайная гачи-фраза\n"
        "/help - эта справка\n\n"
        "💡 <i>Начните вводить / чтобы увидеть все команды</i>\n\n"
        f"♂️ <i>{gachi_phrase}</i> ♂️"
    )

async def gachi_command(update: Update, context: CallbackContext):
    gachi_phrase = get_random_gachi()
    await update.message.reply_html(f"♂️ <b>{gachi_phrase}</b> ♂️")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("tomorrow", tomorrow))
    application.add_handler(CommandHandler("week", week))
    application.add_handler(CommandHandler("gachi", gachi_command))
    application.add_handler(CommandHandler("help", help_command))
    
    application.post_init = set_bot_commands

    print("♂️ GACHI BOT STARTED ♂️")
    application.run_polling()

if __name__ == "__main__":
    main()
