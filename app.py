import logging
import os
import sqlite3
import sys
from datetime import date
from logging.handlers import RotatingFileHandler

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

# Set up logger configuration
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

log_file = os.path.join(logs_dir, f'{date.today()}.log')

log_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s [%(module)s:%(lineno)d] %(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# Delete older log files
for filename in os.listdir(logs_dir):
    if filename.endswith('.log'):
        filepath = os.path.join(logs_dir, filename)
        if filepath != log_file:
            os.remove(filepath)


def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('calculator.db')

        # Define the table creation query
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS calculator_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT,
                num1 REAL,
                num2 REAL,
                result REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''

        # Create the table
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()

        return conn
    except sqlite3.Error as e:
        print(e)

    return conn


@app.route('/')
def home():
    logger.info('Home page accessed')
    return render_template('index.html')


@app.route('/calculate')
def calculate():
    num1 = request.args.get('num1')
    num2 = request.args.get('num2')
    operation = request.args.get('operation')

    logger.info(f'Calculate route accessed with operation: {operation}, num1: {num1}, num2: {num2}')

    url = f'http://localhost:8000/app3/{operation}/{num1}/{num2}/'
    response = requests.get(url)
    result = response.json()['result']

    logger.info(f'Result: {result}')

    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO calculator_logs (operation, num1, num2, result)
                VALUES (?, ?, ?, ?)
            ''', (operation, num1, num2, result))
            conn.commit()
        except sqlite3.Error as e:
            print(e)
        finally:
            conn.close()

    return render_template('result.html', result=result)


@app.route('/app1/')
def app1_view():
    response = requests.get('http://localhost:8000/app1/')
    return response.content


@app.route('/app1/second/')
def app1_second_view():
    response = requests.get('http://localhost:8000/app1/second/')
    return response.content


@app.route('/app2/')
def app2_view():
    response = requests.get('http://localhost:8000/app2/')
    return response.content


@app.route('/app2/second/')
def app2_second_view():
    response = requests.get('http://localhost:8000/app2/second/')
    return response.content


@app.errorhandler(requests.HTTPError)
def handle_http_error(error):
    error_code = error.response.status_code
    error_message = error.response.text

    logger.error(f'HTTP Error {error_code}: {error_message}')

    return f"HTTP Error {error_code}: {error_message}", error_code


if __name__ == '__main__':
    # Allow specifying a custom port at runtime, default to 5000
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000

    app.run(port=port, debug=True)
    print(f"Server started at port {port}")

# if __name__ == '__main__':
#     app.run(debug=True)