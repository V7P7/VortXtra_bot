from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return "I'm Alive!"  # More informative message

def keep_alive():
    """Starts a background thread to run the Flask app."""
    thread = Thread(target=run)
    thread.daemon = True  # Ensures thread exits with main program
    thread.start()

def run():
    """Runs the Flask app in a separate thread."""
    app.run(host='0.0.0.0', port=8080)  # Expose app externally

if __name__ == '__main__':
    keep_alive()  # Start keep-alive thread before any logic