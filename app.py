from flask import Flask, render_template, request, g
import requests
import redis
import sqlite3

app = Flask(__name__)
r = redis.Redis(host='192.168.1.6', port=6379, db=0)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('database.db')
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        short_url = shorten_url(url)
        return render_template('index.html', short_url=short_url)
    return render_template('index.html')

def shorten_url(url):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT short_url FROM urls WHERE original_url = ?', (url,))
    result = cursor.fetchone()
    if result:
        short_url = result[0]
    else:
        response = requests.get(f'https://is.gd/create.php?format=json&url={url}')
        if response.status_code == 200:
            json_response = response.json()
            if 'errorcode' in json_response:
                return None
            if 'shorturl' in json_response:
                short_url = json_response['shorturl']
                cursor.execute('INSERT INTO urls (original_url, short_url) VALUES (?, ?)', (url, short_url))
                conn.commit()
    cursor.close()
    return short_url

if __name__ == '__main__':
    app.run(debug=True)
