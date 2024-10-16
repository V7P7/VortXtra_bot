import os
import logging
from dotenv import load_dotenv
import telebot
import shutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from keep_alive import keep_alive

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv('TOKEN')
print(f"Oyeeee! I'm working!! 🤖")

# Configure logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['storage'])
def handle_storage(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    # Get disk usage information
    total, used, free = shutil.disk_usage(os.getcwd())

    # Convert bytes to GB for easier readability
    total_gb = total / (1024 ** 3)
    used_gb = used / (1024 ** 3)
    free_gb = free / (1024 ** 3)

    # Format the message
    storage_info = f"""
💾 Storage Information:
- Total: {total_gb:.2f} GB
- Used: {used_gb:.2f} GB
- Free: {free_gb:.2f} GB
    """

    bot.reply_to(message, storage_info)
    logging.info(f"User '{user_sessions[message.chat.id]}' requested storage information.")

# Create a directory to store uploaded files
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

user_sessions = {}

user_sessions.clear()

def main_menu():
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton("Login", callback_data="suggest_login"),
        telebot.types.InlineKeyboardButton("Upload", callback_data="suggest_upload"),
        telebot.types.InlineKeyboardButton("List Files", callback_data="suggest_list_files")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("Download", callback_data="suggest_download"),
        telebot.types.InlineKeyboardButton("Rename", callback_data="suggest_rename"),
        telebot.types.InlineKeyboardButton("Delete", callback_data="suggest_delete"),
        telebot.types.InlineKeyboardButton("Logout", callback_data="suggest_logout")
    )
    return keyboard


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Welcome to the bot! Use the menu below:", reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    suggestions = {
        "suggest_login": "Please use the command: /login <username> <password>",
        "suggest_upload": "Please use the command: /upload to attach a file.",
        "suggest_list_files": "Please use the command: /list to see your files.",
        "suggest_download": "Please use the command: /download <file_name>",
        "suggest_rename": "Please use the command: /rename <old_name> <new_name>",
        "suggest_delete": "Please use the command: /delete <file_name>",
        "suggest_logout": "You can logout using: /logout"
    }

    suggestion_message = suggestions.get(call.data, "❓ Command not found.")
    bot.send_message(call.message.chat.id, suggestion_message)


@bot.inline_handler(func=lambda query: True)
def handle_inline_query(inline_query):
    commands = [
        telebot.types.InlineQueryResultArticle(
            id='1',
            title='Login',
            input_message_content=telebot.types.InputTextMessageContent('/login <username> <password>'),
            description='Log in to your account.'
        ),
        telebot.types.InlineQueryResultArticle(
            id='2',
            title='Upload',
            input_message_content=telebot.types.InputTextMessageContent('/upload'),
            description='Upload a file.'
        ),
        telebot.types.InlineQueryResultArticle(
            id='3',
            title='List Files',
            input_message_content=telebot.types.InputTextMessageContent('/list'),
            description='See your uploaded files.'
        ),
        telebot.types.InlineQueryResultArticle(
            id='4',
            title='Download',
            input_message_content=telebot.types.InputTextMessageContent('/download <file_name>'),
            description='Download a file.'
        ),
        telebot.types.InlineQueryResultArticle(
            id='5',
            title='Rename',
            input_message_content=telebot.types.InputTextMessageContent('/rename <old_name> <new_name>'),
            description='Rename a file.'
        ),
        telebot.types.InlineQueryResultArticle(
            id='6',
            title='Delete',
            input_message_content=telebot.types.InputTextMessageContent('/delete <file_name>'),
            description='Delete a file.'
        ),
        telebot.types.InlineQueryResultArticle(
            id='7',
            title='Logout',
            input_message_content=telebot.types.InputTextMessageContent('/logout'),
            description='Log out from your account.'
        )
    ]

    bot.answer_inline_query(inline_query.id, commands)


# The rest of your existing command handlers go here...
def authenticate_user(username, password):
    # Check if the provided username and password match the stored values
    return username == os.getenv('user') and password == os.getenv('password')

@bot.message_handler(commands=['login'])
def handle_login(message):
    text_split = message.text.split()
    if len(text_split) < 3:
        bot.reply_to(message, "❓ Please provide a username and password in the format: /login <username> <password>")
        return

    username = text_split[1]
    password = text_split[2]

    if authenticate_user(username, password):
        user_sessions[message.chat.id] = username
        bot.reply_to(message, f"✅ Welcome, {username}! You are now logged in.")
        logging.info(f"User '{username}' logged in.")
    else:
        bot.reply_to(message, "❌ Invalid username or password.")
        logging.warning(f"Failed login attempt for username: '{username}'.")


@bot.message_handler(commands=['logout'])
def handle_logout(message):
    if message.chat.id in user_sessions:
        username = user_sessions[message.chat.id]
        del user_sessions[message.chat.id]
        bot.reply_to(message, "✅ You have been logged out.")
        logging.info(f"User '{username}' logged out.")
    else:
        bot.reply_to(message, "❌ You are not logged in.")

def is_authenticated(message):
    return message.chat.id in user_sessions


@bot.message_handler(commands=['upload'])
def handle_upload_command(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    current_time = time.time()
    last_command_time = user_command_time.get(message.chat.id, 0)

    if current_time - last_command_time < 5:
        bot.reply_to(message, "⏳ Please wait before using the command again.")
        return

    user_command_time[message.chat.id] = current_time
    bot.reply_to(message, "📁 Please attach a file with the /upload command.")


@bot.message_handler(content_types=['document', 'photo', 'video'])
def handle_file(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    if message.document:
        file_size = message.document.file_size
        file_info = message.document
        file_name = message.document.file_name
    elif message.photo:
        file_size = message.photo[-1].file_size
        file_info = message.photo[-1]
        file_name = "photo.jpg"
    elif message.video:
        file_size = message.video.file_size
        file_info = message.video
        file_name = "video.mp4"
    else:
        bot.reply_to(message, "❌ Please attach a document, photo, or video with the /upload command.")
        return

    if file_size > 20 * 1024 * 1024:
        bot.reply_to(message, "🚫 Unsuccessful transfer! Maximum file size is 20MB.")
        logging.warning(f"File upload failed for user '{user_sessions[message.chat.id]}': File size exceeds 20MB.")
        return

    bot.send_message(message.chat.id, "📤 File upload started...")
    try:
        file_info_full = bot.get_file(file_info.file_id)
        file_content = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info_full.file_path}", stream=True)
        file_content.raise_for_status()

        with open(os.path.join(UPLOAD_DIR, file_name), 'wb') as f:
            for data in file_content.iter_content(1024):
                f.write(data)

        bot.send_message(message.chat.id, f"✅ File uploaded successfully! You can access it as: {file_name}")
        logging.info(f"File '{file_name}' uploaded by user '{user_sessions[message.chat.id]}'.")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ An error occurred during file upload.")
        logging.error(f"Error uploading file for user '{user_sessions[message.chat.id]}': {str(e)}")


def get_session_with_retries():
    session = requests.Session()
    retries = Retry(
        total=5,  # Retry up to 5 times
        backoff_factor=1,  # Wait 1, 2, 4, 8... seconds between retries
        status_forcelist=[502, 503, 504],  # Retry on these HTTP statuses
        allowed_methods=["POST", "GET"]  # Apply retry logic to these methods
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# File download handler with retry and timeout handling
@bot.message_handler(commands=['download'])
def handle_download(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    text_split = message.text.split()
    if len(text_split) < 2:
        bot.reply_to(message, "❓ Please provide a file name after the /download command.")
        return

    file_name = text_split[1]
    file_path = os.path.join(UPLOAD_DIR, file_name)

    if os.path.exists(file_path):
        try:
            file_size = os.path.getsize(file_path)  # Get file size
            max_file_size = 50 * 1024 * 1024  # 50 MB limit for regular bot uploads

            if file_size > max_file_size:
                bot.reply_to(message, "❌ File is too large to be uploaded via Telegram (50 MB limit).")
                logging.warning(
                    f"File '{file_name}' is too large to upload for user '{user_sessions[message.chat.id]}'.")
                return

            with open(file_path, 'rb') as f:
                bot.send_document(message.chat.id, f, timeout=180)  # Increase timeout for larger files
                logging.info(f"User '{user_sessions[message.chat.id]}' downloaded file '{file_name}'.")

        except requests.exceptions.Timeout:
            bot.reply_to(message, "⏳ The download request timed out. Please try again.")
        except requests.exceptions.ConnectionError as e:
            bot.reply_to(message, f"❌ Connection error: {str(e)}. Please try again later.")
        except Exception as e:
            bot.reply_to(message, f"❌ An unexpected error occurred: {str(e)}.")
            logging.error(f"Error downloading file '{file_name}': {str(e)}")
    else:
        bot.reply_to(message, "❌ File not found.")
        logging.warning(f"File '{file_name}' not found for user '{user_sessions[message.chat.id]}'.")

@bot.message_handler(commands=['rename'])
def handle_rename(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    text_split = message.text.split()
    if len(text_split) < 3:
        bot.reply_to(message, "❓ Please provide the old and new file names after the /rename command.")
        return

    old_file_name = text_split[1]
    new_file_name = text_split[2]
    old_file_path = os.path.join(UPLOAD_DIR, old_file_name)
    new_file_path = os.path.join(UPLOAD_DIR, new_file_name)

    if os.path.exists(old_file_path):
        try:
            os.rename(old_file_path, new_file_path)
            bot.reply_to(message, f"✏️ File renamed successfully from {old_file_name} to {new_file_name}.")
            logging.info(f"User '{user_sessions[message.chat.id]}' renamed file '{old_file_name}' to '{new_file_name}'.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to rename file: {str(e)}")
            logging.error(f"Error renaming file for user '{user_sessions[message.chat.id]}': {str(e)}")
    else:
        bot.reply_to(message, f"❌ File '{old_file_name}' not found.")
        logging.warning(f"File '{old_file_name}' not found for user '{user_sessions[message.chat.id]}'.")


@bot.message_handler(commands=['delete'])
def handle_delete(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    text_split = message.text.split()
    if len(text_split) < 2:
        bot.reply_to(message, "❓ Please provide the file name after the /delete command.")
        return

    file_name = text_split[1]
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            bot.reply_to(message, f"✅ File '{file_name}' deleted successfully.")
            logging.info(f"User '{user_sessions[message.chat.id]}' deleted file '{file_name}'.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed to delete file: {str(e)}")
            logging.error(f"Error deleting file for user '{user_sessions[message.chat.id]}': {str(e)}")
    else:
        bot.reply_to(message, f"❌ File '{file_name}' not found.")
        logging.warning(f"File '{file_name}' not found for user '{user_sessions[message.chat.id]}'.")


@bot.message_handler(commands=['list'])
def handle_list(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    files = os.listdir(UPLOAD_DIR)
    if not files:
        bot.reply_to(message, "📁 No files uploaded yet.")
    else:
        file_list = "\n".join(files)
        bot.reply_to(message, f"📁 Uploaded files:\n{file_list}")
        logging.info(f"User '{user_sessions[message.chat.id]}' requested file list.")


@bot.message_handler(commands=['metadata'])
def handle_metadata(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    text_split = message.text.split()
    if len(text_split) < 2:
        bot.reply_to(message, "❓ Please provide a file name after the /metadata command.")
        return

    file_name = text_split[1]
    file_path = os.path.join(UPLOAD_DIR, file_name)

    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        file_creation_time = os.path.getctime(file_path)
        file_modification_time = os.path.getmtime(file_path)

        # Format the timestamps
        creation_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_creation_time))
        modification_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_modification_time))

        metadata_info = f"""
📄 File Metadata:
- Name: {file_name}
- Size: {file_size} bytes
- Created: {creation_time_str}
- Modified: {modification_time_str}
"""
        bot.reply_to(message, metadata_info)
        logging.info(f"User '{user_sessions[message.chat.id]}' requested metadata for file '{file_name}'.")
    else:
        bot.reply_to(message, f"❌ File '{file_name}' not found.")
        logging.warning(f"File '{file_name}' not found for user '{user_sessions[message.chat.id]}'.")
        

if __name__ == '__main__':
    load_dotenv()
    os.system('gunicorn -c gunicorn.conf keep_alive:app')

keep_alive()

# Start the bot
bot.polling()
