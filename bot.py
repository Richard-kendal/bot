import telebot

API_TOKEN = '7540520199:AAHDILtQfWgv3OrbDkMM5XFfCzX-WNrgvwA'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет, я ваш телеграм-бот!")

bot.polling()
