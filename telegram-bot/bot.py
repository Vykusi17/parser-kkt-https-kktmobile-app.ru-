#!/usr/bin/env python3
import requests
import logging
import random
from datetime import datetime, timedelta
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
import asyncio
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "тг токен"

REQUEST_TIMEOUT = 15
MAX_RETRIES = 2
RETRY_DELAY = 2

class ConnectionError(Exception):
    pass

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
        self.token = None
        self.token_file = 'bot_token_cache.json'
        self.schedule_type = "students"
        self.groups = ["И-232", "И-233"]
        
        self.session.mount('http://', requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES))
        self.session.mount('https://', requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES))

    def _make_request_with_timeout(self, method, url, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = REQUEST_TIMEOUT
            
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = method(url, **kwargs)
                return response
                
            except requests.exceptions.Timeout:
                logging.warning(f"⚠️ Таймаут запроса (попытка {attempt + 1}/{MAX_RETRIES + 1})")
                if attempt == MAX_RETRIES:
                    raise ConnectionError("🚨 ТАЙМАУТ ПОДКЛЮЧЕНИЯ! Сайт не отвечает")
                    
            except requests.exceptions.ConnectionError as e:
                logging.warning(f"⚠️ Ошибка подключения (попытка {attempt + 1}/{MAX_RETRIES + 1}): {e}")
                if attempt == MAX_RETRIES:
                    raise ConnectionError("🚨 ДИСКОННЕКТ! Не удалось подключиться к сайту")
                    
            except Exception as e:
                logging.error(f"❌ Неожиданная ошибка (попытка {attempt + 1}/{MAX_RETRIES + 1}): {e}")
                if attempt == MAX_RETRIES:
                    raise ConnectionError(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (attempt + 1))

    def find_auth_endpoint(self):
        try:
            response = self._make_request_with_timeout(
                self.session.get, 
                f'{self.web_url}/login'
            )
            js_files = re.findall(r'src="([^"]*\.js[^"]*)"', response.text)
            js_files.append('/static/js/bundle.js')

            for js_file in js_files:
                if not js_file.startswith('http'):
                    js_url = self.web_url + js_file if js_file.startswith('/') else self.web_url + '/' + js_file
                else:
                    js_url = js_file

                try:
                    js_response = self._make_request_with_timeout(
                        self.session.get, 
                        js_url
                    )
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
                except ConnectionError:
                    continue
                except Exception:
                    continue

            return f'{self.base_url}/alogin'

        except ConnectionError as e:
            raise e
        except Exception as e:
            logging.error(f"Ошибка поиска эндпоинта: {e}")
            return f'{self.base_url}/alogin'

    def get_auth_token(self):
        try:
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

            response = self._make_request_with_timeout(
                self.session.post, 
                endpoint, 
                json=auth_data, 
                headers=headers
            )
            
            if response.status_code == 200:
                token_data = response.json()
                logging.info("✅ Авторизация успешна")
                return token_data.get('access_token')
            else:
                logging.error(f"❌ Ошибка авторизации: {response.status_code}")
                
        except ConnectionError as e:
            logging.error(f"🚨 {str(e)}")
        except Exception as e:
            logging.error(f"❌ Ошибка авторизации: {e}")

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
                            logging.info("✅ Используется кэшированный токен")
                            return token
                        else:
                            logging.warning("❌ Кэшированный токен невалиден")
        except Exception as e:
            logging.error(f"Ошибка загрузки токена: {e}")
        return None

    def save_token_to_cache(self, token):
        try:
            data = {'token': token, 'timestamp': time.time()}
            with open(self.token_file, 'w') as f:
                json.dump(data, f)
            logging.info("✅ Токен сохранен в кэш")
        except Exception as e:
            logging.error(f"Ошибка сохранения токена: {e}")

    def get_fresh_token(self):
        token = self.get_auth_token()
        if token:
            self.save_token_to_cache(token)
        return token

    def ensure_valid_token(self):
        try:
            cached_token = self.load_cached_token()
            if cached_token:
                self.token = cached_token
                return True

            new_token = self.get_fresh_token()
            if new_token:
                self.token = new_token
                return True

            return False
        except ConnectionError as e:
            logging.error(f"🚨 {str(e)}")
            return False

    def test_token(self, token):
        groups_param = ",".join(self.groups)
        test_url = f'{self.base_url}/api/public/schedule/{self.schedule_type}/{groups_param}/1'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept': 'application/json, text/plain, */*',
            'Authorization': f'Bearer {token}',
            'Origin': self.web_url,
            'Referer': f'{self.web_url}/',
        }

        try:
            response = self._make_request_with_timeout(
                self.session.get, 
                test_url, 
                headers=headers
            )
            return response.status_code == 200
        except ConnectionError:
            return False
        except Exception as e:
            logging.error(f"Ошибка проверки токена: {e}")
            return False

    def get_schedule(self, day=None):
        try:
            if not self.ensure_valid_token():
                logging.error("Не удалось получить валидный токен")
                return None

            if day is None:
                day = datetime.now().isoweekday()

            groups_param = ",".join(self.groups)
            url = f'{self.base_url}/api/public/schedule/{self.schedule_type}/{groups_param}/{day}'

            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
                'Accept': 'application/json, text/plain, */*',
                'Authorization': f'Bearer {self.token}',
                'Origin': self.web_url,
                'Referer': f'{self.web_url}/',
            }

            response = self._make_request_with_timeout(
                self.session.get, 
                url, 
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                logging.info(f"✅ Расписание получено для дня {day}: {len(data) if isinstance(data, list) else 0} пар")
                return data
            elif response.status_code == 401:
                logging.warning("Токен устарел, очищаем кэш...")
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
                self.token = None
                return self.get_schedule(day)
            else:
                logging.error(f"Ошибка API: {response.status_code}")

        except ConnectionError as e:
            logging.error(f"🚨 {str(e)}")
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

def format_room(room):
    """Форматирование аудитории с большими буквами для дистанта"""
    if room and ('дист' in room.lower() or 'дистант' in room.lower() or 'online' in room.lower()):
        return "🚨 <b>ДИСТАНТ</b> 🚨"
    return room

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

async def safe_schedule_command(update: Update, context: CallbackContext, command_func):
    try:
        with ThreadPoolExecutor() as executor:
            schedule_task = asyncio.get_event_loop().run_in_executor(
                executor, 
                schedule_parser.get_schedule
            )
            schedule = await asyncio.wait_for(schedule_task, timeout=REQUEST_TIMEOUT + 5)
            
    except asyncio.TimeoutError:
        error_msg = (
            "🚨 <b>ДИСКОННЕКТ!</b> 🚨\n\n"
            "♂️ <b>САЙТ НЕ ОТВЕЧАЕТ</b> ♂️\n\n"
            "❌ Не удалось получить расписание:\n"
            "⏰ Превышено время ожидания\n"
            "🌐 Проблемы с подключением к сайту\n\n"
            "♂️ <i>Попробуйте позже</i> ♂️"
        )
        await update.message.reply_html(error_msg)
        return
    except ConnectionError as e:
        error_msg = (
            f"🚨 <b>ДИСКОННЕКТ!</b> 🚨\n\n"
            f"♂️ <b>САЙТ НЕ ДОСТУПЕН</b> ♂️\n\n"
            f"❌ {str(e)}\n\n"
            f"♂️ <i>Попробуйте позже</i> ♂️"
        )
        await update.message.reply_html(error_msg)
        return
    except Exception as e:
        error_msg = (
            "🚨 <b>ОШИБКА!</b> 🚨\n\n"
            f"❌ Произошла непредвиденная ошибка:\n"
            f"🔧 {str(e)}\n\n"
            "♂️ <i>Попробуйте позже</i> ♂️"
        )
        await update.message.reply_html(error_msg)
        return
    
    await command_func(update, context, schedule)

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    gachi_phrase = get_random_gachi()

    await update.message.reply_html(
        f"♂️ <b>WELCOME TO THE GYM, {user.first_name}! ♂️</b>\n\n"
        f"{gachi_phrase}\n\n"
        "🎓 <b>Бот расписания групп И-232, И-233</b>\n\n"
        "📋 <b>Доступные команды:</b>\n"
        "/today - расписание на сегодня\n"
        "/tomorrow - расписание на завтра\n"
        "/week - расписание на неделю\n"
        "/gachi - случайная гачи-фраза\n"
        "/help - список команд\n\n"
        "💡 <i>Начните вводить / чтобы увидеть все команды</i>\n\n"
        "♂️ <i>FUCKING SCHEDULE READY ♂️</i>"
    )

async def today_wrapper(update: Update, context: CallbackContext, schedule=None):
    today_date = datetime.now()
    day_name = get_day_name(today_date.isoweekday())
    gachi_phrase = get_random_gachi()

    if schedule and isinstance(schedule, list) and schedule:
        message = (
            f"📅 <b>♂️ РАСПИСАНИЕ НА СЕГОДНЯ ♂️</b>\n"
            f"📆 {today_date.strftime('%d.%m.%Y')}, {day_name}\n"
            f"🎓 Группы: И-232, И-233\n"
            f"🎯 Пар сегодня: {len(schedule)}\n\n"
        )

        for i, lesson in enumerate(schedule, 1):
            room = format_room(lesson.get('room', 'Аудитория'))
            message += (
                f"<b>{i}. {lesson.get('subject', 'Предмет')}</b>\n"
                f"   ⏰ {lesson.get('start_time', '')} - {lesson.get('end_time', '')}\n"
                f"   👨‍🏫 {lesson.get('teacher_full_name', 'Преподаватель')}\n"
                f"   🏫 {room}\n\n"
            )

        message += f"♂️ <i>{gachi_phrase}</i> ♂️"
    else:
        message = (
            f"🎉 <b>♂️ СЕГОДНЯ ПАР НЕТ! ♂️</b>\n"
            f"📆 {today_date.strftime('%d.%m.%Y')}, {day_name}\n"
            f"🎓 Группы: И-232, И-233\n\n"
            f"♂️ <i>{gachi_phrase}</i> ♂️"
        )

    await update.message.reply_html(message)

async def tomorrow_wrapper(update: Update, context: CallbackContext, schedule=None):
    tomorrow_date = datetime.now() + timedelta(days=1)
    day_num = tomorrow_date.isoweekday()
    day_name = get_day_name(day_num)
    gachi_phrase = get_random_gachi()

    if schedule and isinstance(schedule, list) and schedule:
        message = (
            f"📅 <b>♂️ РАСПИСАНИЕ НА ЗАВТРА ♂️</b>\n"
            f"📆 {tomorrow_date.strftime('%d.%m.%Y')}, {day_name}\n"
            f"🎓 Группы: И-232, И-233\n"
            f"🎯 Пар завтра: {len(schedule)}\n\n"
        )

        for i, lesson in enumerate(schedule, 1):
            room = format_room(lesson.get('room', 'Аудитория'))
            message += (
                f"<b>{i}. {lesson.get('subject', 'Предмет')}</b>\n"
                f"   ⏰ {lesson.get('start_time', '')} - {lesson.get('end_time', '')}\n"
                f"   👨‍🏫 {lesson.get('teacher_full_name', 'Преподаватель')}\n"
                f"   🏫 {room}\n\n"
            )

        message += f"♂️ <i>{gachi_phrase}</i> ♂️"
    else:
        message = (
            f"🎉 <b>♂️ ЗАВТРА ПАР НЕТ! ♂️</b>\n"
            f"📆 {tomorrow_date.strftime('%d.%m.%Y')}, {day_name}\n"
            f"🎓 Группы: И-232, И-233\n\n"
            f"♂️ <i>{gachi_phrase}</i> ♂️"
        )

    await update.message.reply_html(message)

async def today(update: Update, context: CallbackContext):
    await safe_schedule_command(update, context, today_wrapper)

async def tomorrow(update: Update, context: CallbackContext):
    tomorrow_date = datetime.now() + timedelta(days=1)
    day_num = tomorrow_date.isoweekday()
    
    try:
        with ThreadPoolExecutor() as executor:
            schedule_task = asyncio.get_event_loop().run_in_executor(
                executor, 
                lambda: schedule_parser.get_schedule(day_num)
            )
            schedule = await asyncio.wait_for(schedule_task, timeout=REQUEST_TIMEOUT + 5)
            
        await tomorrow_wrapper(update, context, schedule)
        
    except asyncio.TimeoutError:
        error_msg = (
            "🚨 <b>ДИСКОННЕКТ!</b> 🚨\n\n"
            "♂️ <b>САЙТ НЕ ОТВЕЧАЕТ</b> ♂️\n\n"
            "❌ Не удалось получить расписание на завтра:\n"
            "⏰ Превышено время ожидания\n"
            "🌐 Проблемы с подключением к сайту\n\n"
            "♂️ <i>Попробуйте позже</i> ♂️"
        )
        await update.message.reply_html(error_msg)
    except ConnectionError as e:
        error_msg = (
            f"🚨 <b>ДИСКОННЕКТ!</b> 🚨\n\n"
            f"♂️ <b>САЙТ НЕ ДОСТУПЕН</b> ♂️\n\n"
            f"❌ {str(e)}\n\n"
            f"♂️ <i>Попробуйте позже</i> ♂️"
        )
        await update.message.reply_html(error_msg)
    except Exception as e:
        error_msg = (
            "🚨 <b>ОШИБКА!</b> 🚨\n\n"
            f"❌ Произошла непредвиденная ошибка:\n"
            f"🔧 {str(e)}\n\n"
            "♂️ <i>Попробуйте позже</i> ♂️"
        )
        await update.message.reply_html(error_msg)

async def week(update: Update, context: CallbackContext):
    gachi_phrase = get_random_gachi()

    try:
        schedules = {}
        days = {
            1: "Понедельник", 2: "Вторник", 3: "Среда",
            4: "Четверг", 5: "Пятница", 6: "Суббота"
        }

        with ThreadPoolExecutor() as executor:
            tasks = {}
            for day_num, day_name in days.items():
                task = asyncio.get_event_loop().run_in_executor(
                    executor, 
                    lambda d=day_num: schedule_parser.get_schedule(d)
                )
                tasks[day_num] = task
            
            for day_num, task in tasks.items():
                try:
                    schedules[day_num] = await asyncio.wait_for(task, timeout=REQUEST_TIMEOUT + 5)
                except asyncio.TimeoutError:
                    schedules[day_num] = None
                except Exception:
                    schedules[day_num] = None

        message = (
            f"📅 <b>♂️ РАСПИСАНИЕ НА НЕДЕЛЮ ♂️</b>\n"
            f"🎓 Группы: И-232, И-233\n\n"
        )

        for day_num, day_name in days.items():
            schedule = schedules.get(day_num)

            message += f"<b>📖 {day_name}:</b>\n"

            if schedule and isinstance(schedule, list) and schedule:
                for i, lesson in enumerate(schedule, 1):
                    room = format_room(lesson.get('room', 'Аудитория'))
                    message += (
                        f"  {i}. <b>{lesson.get('subject', 'Предмет')}</b>\n"
                        f"     ⏰ {lesson.get('start_time', '')}-{lesson.get('end_time', '')}\n"
                        f"     🏫 {room}\n"
                    )
                if len(schedule) > 0:
                    message += "\n"
            else:
                message += "  🎉 Пар нет\n\n"

        message += f"♂️ <i>{gachi_phrase}</i> ♂️"

        if len(message) > 4096:
            parts = []
            current_part = ""
            lines = message.split('\n')

            for line in lines:
                if len(current_part + line + '\n') < 4096:
                    current_part += line + '\n'
                else:
                    parts.append(current_part)
                    current_part = line + '\n'

            if current_part:
                parts.append(current_part)

            for part in parts:
                await update.message.reply_html(part)
        else:
            await update.message.reply_html(message)

    except Exception as e:
        error_msg = (
            "🚨 <b>ДИСКОННЕКТ!</b> 🚨\n\n"
            "♂️ <b>САЙТ НЕ ОТВЕЧАЕТ</b> ♂️\n\n"
            "❌ Не удалось получить расписание на неделю:\n"
            f"🔧 {str(e)}\n\n"
            "♂️ <i>Попробуйте позже</i> ♂️"
        )
        await update.message.reply_html(error_msg)

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
