import telebot
import urllib.parse
import requests
import json
import os
import asyncio

bot = telebot.TeleBot('')

@bot.message_handler(commands=['start'])
def start_message(message):
    #bot.reply_to(message, 'Hello!')
    bot.send_message(message.chat.id, "Hello, I'm Li. Welcome!!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    #bot.reply_to(message, message.text)
    try:
        encoded_text = urllib.parse.quote(message.text)
        response = requests.post('http://127.0.0.1:8000/chat?query='+encoded_text,timeout=100)
        if response.status_code == 200:
            aisay = json.loads(response.text)
            if "msg" in aisay:
                bot.reply_to(message, aisay["msg"]["output"])
                audio_path = f"{aisay['id']}.mp3"
                asyncio.run(check_audio(message,audio_path))
            else:
                bot.reply_to(message, "Sorry, I don't know how to answer you")
    except requests.RequestException as e:
        bot.reply_to(message, "Sorry, I don't know how to answer you")

async def check_audio(message,audio_path):
    while True:
        if os.path.exists(audio_path):
            with open(audio_path, 'rb') as f:
                bot.send_audio(message.chat.id, f)
            os.remove(audio_path)
            break
        else:
            print("waiting")
            await asyncio.sleep(1) #Use asyncio.sleep(1) to wait for 1 second

bot.infinity_polling()