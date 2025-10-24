# 📚 Парсер расписания ККТ

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20NixOS%20%7C%20Windows-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

Парсер для автоматического получения расписания занятий группы И-232 с официального портала ККТ (https://kktmobile-app.ru). Проект предоставляет удобный интерфейс для просмотра актуального расписания в терминале.

## ✨ Особенности

- 🎯 **Автоматическое определение текущей даты** - всегда актуальное расписание
- 📅 **Гибкий просмотр** - на сегодня или на всю неделю
- 👨‍🏫 **Полная информация** - предметы, преподаватели, аудитории, время
- 🚀 **Простота использования** - запуск одной командой
- 🔧 **Кроссплатформенность** - работает на NixOS, других дистрибутивах Linux и Windows

## 🛠 Установка

### Клонирование репозитория

```bash
git clone https://github.com/Vykusi17/parser-kkt-https-kktmobile-app.ru-.git
cd parser-kkt-https-kktmobile-app.ru-
```

### Способ 1: Запуск на NixOS / с Nix

```bash
nix-shell shell.nix

python get_real_schedule.py
```

### Способ 2: Запуск на других дистрибутивах Linux

```bash
pip install requests

python get_real_schedule.py
```

### Способ 3: Запуск на Windows

```cmd
# Установить Python 3.11+
# Установить зависимости
pip install requests

# Запустить парсер
python get_real_schedule.py
```

## 🚀 Использование

```bash
python get_real_schedule.py
```
