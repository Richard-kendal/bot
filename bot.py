from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Хранение данных пользователей (в реальном проекте используйте базу данных)
users_data = {}

# Начальная функция
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[KeyboardButton("Отправить местоположение", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text('Привет! Давай зарегистрируем тебя! Пожалуйста, отправь свое местоположение.', reply_markup=reply_markup)

# Функция для обработки местоположения
def location(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    location = update.message.location

    users_data[user_id] = {
        "name": None,  # Здесь можно попросить ввести имя
        "location": (location.latitude, location.longitude),
        "radius": None,
        "photo": None
    }
    
    update.message.reply_text('Спасибо! Теперь, пожалуйста, отправь фотографию.')

# Функция для загрузки фотографии
def photo_received(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    if user_id in users_data:
        file = update.message.photo[-1].get_file()
        file.download(f'{user_id}_photo.jpg')  # Сохранение фотографии
        users_data[user_id]['photo'] = f'{user_id}_photo.jpg'  # Сохранение пути к фото

        update.message.reply_text('Фотография загружена! Теперь выбери радиус поиска (1, 5, 10 км).')
        
def set_radius(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    radius = update.message.text

    if user_id in users_data:
        users_data[user_id]['radius'] = radius
        update.message.reply_text(f'Радиус поиска установлен на {radius} км. Готов к игре!')
        # Здесь можно запустить процесс поиска (не реализовано в данном примере)

def main() -> None:
    # Замена `YOUR_TOKEN` на токен вашего бота
    updater = Updater("7540520199:AAHDILtQfWgv3OrbDkMM5XFfCzX-WNrgvwA", use_context=True)
    
    dispatcher = updater.dispatcher

    # Обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))
    
    # Обработчик местоположения
    dispatcher.add_handler(MessageHandler(Filters.location, location))
    
    # Обработчик загрузки фотографий
    dispatcher.add_handler(MessageHandler(Filters.photo, photo_received))
    
    # Обработчик для установки радиуса (ввод пользователем)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, set_radius))

    # Запуск бота
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
