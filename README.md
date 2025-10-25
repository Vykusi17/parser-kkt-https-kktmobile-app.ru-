# 📚 Парсер расписания ККТ

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20NixOS%20%7C%20Windows-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Парсер для автоматического получения расписания занятий группы И-232 с официального портала ККТ (https://kktmobile-app.ru). Проект включает консольную версию и Telegram бота.

## ✨ Особенности

- 🎯 **Автоматическое определение текущей даты** - всегда актуальное расписание
- 📅 **Гибкий просмотр** - на сегодня или на всю неделю
- 👨‍🏫 **Полная информация** - предметы, преподаватели, аудитории, время
- 🤖 **Telegram бот** - удобный доступ через мессенджер
- 🚀 **Простота использования** - запуск одной командой
- 🔧 **Кроссплатформенность** - работает на NixOS, других дистрибутивах Linux и Windows

## 🛠 Установка

### Клонирование репозитория

```bash
git clone https://github.com/Vykusi17/parser-kkt-https-kktmobile-app.ru-.git
cd parser-kkt-https-kktmobile-app.ru-
```

## 🖥 Консольная версия

### Запуск на NixOS / с Nix

```bash
cd parser
nix-shell shell.nix
python parser.py
```

### Запуск на других дистрибутивах Linux

```bash
cd parser
pip install requests
python parser.py
```

### Запуск на Windows

```cmd
cd parser
pip install requests
python parser.py
```

## 🤖 Telegram бот

Бот доступен по ссылке: [@parser_kkt_bot](https://t.me/parser_kkt_bot)

### Локальный запуск бота

#### С использованием Nix

```bash
cd telegram-bot
nix-shell bot.nix
python bot.py
```

#### С использованием pip

```bash
cd telegram-bot
pip install -r requirements.txt
python bot.py
```

### Команды бота

- `/start` - начать работу
- `/today` - расписание на сегодня
- `/tomorrow` - расписание на завтра  
- `/week` - расписание на неделю
- `/gachi` - случайная гачи-фраза
- `/help` - справка по командам
