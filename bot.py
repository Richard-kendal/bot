import telebot
import os
import json
from telebot import types

# Замените YOUR_TOKEN_HERE на токен вашего бота
bot = telebot.TeleBot("7540520199:AAHDILtQfWgv3OrbDkMM5XFfCzX-WNrgvwA")

# Файл для хранения профилей пользователей
profiles_file = 'user_profiles.json'

# Проверяем, существует ли файл профилей, если нет - создаем пустой файл
if not os.path.exists(profiles_file):
    with open(profiles_file, 'w') as f:
        json.dump({}, f)

def load_profiles():
    try:
        with open(profiles_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_profiles(profiles):
    with open(profiles_file, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, ensure_ascii=False, indent=4)

# Загружаем профили пользователей из файла
user_profiles = load_profiles()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    profile_btn = types.KeyboardButton("Профиль")
    location_btn = types.KeyboardButton("Моя геопозиция", request_location=True)
    markup.add(profile_btn, location_btn)
    bot.reply_to(message, "Привет! Я бот для создания профилей. Начнем с вашего имени. Пожалуйста, введите ваше имя.", reply_markup=markup)
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_id = str(message.from_user.id)
    if user_id not in user_profiles:
        user_profiles[user_id] = {}
    user_profiles[user_id]['name'] = message.text
    bot.reply_to(message, 'Введите ваш возраст.')
    bot.register_next_step_handler(message, get_age)

def get_age(message):
    user_id = str(message.from_user.id)
    user_profiles[user_id]['age'] = message.text
    bot.reply_to(message, 'Введите ваш город.')
    bot.register_next_step_handler(message, get_city)

def get_city(message):
    user_id = str(message.from_user.id)
    user_profiles[user_id]['city'] = message.text
    bot.reply_to(message, 'Ваш профиль сохранен. Теперь отправьте свою фотографию.')
    save_profiles(user_profiles)
    bot.register_next_step_handler(message, get_photo)

def get_photo(message):
    user_id = str(message.from_user.id)
    if message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Создаем папку для сохранения фотографий, если она не существует
        if not os.path.exists('photos'):
            os.makedirs('photos')

        photo_path = f'photos/{user_id}.jpg'
        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        user_profiles[user_id]['photo'] = photo_path
        save_profiles(user_profiles)
        bot.reply_to(message, 'Фотография сохранена. Ваш профиль обновлен.')
    else:
        bot.reply_to(message, 'Пожалуйста, отправьте фотографию.')

@bot.message_handler(func=lambda message: message.text == "Профиль")
def get_profile(message):
    user_id = str(message.from_user.id)
    profile = user_profiles.get(user_id, None)
    
    if profile:
        response = f"Имя: {profile['name']}\nВозраст: {profile['age']}\nГород: {profile['city']}"
        if 'photo' in profile:
            with open(profile['photo'], 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Ваш профиль не найден. Пожалуйста, заполните ваш профиль.")

@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = str(message.from_user.id)
    latitude = message.location.latitude
    longitude = message.location.longitude
    user_profiles[user_id]['location'] = {'latitude': latitude, 'longitude': longitude}
    save_profiles(user_profiles)
    bot.reply_to(message, f'Ваша геопозиция сохранена: широта - {latitude}, долгота - {longitude}')

bot.polling()
