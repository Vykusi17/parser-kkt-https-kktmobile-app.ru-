#!/usr/bin/env python3
import requests
import json
from datetime import datetime

def get_schedule(day=None):
    """Получает расписание группы И-232"""
    session = requests.Session()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjgiLCJpYXQiOjE3NjEzMzQwNjAsIm5iZiI6MTc2MTMzNDA2MCwianRpIjoiMGEwZjM3NzAtMjYxNC00MzZhLThiNTUtM2EyN2VlNmM5ZWQwIiwiZXhwIjoxNzYxNDIwNDYwLCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlfQ.CoZXOGlOqT1ov-o_avCZQkSlZ4RJvjbqE9CB_lEa3O0',
    }
    
    base_url = 'https://api.kktmobile-app.ru'
    group = 'И-232'
    
    days_names = {
        1: "Понедельник", 2: "Вторник", 3: "Среда", 
        4: "Четверг", 5: "Пятница", 6: "Суббота", 7: "Воскресенье"
    }
    
    if day is None:
        day = datetime.now().isoweekday()
    
    url = f'{base_url}/schedule/students/{group}/{day}'
    
    try:
        response = session.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception:
        return None

def display_schedule():
    """Отображает расписание"""
    today = datetime.now()
    current_day = today.isoweekday()
    
    print("🎓 Расписание группы И-232")
    print("=" * 40)
    print(f"📅 {today.strftime('%d.%m.%Y')}\n")
    
    schedule = get_schedule()
    
    if schedule and isinstance(schedule, list) and schedule:
        print(f"Пар сегодня: {len(schedule)}\n")
        
        for i, lesson in enumerate(schedule, 1):
            print(f"{i}. {lesson.get('subject', 'Предмет')}")
            print(f"   🕐 {lesson.get('start_time', '')} - {lesson.get('end_time', '')}")
            print(f"   👤 {lesson.get('teacher_full_name', 'Преподаватель')}")
            print(f"   🏠 {lesson.get('room', 'Аудитория')}")
            print()
    else:
        print("🎉 Сегодня пар нет!")

def display_weekly_schedule():
    """Отображает расписание на всю неделю"""
    print("\n📅 Расписание на неделю")
    print("=" * 40)
    
    days_names = {
        1: "Понедельник", 2: "Вторник", 3: "Среда", 
        4: "Четверг", 5: "Пятница", 6: "Суббота"
    }
    
    for day_num, day_name in days_names.items():
        print(f"\n{day_name}:")
        print("-" * 20)
        
        schedule = get_schedule(day_num)
        
        if schedule and isinstance(schedule, list) and schedule:
            for i, lesson in enumerate(schedule, 1):
                print(f"  {i}. {lesson.get('subject', 'Предмет')}")
                print(f"     🕐 {lesson.get('start_time', '')} - {lesson.get('end_time', '')}")
                print(f"     👤 {lesson.get('teacher_full_name', 'Преподаватель')}")
                print(f"     🏠 {lesson.get('room', 'Аудитория')}")
        else:
            print("  Пар нет")

if __name__ == "__main__":
    display_schedule()
    
    print("\nПосмотреть расписание на неделю? (д/н): ", end='')
    answer = input().lower()
    
    if answer in ['д', 'y', 'yes', 'да']:
        display_weekly_schedule()
