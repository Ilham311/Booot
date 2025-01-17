import telebot
import requests
import json
import re
import io
import tempfile
import threading
import time

TOKEN_BOT = "5219568853:AAF1-nRCJSOJqHY7r1S2QEM3n74EVRaUU6Y"
bot = telebot.TeleBot(TOKEN_BOT)

CHANNEL_USERNAME = "@BypasserID"

# Dictionary to store progress information for each user
progress_data = {}

def get_facebook_video_url(fb_url):
    url = 'https://aiovideodownloader.com/api/facebook'
    params = {'url': fb_url}
    headers = {
        'Host': 'aiovideodownloader.com',
        'accept-encoding': 'gzip',
        'user-agent': 'okhttp/4.9.2',
        'if-none-match': '"nm0oji8s3o1st"'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'hd' in data:
            return data['hd']
        elif 'sd' in data:
            return data['sd']
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except ValueError as e:
        print(f"JSON decoding error: {e}")
        print(f"Response content: {response.text}")
        return None

def download_and_upload_video(chat_id, user_id, platform, url):
    try:
        progress_data[user_id] = True
        msg_download = bot.send_message(chat_id, f"Sedang mengunduh video dari {platform}...")

        if platform == 'Facebook':
            video_url = get_facebook_video_url(url)
        elif platform == 'Instagram':
            response = requests.post(
                'https://api.cobalt.tools/api/json',
                json={'url': url, 'vQuality': '1080'},
                headers={'Accept': 'application/json'}
            )
            video_url = response.json().get('url')
        else:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            data = {
                "url": url
            }
            response = requests.post("https://co.wuk.sh/api/json", headers=headers, json=data)
            result = response.json()
            video_url = result.get("url", None)

        if video_url:
            upload_msg = bot.send_message(chat_id, "Video berhasil diunduh. Sedang mengunggah...")

            # Download video directly to memory without saving to a temporary file
            video_response = requests.get(video_url, stream=False)
            video_content = io.BytesIO(video_response.content)

            # Generate a random temporary filename with .mp4 extension
            temp_filename = tempfile.NamedTemporaryFile(suffix=".mp4").name

            # Upload the video directly
            bot.send_video(chat_id, video_content, timeout=40, supports_streaming=True)

            # Schedule deletion of messages after 10 seconds
            threading.Timer(10.0, delete_messages, args=(chat_id, msg_download.message_id, upload_msg.message_id)).start()

        else:
            bot.send_message(chat_id, "Terjadi kesalahan saat mengambil URL video.")

        # Clear progress for the user
        del progress_data[user_id]

    except Exception as e:
        bot.send_message(chat_id, f"Terjadi kesalahan: {str(e)}")
        # Clear progress for the user in case of an error
        if user_id in progress_data:
            del progress_data[user_id]

def delete_messages(chat_id, *message_ids):
    for message_id in message_ids:
        try:
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"Failed to delete message {message_id}: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    is_member = bot.get_chat_member(CHANNEL_USERNAME, user_id).status in ['member', 'administrator']

    if is_member:
        help_message = """
📷 /ig [URL] - Unduh video Instagram
📺 /yt [URL] - Ambil video YouTube
🐦 /tw [URL] - Download video Twitter
🎵 /tt [URL] - Unduh video TikTok
📘 /fb [URL] - Unduh video Facebook
"""
        bot.reply_to(message, f"Selamat datang! Gunakan perintah berikut:\n{help_message}")
    else:
        bot.reply_to(message, f"Maaf, Anda harus bergabung dengan saluran {CHANNEL_USERNAME} terlebih dahulu untuk menggunakan bot ini.")

@bot.message_handler(commands=['ig', 'yt', 'tw', 'tt', 'fb'])
def download_and_upload(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    is_member = bot.get_chat_member(CHANNEL_USERNAME, user_id).status in ['member', 'administrator']

    if message.chat.type == 'private' or message.chat.id == -1001438313485:
        if is_member:
            try:
                command, *args = message.text.split(maxsplit=1)

                if len(args) == 1:
                    platform = {
                        '/ig': 'Instagram',
                        '/yt': 'YouTube',
                        '/tw': 'Twitter',
                        '/tt': 'TikTok',
                        '/fb': 'Facebook'
                    }.get(command)

                    if platform:
                        url = args[0]

                        # Check progress for the user
                        if user_id in progress_data:
                            bot.send_message(chat_id, f"Anda masih memiliki proses unduhan/upload sebelumnya yang sedang berjalan.")
                        else:
                            download_and_upload_video(chat_id, user_id, platform, url)

                    else:
                        bot.send_message(chat_id, "Perintah salah. Ketik /help untuk bantuan.")

                else:
                    bot.send_message(chat_id, "Perintah salah. Ketik /help untuk bantuan.")

            except Exception as e:
                bot.send_message(chat_id, f"Terjadi kesalahan: Report @ilham_maulana1")
                # Clear progress for the user in case of an error
                if user_id in progress_data:
                    del progress_data[user_id]
        else:
            bot.send_message(chat_id, f"Maaf, Anda harus bergabung dengan saluran {CHANNEL_USERNAME} terlebih dahulu untuk menggunakan bot ini.")
    else:
        bot.reply_to(message, "Maaf, bot ini tidak dapat digunakan di grup.")

while True:
    try:
        bot.polling()
    except Exception as e:
        print(f"Bot crash: {str(e)}")
        time.sleep(3)  # Delay for 3 seconds before attempting to restart
