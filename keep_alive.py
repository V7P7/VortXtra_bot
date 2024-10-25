from threading import Thread
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
from flask_session import Session
from datetime import datetime
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename  # Import secure_filename

load_dotenv()

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))
app.secret_key = os.urandom(24)  # Set a secret key for session management
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Load credentials from environment variables
USERNAME = os.getenv('user')
PASSWORD = os.getenv('password')

UPLOAD_FOLDER = 'uploads'  # Change this to your uploads directory

def is_logged_in():
    return 'logged_in' in session

@app.route('/')
def index():
    if not is_logged_in():
        flash('Please log in to access the file management system.', 'warning')
        return redirect(url_for('login'))
    
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', files=files)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Clear the session
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if not is_logged_in():
        flash('Please log in to upload files.', 'warning')
        return redirect(url_for('login'))
    
    file = request.files['file']
    if file:
        file.save(os.path.join(UPLOAD_FOLDER, secure_filename(file.filename)))
        flash('File uploaded successfully!', 'success')
    else:
        flash('No file selected for upload.', 'danger')
    return redirect(url_for('index'))

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    if not is_logged_in():
        flash('Please log in to download files.', 'warning')
        return redirect(url_for('login'))
    
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/rename', methods=['POST'])
def rename_file():
    if not is_logged_in():
        flash('Please log in to rename files.', 'warning')
        return redirect(url_for('login'))
    
    old_name = request.form['old_name']
    new_name = request.form['new_name']
    os.rename(os.path.join(UPLOAD_FOLDER, old_name), os.path.join(UPLOAD_FOLDER, new_name))
    flash(f'Renamed {old_name} to {new_name} successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_file():
    if not is_logged_in():
        flash('Please log in to delete files.', 'warning')
        return redirect(url_for('login'))
    
    filename = request.form['filename']
    os.remove(os.path.join(UPLOAD_FOLDER, filename))
    flash(f'Deleted {filename} successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/metadata/<filename>', methods=['GET'])
def metadata_file(filename):
    if not is_logged_in():
        flash('Please log in to view file metadata.', 'warning')
        return redirect(url_for('login'))

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if os.path.exists(file_path):
        # Get file metadata
        metadata = {
            'size': os.path.getsize(file_path),
            'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
            'created': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        }
        return render_template('metadata.html', filename=filename, metadata=metadata)
    else:
        flash('File not found', 'danger')
        return redirect(url_for('index'))

def keep_alive():
    """Starts a background thread to run the Flask app."""
    thread = Thread(target=run)
    thread.daemon = True
    thread.start()

def run():
    """Runs the Flask app in a separate thread."""
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    keep_alive()
