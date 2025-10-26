#!/usr/bin/env python3
import requests
import json
from datetime import datetime

def get_schedule(day=None):
    """Получает расписание группы И-232"""
    session = requests.Session()
    
    WORKING_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjgiLCJpYXQiOjE3NjE1MTIzNjgsIm5iZiI6MTc2MTUxMjM2OCwianRpIjoiNTY0ODg5MDQtZjgyNy00NGUxLTg5OTAtNDliOTI2Zjk3ZDNkIiwiZXhwIjoxNzYxNTk4NzY4LCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlfQ.L98Y-YZpInD1CRSjmKlHklDRtCr2xmT3P_5G7sNBJj4"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
        'Accept': 'application/json, text/plain, */*',
        'Authorization': f'Bearer {WORKING_TOKEN}',
        'Origin': 'https://kktmobile-app.ru',
        'Referer': 'https://kktmobile-app.ru/',
    }
    
    base_url = 'https://api.kktmobile-app.ru'
    group = 'И-232'
    
    if day is None:
        day = datetime.now().isoweekday()
    
    url = f'{base_url}/schedule/students/{group}/{day}'
    
    try:
        response = session.get(url, headers=headers)
        
        if response.status_code == 200:
            schedule_data = response.json()
            print("✅ Расписание успешно получено!")
            return schedule_data if schedule_data else None
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"💡 Ответ сервера: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
        return None

def display_schedule():
    """Отображает расписание"""
    today = datetime.now()
    current_day = today.isoweekday()
    
    days_names = {
        1: "понедельник", 2: "вторник", 3: "среда", 
        4: "четверг", 5: "пятница", 6: "суббота", 7: "воскресенье"
    }
    
    print("🎓 Расписание группы И-232")
    print("=" * 40)
    print(f"📅 {today.strftime('%d.%m.%Y')}, {days_names[current_day]}\n")
    
    schedule = get_schedule()
    
    if schedule is not None:
        if schedule:  
            print(f"🎯 Пар сегодня: {len(schedule)}\n")
            
            for i, lesson in enumerate(schedule, 1):
                print(f"{i}. {lesson.get('subject', 'Предмет')}")
                print(f"   🕐 {lesson.get('start_time', '')} - {lesson.get('end_time', '')}")
                print(f"   👤 {lesson.get('teacher_full_name', 'Преподаватель')}")
                print(f"   🏠 {lesson.get('room', 'Аудитория')}")
                print()
        else:
            print("🎉 Сегодня пар нет!")
    else:
        print("❌ Не удалось получить расписание")

def display_weekly_schedule():
    """Отображает расписание на всю неделю"""
    print("\n📅 Расписание на неделю")
    print("=" * 40)
    
    days_names = {
        1: "Понедельник", 2: "Вторник", 3: "Среда", 
        4: "Четверг", 5: "Пятница", 6: "Суббота"
    }
    
    has_lessons = False
    
    for day_num, day_name in days_names.items():
        print(f"\n{day_name}:")
        print("-" * 20)
        
        schedule = get_schedule(day_num)
        
        if schedule is not None:
            if schedule:  
                has_lessons = True
                for i, lesson in enumerate(schedule, 1):
                    print(f"  {i}. {lesson.get('subject', 'Предмет')}")
                    print(f"     🕐 {lesson.get('start_time', '')} - {lesson.get('end_time', '')}")
                    print(f"     👤 {lesson.get('teacher_full_name', 'Преподаватель')}")
                    print(f"     🏠 {lesson.get('room', 'Аудитория')}")
            else:
                print("  🎉 Пар нет")
        else:
            print("  ❌ Ошибка получения")
    
    if not has_lessons:
        print("\n💡 На этой неделе пар нет!")

if __name__ == "__main__":
    display_schedule()
    
    print("\nПосмотреть расписание на неделю? (д/н): ", end='')
    answer = input().lower()
    
    if answer in ['д', 'y', 'yes', 'да']:
        display_weekly_schedule()
