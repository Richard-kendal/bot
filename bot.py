import telebot
import os
import json
from telebot import types
import cv2
import numpy as np
import math
import folium
import io
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Замените YOUR_TOKEN_HERE на токен вашего бота
bot = telebot.TeleBot("7540520199:AAHDILtQfWgv3OrbDkMM5XFfCzX-WNrgvwA")

# Список ID администраторов
admin_ids = [123456789, 987654321]

# Переменная для хранения состояния бота (вкл/выкл)
bot_active = True

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

# Загрузка предобученной модели для обнаружения лиц
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def is_human_present(image_path):
    # Загрузка изображения
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Обнаружение лиц на изображении
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    # Возвращаем True, если лицо обнаружено, иначе False
    return len(faces) > 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
    user_id = str(message.from_user.id)
    profile = user_profiles.get(user_id, None)
    if profile:
        response = f"Имя: {profile['name']}\nВозраст: {profile['age']}\nГород: {profile['city']}"
        if 'photo' in profile:
            with open(profile['photo'], 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=response)
        else:
            bot.reply_to(message, response)
    else:
        bot.send_photo(message.chat.id, open('welcome.jpg', 'rb'), caption="Привет! Я бот для создания профилей. Начнем с вашего имени. Пожалуйста, введите ваше имя.")
        bot.register_next_step_handler(message, get_name)

def get_name(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
    user_id = str(message.from_user.id)
    if user_id not in user_profiles:
        user_profiles[user_id] = {}
    user_profiles[user_id]['name'] = message.text
    bot.reply_to(message, 'Введите ваш возраст.')
    bot.register_next_step_handler(message, get_age)

def get_age(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
    user_id = str(message.from_user.id)
    if not message.text.isdigit():
        bot.reply_to(message, 'Возраст должен быть числом. Введите ваш возраст.')
        bot.register_next_step_handler(message, get_age)
        return
    user_profiles[user_id]['age'] = message.text
    bot.reply_to(message, 'Введите ваш город.')
    bot.register_next_step_handler(message, get_city)

def get_city(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
    user_id = str(message.from_user.id)
    user_profiles[user_id]['city'] = message.text
    bot.reply_to(message, 'Ваш профиль сохранен. Теперь отправьте свою фотографию.')
    save_profiles(user_profiles)
    bot.register_next_step_handler(message, get_photo)

def get_photo(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
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
        
        if is_human_present(photo_path):
            user_profiles[user_id]['photo'] = photo_path
            save_profiles(user_profiles)
            
            # Показываем дополнительные кнопки после заполнения профиля
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            profile_btn = types.KeyboardButton("Профиль")
            play_btn = types.KeyboardButton("Играть")
            rating_btn = types.KeyboardButton("Рейтинг")
            support_about_btn = types.KeyboardButton("Поддержка и О команде")
            markup.add(profile_btn, play_btn, rating_btn, support_about_btn)
            
            if message.from_user.id in admin_ids:
                admin_panel_btn = types.KeyboardButton("Админ панель")
                markup.add(admin_panel_btn)
            
            bot.reply_to(message, 'Фотография сохранена. Ваш профиль обновлен.', reply_markup=markup)
        else:
            bot.reply_to(message, 'На фото не обнаружено лицо. Пожалуйста, отправьте фото, на котором видно ваше лицо.')
            bot.register_next_step_handler(message, get_photo)
    else:
        bot.reply_to(message, 'Пожалуйста, отправьте фотографию.')
        bot.register_next_step_handler(message, get_photo)

@bot.message_handler(func=lambda message: message.text == "Профиль")
def get_profile(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
    user_id = str(message.from_user.id)
    profile = user_profiles.get(user_id, None)
    
    if profile:
        response = f"Имя: {profile['name']}\nВозраст: {profile['age']}\nГород: {profile['city']}"
        if 'photo' in profile:
            with open(profile['photo'], 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=response)
        else:
            bot.reply_to(message, response)

        # Добавление кнопок "Сменить фото профиля" и "Сменить город"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        change_photo_btn = types.KeyboardButton("Сменить фото профиля")
        change_city_btn = types.KeyboardButton("Сменить город")
        back_btn = types.KeyboardButton("Назад")
        markup.add(change_photo_btn, change_city_btn, back_btn)
        bot.reply_to(message, "Выберите действие:", reply_markup=markup)
    else:
        bot.reply_to(message, "Ваш профиль не найден. Пожалуйста, заполните ваш профиль.")

@bot.message_handler(func=lambda message: message.text == "Сменить фото профиля")
def change_photo(message):
    user_id = str(message.from_user.id)
    bot.reply_to(message, 'Пожалуйста, отправьте новое фото профиля.')
    bot.register_next_step_handler(message, get_new_photo)

def get_new_photo(message):
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
        
        if is_human_present(photo_path):
            user_profiles[user_id]['photo'] = photo_path
            save_profiles(user_profiles)
            bot.reply_to(message, 'Фотография обновлена.')
        else:
            bot.reply_to(message, 'На фото не обнаружено лицо. Пожалуйста, отправьте фото, на котором видно ваше лицо.')
            bot.register_next_step_handler(message, get_new_photo)
    else:
        bot.reply_to(message, 'Пожалуйста, отправьте фотографию.')
        bot.register_next_step_handler(message, get_new_photo)

@bot.message_handler(func=lambda message: message.text == "Сменить город")
def change_city(message):
    user_id = str(message.from_user.id)
    bot.reply_to(message, 'Пожалуйста, введите новый город.')
    bot.register_next_step_handler(message, get_new_city)

def get_new_city(message):
    user_id = str(message.from_user.id)
    user_profiles[user_id]['city'] = message.text
    save_profiles(user_profiles)
    bot.reply_to(message, 'Город обновлен.')

@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    profile_btn = types.KeyboardButton("Профиль")
    play_btn = types.KeyboardButton("Играть")
    rating_btn = types.KeyboardButton("Рейтинг")
    support_about_btn = types.KeyboardButton("Поддержка и О команде")
    markup.add(profile_btn, play_btn, rating_btn, support_about_btn)
    
    if message.from_user.id in admin_ids:
        admin_panel_btn = types.KeyboardButton("Админ панель")
        markup.add(admin_panel_btn)
    
    bot.reply_to(message, 'Вы вернулись в главное меню.', reply_markup=markup)

def distance(lat1, lon1, lat2, lon2):
    R = 6371  # радиус Земли в километрах
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c * 1000  # возвращаем расстояние в метрах

@bot.message_handler(func=lambda message: message.text == "Играть")
def play_game(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    normal_mode_btn = types.KeyboardButton("Обычный режим")
    markup.add(normal_mode_btn)
    bot.reply_to(message, "Выберите режим игры:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Обычный режим")
def normal_mode(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("Назад")
    markup.add(back_btn)
    bot.reply_to(message, "Игра началась! Ищу игроков в вашем городе...", reply_markup=markup)
    find_player(message)

@bot.message_handler(func=lambda message: message.text == "Поиск игрока")
def find_player(message):
    user_id = str(message.from_user.id)
    city = user_profiles[user_id]['city']
    
    found_players = False

    for uid, profile in user_profiles.items():
        if uid != user_id and profile.get('city') == city and 'location' in profile:
            other_lat = profile['location']['latitude']
            other_lon = profile['location']['longitude']
            bot.send_message(uid, f"Найден игрок в вашем городе! Имя: {user_profiles[user_id]['name']}, Возраст: {user_profiles[user_id]['age']}. Найдите его!")
            bot.send_message(message.chat.id, f"Найден игрок в вашем городе! Имя: {profile['name']}, Возраст: {profile['age']}. Найдите его!")
            if 'photo' in profile:
                with open(profile['photo'], 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption=f"Имя: {profile['name']}, Возраст: {profile['age']}")
            if 'photo' in user_profiles[user_id]:
                with open(user_profiles[user_id]['photo'], 'rb') as photo:
                    bot.send_photo(uid, photo, caption=f"Имя: {user_profiles[user_id]['name']}, Возраст: {user_profiles[user_id]['age']}")
            found_players = True

    if found_players:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        request_location_btn = types.KeyboardButton("Запросить геопозицию")
        markup.add(request_location_btn)
        bot.reply_to(message, "Игрок найден! Запрашиваю геопозицию...", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_btn = types.KeyboardButton("Назад")
        markup.add(back_btn)
        bot.reply_to(message, "Игроки не найдены. Продолжаю поиск...", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Запросить геопозицию")
def request_location(message):
    bot.reply_to(message, "Пожалуйста, отправьте свою геопозицию.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(types.KeyboardButton(text="Отправить геопозицию", request_location=True)))

@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = str(message.from_user.id)
    latitude = message.location.latitude
    longitude = message.location.longitude
    user_profiles[user_id]['location'] = {'latitude': latitude, 'longitude': longitude}
    save_profiles(user_profiles)
    
    for uid, profile in user_profiles.items():
        if uid != user_id and profile.get('city') == user_profiles[user_id]['city'] and 'location' in profile:
            other_lat = profile['location']['latitude']
            other_lon = profile['location']['longitude']
            distance_m = distance(latitude, longitude, other_lat, other_lon)
            bot.send_message(uid, f"Ваш противник находится в {distance_m:.2f} метрах от вас. Готовы начать игру?")
            bot.reply_to(message, f"Ваш противник находится в {distance_m:.2f} метрах от вас. Готовы начать игру?")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            ready_btn = types.KeyboardButton("Готовы")
            back_btn = types.KeyboardButton("Назад")
            markup.add(ready_btn, back_btn)
            bot.reply_to(message, "Нажмите 'Готовы', чтобы начать игру.", reply_markup=markup)
            return

@bot.message_handler(func=lambda message: message.text == "Готовы")
def ready_to_play(message):
    user_id = str(message.from_user.id)
    for uid, profile in user_profiles.items():
        if uid != user_id and profile.get('city') == user_profiles[user_id]['city'] and 'location' in profile:
            user_lat = user_profiles[user_id]['location']['latitude']
            user_lon = user_profiles[user_id]['location']['longitude']
            other_lat = profile['location']['latitude']
            other_lon = profile['location']['longitude']
            
            # Создание карты с диапазоном поиска
            map_center = [(user_lat + other_lat) / 2, (user_lon + other_lon) / 2]
            m = folium.Map(location=map_center, zoom_start=15)
            folium.Marker([user_lat, user_lon], tooltip='Вы').add_to(m)
            folium.Marker([other_lat, other_lon], tooltip='Противник').add_to(m)
            folium.Circle(location=map_center, radius=distance(user_lat, user_lon, other_lat, other_lon), color='blue', fill=True, fill_opacity=0.1).add_to(m)
            
            # Создаем папку для сохранения карт, если она не существует
            if not os.path.exists('maps'):
                os.makedirs('maps')
            
            map_path = f'maps/{user_id}_map.html'
            m.save(map_path)
            
            if os.path.exists(map_path) and os.path.getsize(map_path) > 0:
                # Конвертируем HTML-карту в изображение
                options = webdriver.ChromeOptions()
                options.add_argument('--headless')
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                driver.get(f'file://{os.path.abspath(map_path)}')
                img_data = driver.get_screenshot_as_png()
                driver.quit()
                
                img = Image.open(io.BytesIO(img_data))
                img_path = f'maps/{user_id}_map.png'
                img.save(img_path)
                
                with open(img_path, 'rb') as img_file:
                    bot.send_photo(message.chat.id, img_file, caption="Вот диапазон поиска. Найдите друг друга в этой области!")
                    bot.send_photo(uid, img_file, caption="Вот диапазон поиска. Найдите друг друга в этой области!")
            else:
                bot.reply_to(message, "Не удалось создать карту. Попробуйте еще раз.")
            return

def is_two_people_present(image_path):
    # Загрузка изображения
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Обнаружение лиц на изображении
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    # Возвращаем True, если обнаружено два лица, иначе False
    return len(faces) == 2

def compare_faces(face1_path, face2_path):
    # Загрузка изображений
    face1 = cv2.imread(face1_path)
    face2 = cv2.imread(face2_path)
    
    # Преобразование изображений в оттенки серого
    gray1 = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)
    
    # Обнаружение лиц на изображениях
    faces1 = face_cascade.detectMultiScale(gray1, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    faces2 = face_cascade.detectMultiScale(gray2, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    if len(faces1) == 1 and len(faces2) == 1:
        (x1, y1, w1, h1) = faces1[0]
        (x2, y2, w2, h2) = faces2[0]
        
        # Извлечение лиц из изображений
        face1_crop = gray1[y1:y1+h1, x1:x1+w1]
        face2_crop = gray2[y2:y2+h2, x2:x2+w2]
        
        # Сравнение лиц
        res = cv2.matchTemplate(face1_crop, face2_crop, cv2.TM_CCOEFF_NORMED)
        threshold = 0.6
        if res >= threshold:
            return True
    return False

@bot.message_handler(content_types=['photo'])
def end_game(message):
    user_id = str(message.from_user.id)
    if 'radius' in user_profiles[user_id]:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        photo_path = f'photos/{user_id}_endgame.jpg'
        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        if is_two_people_present(photo_path):
            for uid, profile in user_profiles.items():
                if uid != user_id and 'radius' in profile:
                    if compare_faces(user_profiles[user_id]['photo'], photo_path) and compare_faces(profile['photo'], photo_path):
                        bot.reply_to(message, "Поздравляем! Вы нашли друг друга и завершили игру.")
                        bot.send_message(uid, "Поздравляем! Вы нашли друг друга и завершили игру.")
                        # Очистить данные радиуса и локации
                        del user_profiles[user_id]['radius']
                        del user_profiles[user_id]['location']
                        del user_profiles[uid]['radius']
                        del user_profiles[uid]['location']
                        save_profiles(user_profiles)
                        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                        find_another_player_btn = types.KeyboardButton("Найти другого игрока")
                        main_menu_btn = types.KeyboardButton("В меню")
                        markup.add(find_another_player_btn, main_menu_btn)
                        bot.reply_to(message, "Выберите действие:", reply_markup=markup)
                    else:
                        bot.reply_to(message, "На фото должны быть вы и ваш противник. Попробуйте еще раз.")
        else:
            bot.reply_to(message, "На фото должно быть два человека. Попробуйте еще раз.")

@bot.message_handler(func=lambda message: message.text == "Рейтинг")
def show_rating(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
    # Добавьте сюда логику показа рейтинга
    bot.reply_to(message, "Вот текущий рейтинг!")

@bot.message_handler(func=lambda message: message.text == "Поддержка и О команде")
def support_and_about(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
    response = "Поддержка: свяжитесь с нами по email: support@example.com\n"
    response += "О команде: Мы команда разработчиков, работающих над этим проектом. Вы всегда можете обратиться к нам за помощью!"
    bot.reply_to(message, response)

@bot.message_handler(func=lambda message: message.text == "Админ панель" and message.from_user.id in admin_ids)
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    shutdown_btn = types.KeyboardButton("Отключить бота")
    enable_btn = types.KeyboardButton("Включить бота")
    notify_btn = types.KeyboardButton("Оповестить всех")
    list_users_btn = types.KeyboardButton("Список пользователей")
    back_btn = types.KeyboardButton("Назад")
    markup.add(shutdown_btn, enable_btn, notify_btn, list_users_btn, back_btn)
    bot.reply_to(message, "Админ панель", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Отключить бота" and message.from_user.id in admin_ids)
def shutdown_bot(message):
    global bot_active
    bot_active = False
    bot.reply_to(message, "Бот переведен в спящий режим. Администраторы все еще могут пользоваться ботом.")

@bot.message_handler(func=lambda message: message.text == "Включить бота" and message.from_user.id in admin_ids)
def enable_bot(message):
    global bot_active
    bot_active = True
    bot.reply_to(message, "Бот включен и снова доступен для всех пользователей.")

@bot.message_handler(func=lambda message: message.text == "Оповестить всех" and message.from_user.id in admin_ids)
def notify_all_users(message):
    bot.reply_to(message, "Введите сообщение для рассылки всем пользователям:")
    bot.register_next_step_handler(message, send_notification)

def send_notification(message):
    notification_text = message.text
    for user_id in user_profiles.keys():
        bot.send_message(user_id, f"Сообщение от админа: {notification_text}")
    bot.reply_to(message, "Сообщение отправлено всем пользователям.")

@bot.message_handler(func=lambda message: message.text == "Список пользователей" and message.from_user.id in admin_ids)
def list_all_users(message):
    if not bot_active and message.from_user.id not in admin_ids:
        return
    response = "Список всех зарегистрированных пользователей:\n"
    for user_id, profile in user_profiles.items():
        response += f"ID: {user_id}, Имя: {profile.get('name', 'Не указано')}, Возраст: {profile.get('age', 'Не указано')}, Город: {profile.get('city', 'Не указано')}\n"
    bot.reply_to(message, response)

bot.polling()
