import telebot
from telebot import types
import cv2
import os
import json

# Создание бота
bot = telebot.TeleBot('YOUR_TELEGRAM_BOT_API_KEY')

# Папка для хранения данных пользователей
DATA_DIR = 'user_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Этот бот создан для знакомства. Начнем с нашего знакомства. Как ваше имя?")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_id = message.chat.id
    user_file = os.path.join(DATA_DIR, f'{user_id}.json')
    user_data = load_user_data(user_file)
    user_data['name'] = message.text
    save_user_data(user_file, user_data)
    bot.send_message(user_id, "Какой у вас возраст?")
    bot.register_next_step_handler(message, get_age)

def get_age(message):
    user_id = message.chat.id
    user_file = os.path.join(DATA_DIR, f'{user_id}.json')
    user_data = load_user_data(user_file)
    user_data['age'] = message.text
    save_user_data(user_file, user_data)
    bot.send_message(user_id, "В каком городе вы живете?")
    bot.register_next_step_handler(message, get_city)

def get_city(message):
    user_id = message.chat.id
    user_file = os.path.join(DATA_DIR, f'{user_id}.json')
    user_data = load_user_data(user_file)
    user_data['city'] = message.text
    save_user_data(user_file, user_data)
    bot.send_message(user_id, "Пожалуйста, отправьте ваше фото.")
    bot.register_next_step_handler(message, get_photo)

def get_photo(message):
    user_id = message.chat.id
    if message.content_type == 'photo':
        photo_file = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(photo_file.file_path)
        photo_path = os.path.join(DATA_DIR, f'{user_id}.jpg')
        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Проверка на наличие лица
        face_detected = detect_face(photo_path)
        if face_detected:
            bot.send_message(user_id, "Лицо на фото обнаружено. Ваш профиль сохранен.")
        else:
            bot.send_message(user_id, "Лицо на фото не обнаружено. Попробуйте снова.")
    else:
        bot.send_message(user_id, "Пожалуйста, отправьте фото.")

def detect_face(photo_path):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    img = cv2.imread(photo_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return len(faces) > 0

def load_user_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            return json.load(file)
    return {}

def save_user_data(filepath, data):
    with open(filepath, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Обработка всех текстовых сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.send_message(message.chat.id, "Извините, я понимаю только команду /start.")

# Запуск бота
bot.polling()
