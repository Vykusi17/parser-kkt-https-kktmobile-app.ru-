#!/usr/bin/env python3
import requests
import logging
import random
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackContext

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "токен"
API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Accept': 'application/json, text/plain, */*',
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjgiLCJpYXQiOjE3NjEzMzQwNjAsIm5iZiI6MTc2MTMzNDA2MCwianRpIjoiMGEwZjM3NzAtMjYxNC00MzZhLThiNTUtM2EyN2VlNmM5ZWQwIiwiZXhwIjoxNzYxNDIwNDYwLCJ0eXBlIjoiYWNjZXNzIiwiZnJlc2giOmZhbHNlfQ.CoZXOGlOqT1ov-o_avCZQkSlZ4RJvjbqE9CB_lEa3O0',
}
BASE_URL = 'https://api.kktmobile-app.ru'
GROUP = 'И-232'

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

def get_schedule(day=None):
    if day is None:
        day = datetime.now().isoweekday()
    
    url = f'{BASE_URL}/schedule/students/{GROUP}/{day}'
    
    try:
        response = requests.get(url, headers=API_HEADERS)
        return response.json() if response.status_code == 200 else None
    except Exception:
        return None

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
    
    schedule = get_schedule()
    
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
    
    schedule = get_schedule(day_num)
    
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
    """Расписание на неделю"""
    gachi_phrase = get_random_gachi()
    
    message = "📅 <b>♂️ РАСПИСАНИЕ НА НЕДЕЛЮ ♂️</b>\n\n"
    
    days = {
        1: "Понедельник", 2: "Вторник", 3: "Среда", 
        4: "Четверг", 5: "Пятница", 6: "Суббота"
    }
    
    for day_num, day_name in days.items():
        schedule = get_schedule(day_num)
        
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

def get_day_name(day_num):

    days = {
        1: "понедельник", 2: "вторник", 3: "среда",
        4: "четверг", 5: "пятница", 6: "суббота", 7: "воскресенье"
    }
    return days.get(day_num, "день")

def main():

    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("tomorrow", tomorrow))
    application.add_handler(CommandHandler("week", week))
    application.add_handler(CommandHandler("gachi", gachi_command))
    application.add_handler(CommandHandler("help", help_command))
    
    application.post_init = set_bot_commands

    print("BOT")
    application.run_polling()

if __name__ == "__main__":
    main()
