import telebot
from telebot import types
from geopy.distance import geodesic
import folium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import io
import os

API_TOKEN = '7540520199:AAHDILtQfWgv3OrbDkMM5XFfCzX-WNrgvwA'
bot = telebot.TeleBot(API_TOKEN)
users = {}
screenshots_folder = 'screenshots'
if not os.path.exists(screenshots_folder):
    os.makedirs(screenshots_folder)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    play_button = types.KeyboardButton('Играть')
    markup.add(play_button)
    bot.send_message(message.chat.id, "Добро пожаловать! Нажмите 'Играть' чтобы начать.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Играть')
def choose_mode(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    normal_mode_button = types.KeyboardButton('Обычный режим')
    back_button = types.KeyboardButton('Назад в меню')
    markup.add(normal_mode_button, back_button)
    bot.send_message(message.chat.id, "Выберите режим игры.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ['Обычный режим', 'Назад в меню'])
def handle_mode_choice(message):
    if message.text == 'Обычный режим':
        request_location(message)
    elif message.text == 'Назад в меню':
        send_welcome(message)

def request_location(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    location_button = types.KeyboardButton('Отправить местоположение', request_location=True)
    back_button = types.KeyboardButton('Назад в меню')
    markup.add(location_button, back_button)
    bot.send_message(message.chat.id, "Отправьте ваше местоположение или нажмите 'Назад в меню'.", reply_markup=markup)

@bot.message_handler(content_types=['location'])
def handle_location(message):
    user_id = message.chat.id
    users[user_id] = {
        'location': (message.location.latitude, message.location.longitude),
        'status': 'waiting',
        'agreed': False
    }
    find_player_prompt(message)

def find_player_prompt(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    find_player_button = types.KeyboardButton('Найти игрока')
    back_button = types.KeyboardButton('Назад в меню')
    markup.add(find_player_button, back_button)
    bot.send_message(message.chat.id, "Теперь нажмите 'Найти игрока' или 'Назад в меню'.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Найти игрока')
def find_player(message):
    user_id = message.chat.id
    if users.get(user_id):
        users[user_id]['status'] = 'searching'
        for other_user_id, other_user_data in users.items():
            if other_user_id != user_id and other_user_data['status'] == 'searching':
                users[user_id]['status'] = 'found'
                users[other_user_id]['status'] = 'found'
                exchange_profiles(user_id, other_user_id)
                return
        bot.send_message(message.chat.id, "Поиск игрока...")
    else:
        send_welcome(message)

def exchange_profiles(user_id, other_user_id):
    bot.send_message(user_id, f"Игрок найден: {other_user_id}")
    bot.send_message(other_user_id, f"Игрок найден: {user_id}")
    offer_to_play(user_id, other_user_id)

def offer_to_play(user_id, other_user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    play_button = types.KeyboardButton('Играть с найденным игроком')
    find_another_button = types.KeyboardButton('Найти другого игрока')
    markup.add(play_button, find_another_button)
    bot.send_message(user_id, "Хотите играть с этим игроком?", reply_markup=markup)
    bot.send_message(other_user_id, "Хотите играть с этим игроком?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ['Играть с найденным игроком', 'Найти другого игрока'])
def handle_play_choice(message):
    user_id = message.chat.id
    other_user_id = None
    for u_id, data in users.items():
        if data['status'] == 'found' and u_id != user_id:
            other_user_id = u_id
            break

    if other_user_id is None:
        bot.send_message(user_id, "Ошибка: другой игрок не найден.")
        find_player(message)
        return

    if message.text == 'Играть с найденным игроком':
        users[user_id]['agreed'] = True
        if users[other_user_id]['agreed']:
            start_game(user_id, other_user_id)
    elif message.text == 'Найти другого игрока':
        bot.send_message(user_id, "Ищем другого игрока...")
        users[user_id]['status'] = 'waiting'
        users[other_user_id]['status'] = 'waiting'
        users[user_id]['agreed'] = False
        users[other_user_id]['agreed'] = False
        find_player_prompt(message)

def start_game(user_id, other_user_id):
    loc1 = users[user_id]['location']
    loc2 = users[other_user_id]['location']
    distance = geodesic(loc1, loc2).meters
    radius = distance / 2
    if create_radius_map(loc1, loc2, radius, user_id, other_user_id):
        bot.send_message(user_id, f"Игра началась! Расстояние между игроками: {distance:.2f} метров. Радиус поиска: {radius:.2f} метров.")
        bot.send_message(other_user_id, f"Игра началась! Расстояние между игроками: {distance:.2f} метров. Радиус поиска: {radius:.2f} метров.")
        send_image(user_id, other_user_id)
    else:
        bot.send_message(user_id, "Не удалось создать карту с радиусом.")
        bot.send_message(other_user_id, "Не удалось создать карту с радиусом.")

def create_radius_map(loc1, loc2, radius, user_id, other_user_id):
    try:
        m = folium.Map(location=[(loc1[0] + loc2[0]) / 2, (loc1[1] + loc2[1]) / 2], zoom_start=18)
        folium.Marker(location=loc1, popup='Игрок 1', icon=folium.Icon(color='red')).add_to(m)
        folium.Marker(location=loc2, popup='Игрок 2', icon=folium.Icon(color='green')).add_to(m)
        folium.Circle(location=loc1, radius=radius, color='blue', fill=True, fill_opacity=0.1).add_to(m)
        html_path = os.path.join(screenshots_folder, f'{user_id}_{other_user_id}_radius.html')
        m.save(html_path)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(f'file://{os.path.abspath(html_path)}')
        screenshot_path = os.path.join(screenshots_folder, f'{user_id}_{other_user_id}_radius.png')
        driver.save_screenshot(screenshot_path)
        driver.quit()
        if os.path.getsize(screenshot_path) > 0:
            return True
        else:
            print("Error: The image file is empty or corrupted.")
            return False
    except Exception as e:
        print(f"Error creating map: {e}")
        return False

def send_image(user1_chat_id, user2_chat_id):
    screenshot_path = os.path.join(screenshots_folder, f'{user1_chat_id}_{user2_chat_id}_radius.png')
    if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 0:
        try:
            with open(screenshot_path, 'rb') as photo:
                bot.send_photo(user1_chat_id, photo)
        except Exception as e:
            print(f"Error sending photo to user1 ({user1_chat_id}): {e}")

        try:
            with open(screenshot_path, 'rb') as photo:
                bot.send_photo(user2_chat_id, photo)
        except Exception as e:
            print(f"Error sending photo to user2 ({user2_chat_id}): {e}")

        os.remove(screenshot_path)
    else:
        print("Error: The image file does not exist or is empty.")

@bot.message_handler(func=lambda message: message.text == 'Назад в меню')
def back_to_menu(message):
    send_welcome(message)

bot.polling()
