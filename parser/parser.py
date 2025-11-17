#!/usr/bin/env python3
import requests
import json
from datetime import datetime
import os
import time
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

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
            print(f"❌ Ошибка дешифрования: {e}")
            return None, None

def format_room(room):
    """Форматирование аудитории с большими буквами для дистанта"""
    if room and ('дист' in room.lower() or 'дистант' in room.lower() or 'online' in room.lower()):
        return "🚨 ДИСТАНТ 🚨"
    return room

class ScheduleParser:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = 'https://api.kktmobile-app.ru'
        self.web_url = 'https://kktmobile-app.ru'
        self.token = None
        self.token_file = 'token_cache.json'
        self.schedule_type = "students"
        self.groups = ["И-232", "И-233"] 
        
    def find_auth_endpoint(self):
        print("🔍 Поиск эндпоинта авторизации...")
        
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
            print(f"Ошибка поиска эндпоинта: {e}")
            return f'{self.base_url}/alogin'

    def get_auth_token(self):
        print("🔐 Авторизация...")
        
        endpoint = self.find_auth_endpoint()
        cred_manager = CredentialsManager()
        username, password = cred_manager.get_credentials()
        
        if not username or not password:
            print("❌ Не удалось получить учетные данные")
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
                print("✅ Авторизация успешна")
                return token_data.get('access_token')
            else:
                print(f"❌ Ошибка авторизации: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка авторизации: {e}")
        
        return None

    def load_cached_token(self):
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    token = data.get('token')
                    timestamp = data.get('timestamp', 0)
                    
                    if token and time.time() - timestamp < 43200: 
                        print("✅ Используется кэшированный токен")
                        return token
                    else:
                        print("⚠️ Токен устарел, требуется обновление")
        except Exception as e:
            print(f"⚠️ Ошибка загрузки токена: {e}")
        return None

    def save_token_to_cache(self, token):
        try:
            data = {'token': token, 'timestamp': time.time()}
            with open(self.token_file, 'w') as f:
                json.dump(data, f)
            print("✅ Токен сохранен в кэш")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения токена: {e}")

    def get_fresh_token(self):
        token = self.get_auth_token()
        if token:
            self.save_token_to_cache(token)
        return token

    def ensure_valid_token(self):
        cached_token = self.load_cached_token()
        if cached_token:
            if self.test_token(cached_token):
                self.token = cached_token
                return True
            else:
                print("❌ Кэшированный токен невалиден")
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
        
        print("🔄 Получение нового токена...")
        new_token = self.get_fresh_token()
        if new_token:
            self.token = new_token
            return True
        
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
            response = self.session.get(test_url, headers=headers, timeout=10)
            if response.status_code == 200:
                print("✅ Токен валиден")
                return True
            else:
                print(f"❌ Токен невалиден: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка проверки токена: {e}")
            return False

    def get_schedule(self, day=None):
        if not self.ensure_valid_token():
            print("❌ Не удалось получить валидный токен")
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
        
        try:
            print(f"📡 Запрос расписания для дня {day}...")
            response = self.session.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Расписание получено успешно ({len(data)} пар)")
                return data
            elif response.status_code == 401:
                print("❌ Токен устарел, очищаем кэш...")
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
                self.token = None
                return self.get_schedule(day)
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка получения расписания: {e}")
        
        return None

    def display_schedule(self, day=None):
        if day is None:
            today = datetime.now()
            current_day = today.isoweekday()
            date_display = today.strftime('%d.%m.%Y')
            day_name_key = current_day
        else:
            current_day = day
            date_display = f"день {current_day}"
            day_name_key = current_day
        
        days_names = {
            1: "понедельник", 2: "вторник", 3: "среда", 
            4: "четверг", 5: "пятница", 6: "суббота", 7: "воскресенье"
        }
        
        print(f"\n🎓 Расписание для групп: {', '.join(self.groups)}")
        print("=" * 50)
        print(f"📅 {date_display}, {days_names.get(day_name_key, 'день')}")
        print(f"📋 Тип: {'Для студентов' if self.schedule_type == 'students' else 'Для преподавателей'}\n")
        
        schedule = self.get_schedule(current_day)
        
        if schedule:
            if schedule:  
                print(f"🎯 Пар сегодня: {len(schedule)}\n")
                for i, lesson in enumerate(schedule, 1):
                    room = format_room(lesson.get('room', 'Аудитория'))
                    print(f"{i}. {lesson.get('subject', 'Предмет')}")
                    print(f"   🕐 {lesson.get('start_time', '')} - {lesson.get('end_time', '')}")
                    print(f"   👤 {lesson.get('teacher_full_name', 'Преподаватель')}")
                    print(f"   🏠 {room}\n")
            else:
                print("🎉 На выбранный день пар нет!")
        else:
            print("❌ Не удалось получить расписание")

    def display_weekly_schedule(self):
        print(f"\n📅 Расписание на неделю для групп: {', '.join(self.groups)}")
        print("=" * 50)
        print(f"📋 Тип: {'Для студентов' if self.schedule_type == 'students' else 'Для преподавателей'}\n")
        
        days_names = {
            1: "Понедельник", 2: "Вторник", 3: "Среда", 
            4: "Четверг", 5: "Пятница", 6: "Суббота"
        }
        
        for day_num, day_name in days_names.items():
            print(f"\n{day_name}:")
            print("-" * 30)
            
            schedule = self.get_schedule(day_num)
            
            if schedule:
                if schedule:  
                    for i, lesson in enumerate(schedule, 1):
                        room = format_room(lesson.get('room', 'Аудитория'))
                        print(f"  {i}. {lesson.get('subject', 'Предмет')}")
                        print(f"     🕐 {lesson.get('start_time', '')} - {lesson.get('end_time', '')}")
                        print(f"     👤 {lesson.get('teacher_full_name', 'Преподаватель')}")
                        print(f"     🏠 {room}")
                else:
                    print("  🎉 Пар нет")
            else:
                print("  ❌ Ошибка получения")

def main():
    parser = ScheduleParser()
    
    print("🎓 Парсер расписания ККТ")
    print("=" * 30)
    print("✅ Автоматические настройки:")
    print(f"   👤 Тип: Студент")
    print(f"   👥 Группы: {', '.join(parser.groups)}")
    
    parser.display_schedule()
    
    while True:
        print("\n🚀 Быстрое меню:")
        print("1. Расписание на сегодня")
        print("2. Расписание на неделю") 
        print("3. Выбрать день")
        print("4. Выход")
        
        choice = input("Ваш выбор (1-4): ").strip()
        
        if choice == "1":
            parser.display_schedule()
        elif choice == "2":
            parser.display_weekly_schedule()
        elif choice == "3":
            print("\n📅 Выберите день (1-6): ", end='')
            try:
                day = int(input().strip())
                if 1 <= day <= 6:
                    parser.display_schedule(day)
                else:
                    print("❌ Неверный день")
            except:
                print("❌ Неверный ввод")
        elif choice == "4":
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
