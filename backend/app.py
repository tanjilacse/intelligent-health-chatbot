"""Main Flask application."""

from flask import Flask, render_template, session, redirect, url_for
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-secret-key')

# Register API routes
from backend.api.routes import api
app.register_blueprint(api, url_prefix='/api')

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session.get('username'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
