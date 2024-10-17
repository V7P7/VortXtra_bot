import os
import logging
from dotenv import load_dotenv
import telebot
import shutil
import psutil
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

UPLOAD_LIMIT_GB = 1  # 1 GB limit for the uploads directory

def get_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def get_storage_info():
    # Get disk usage for the current directory
    current_directory = os.getcwd()
    disk_usage = psutil.disk_usage(current_directory)

    # Calculate total, used, and free space in GB for the partition
    total = disk_usage.total / (1024 ** 3)  # Convert to GB
    used = disk_usage.used / (1024 ** 3)    # Convert to GB
    free = disk_usage.free / (1024 ** 3)    # Convert to GB

    return total, used, free, current_directory

@bot.message_handler(commands=['storage'])
def send_storage_info(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    # Get disk storage info
    total, used, free, current_directory = get_storage_info()

    # Calculate the size of files in the uploads directory
    uploads_size_bytes = get_directory_size(UPLOAD_DIR)
    uploads_size_gb = uploads_size_bytes / (1024 ** 3)  # Convert to GB

    # Get the remaining space in the uploads directory
    remaining_upload_space_gb = UPLOAD_LIMIT_GB - uploads_size_gb

    # Format the storage information message
    storage_message = f"""
💾 Storage Information:
- Directory: {current_directory}
- Total Disk Space: {total:.2f} GB
- Used Disk Space: {used:.2f} GB
- Free Disk Space: {free:.2f} GB

🗂️ Uploads Directory:
- Uploads Size: {uploads_size_gb:.2f} GB
- Remaining Upload Space: {remaining_upload_space_gb:.2f} GB (out of {UPLOAD_LIMIT_GB} GB)
"""

    bot.reply_to(message, storage_message)
    logging.info(f"User '{user_sessions[message.chat.id]}' requested storage information.")

# Create a directory to store uploaded files
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

user_sessions = {}

user_sessions.clear()

def main_menu():
    markup = telebot.types.InlineKeyboardMarkup()

    # Adding buttons for the various features
    login_button = telebot.types.InlineKeyboardButton(text='Login', callback_data='suggest_login')
    upload_button = telebot.types.InlineKeyboardButton(text='Upload', callback_data='suggest_upload')
    list_files_button = telebot.types.InlineKeyboardButton(text='List Files', callback_data='suggest_list_files')
    download_button = telebot.types.InlineKeyboardButton(text='Download', callback_data='suggest_download')
    rename_button = telebot.types.InlineKeyboardButton(text='Rename', callback_data='suggest_rename')
    delete_button = telebot.types.InlineKeyboardButton(text='Delete', callback_data='suggest_delete')
    metadata_button = telebot.types.InlineKeyboardButton(text='Metadata', callback_data='suggest_metadata')
    storage_button = telebot.types.InlineKeyboardButton(text='Storage Check', callback_data='suggest_storage')
    logout_button = telebot.types.InlineKeyboardButton(text='Logout', callback_data='suggest_logout')

    # Organize buttons into rows
    markup.row(login_button, logout_button, list_files_button)
    markup.row(upload_button, download_button, storage_button)
    markup.row(metadata_button, rename_button, delete_button)

    return markup


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, """
👋 Welcome to the bot! Here are the available commands:

- /login <username> <password> - Log in to your account.
- /upload - Upload a file.
- /list - See your uploaded files.
- /download <file_name> - Download a file.
- /rename <old_name> <new_name> - Rename a file.
- /delete <file_name> - Delete a file.
- /logout - Log out from your account.
- /metadata <file_name> - Get metadata of a file.
- /storage - Check how much storage is left.

Use the menu below:
""", reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    # Define responses for each button click
    suggestions = {
        "suggest_login": "Please use the command: /login <username> <password>",
        "suggest_upload": "Please use the command: /upload to attach a file.",
        "suggest_list_files": "Please use the command: /list to see your files.",
        "suggest_download": "Please use the command: /download <file_name>",
        "suggest_rename": "Please use the command: /rename <old_name> <new_name>",
        "suggest_delete": "Please use the command: /delete <file_name>",
        "suggest_logout": "You can logout using: /logout",
        "suggest_metadata": "Please use the command: /metadata <file_name> to get file metadata.",
        "suggest_storage": "Please use the command: /storage to check available storage."
    }

    # Get the appropriate response based on the button clicked
    suggestion_message = suggestions.get(call.data, "❓ Command not found.")

    # Send the response message to the user
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
        ),
        telebot.types.InlineQueryResultArticle(
            id='8',
            title='Metadata',
            input_message_content=telebot.types.InputTextMessageContent('/metadata <file_name>'),
            description='Get file metadata.'
        ),
        telebot.types.InlineQueryResultArticle(
            id='9',
            title='Storage Check',
            input_message_content=telebot.types.InputTextMessageContent('/storage'),
            description='Check how much storage is left.'
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
    last_command_time = user_command_time.get(message.chat.id, 0) # type: ignore

    if current_time - last_command_time < 5:
        bot.reply_to(message, "⏳ Please wait before using the command again.")
        return

    user_command_time[message.chat.id] = current_time # type: ignore
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


@bot.message_handler(commands=['download'])
def handle_download(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    text_split = message.text.split()
    if len(text_split) < 2:
        bot.reply_to(message, "❓ Please provide file indices after the /download command (e.g., /download 1 2).")
        return

    file_indices = [int(i) - 1 for i in text_split[1:] if i.isdigit()]
    files = os.listdir(UPLOAD_DIR)
    too_large_files = []
    downloaded_files = []
    not_found_files = []

    for index in file_indices:
        if 0 <= index < len(files):  # Validate index
            file_name = files[index]
            file_path = os.path.join(UPLOAD_DIR, file_name)
            if os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    max_file_size = 50 * 1024 * 1024  # 50 MB limit for Telegram uploads

                    if file_size > max_file_size:
                        too_large_files.append(file_name)
                        logging.warning(f"File '{file_name}' is too large to upload for user '{user_sessions[message.chat.id]}'.")
                    else:
                        with open(file_path, 'rb') as f:
                            bot.send_document(message.chat.id, f, timeout=180)  # Increase timeout for larger files
                            downloaded_files.append(file_name)
                            logging.info(f"User '{user_sessions[message.chat.id]}' downloaded file '{file_name}'.")
                except requests.exceptions.Timeout:
                    bot.reply_to(message, f"⏳ The download request for '{file_name}' timed out. Please try again.")
                except requests.exceptions.ConnectionError as e:
                    bot.reply_to(message, f"❌ Connection error while downloading '{file_name}': {str(e)}. Please try again later.")
                except Exception as e:
                    bot.reply_to(message, f"❌ An unexpected error occurred while downloading '{file_name}': {str(e)}.")
                    logging.error(f"Error downloading file '{file_name}': {str(e)}")
            else:
                not_found_files.append(file_name)
        else:
            not_found_files.append(str(index + 1))

    # Response messages
    if downloaded_files:
        bot.reply_to(message, f"✅ Successfully downloaded files:\n- {', '.join(downloaded_files)}.")
    if too_large_files:
        bot.reply_to(message, f"❌ Files too large to download: {', '.join(too_large_files)}.")
    if not_found_files:
        bot.reply_to(message, f"❌ Invalid indices or files not found: {', '.join(not_found_files)}.")


@bot.message_handler(commands=['rename'])
def handle_rename(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    text_split = message.text.split()
    if len(text_split) < 3 or not text_split[1].isdigit():
        bot.reply_to(message, "❓ Please provide a file index and the new file name after the /rename command.")
        return

    file_index = int(text_split[1]) - 1  # Convert to zero-based index
    new_file_name = text_split[2]
    files = os.listdir(UPLOAD_DIR)

    if 0 <= file_index < len(files):  # Validate file index
        old_file_name = files[file_index]
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
    else:
        bot.reply_to(message, "❌ Invalid file index.")


@bot.message_handler(commands=['delete'])
def handle_delete(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    text_split = message.text.split()
    if len(text_split) < 2:
        bot.reply_to(message, "❓ Please provide file indices after the /delete command (e.g., /delete 1 3 5).")
        return

    file_indices = [int(i) - 1 for i in text_split[1:] if i.isdigit()]
    files = os.listdir(UPLOAD_DIR)
    deleted_files = []
    not_found_files = []

    for index in file_indices:
        if 0 <= index < len(files):  # Check if index is valid
            file_name = files[index]
            file_path = os.path.join(UPLOAD_DIR, file_name)
            try:
                os.remove(file_path)
                deleted_files.append(file_name)
                logging.info(f"User '{user_sessions[message.chat.id]}' deleted file '{file_name}'.")
            except Exception as e:
                bot.reply_to(message, f"❌ Failed to delete file '{file_name}': {str(e)}")
                logging.error(f"Error deleting file for user '{user_sessions[message.chat.id]}': {str(e)}")
        else:
            not_found_files.append(str(index + 1))

    # Response messages
    if deleted_files:
        bot.reply_to(message, f"✅ Successfully deleted files:\n- {', '.join(deleted_files)}.")
    if not_found_files:
        bot.reply_to(message, f"❌ Invalid indices: {', '.join(not_found_files)}.")


@bot.message_handler(commands=['list'])
def handle_list(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    files = os.listdir(UPLOAD_DIR)
    if not files:
        bot.reply_to(message, "📁 No files uploaded yet.")
    else:
        file_list = "\n".join([f"{i + 1}. {file}" for i, file in enumerate(files)])  # Add index
        bot.reply_to(message, f"📁 Uploaded files:\n{file_list}")
        logging.info(f"User '{user_sessions[message.chat.id]}' requested file list.")


@bot.message_handler(commands=['metadata'])
def handle_metadata(message):
    if not is_authenticated(message):
        bot.reply_to(message, "❌ You need to log in first. Please use the /login command.")
        return

    text_split = message.text.split()
    if len(text_split) < 2 or not text_split[1].isdigit():
        bot.reply_to(message, "❓ Please provide a valid file index after the /metadata command.")
        return

    file_index = int(text_split[1]) - 1  # Convert to zero-based index
    files = os.listdir(UPLOAD_DIR)

    if 0 <= file_index < len(files):  # Validate file index
        file_name = files[file_index]
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
    else:
        bot.reply_to(message, "❌ Invalid file index.")
     

keep_alive()

# Start the bot
bot.polling()
