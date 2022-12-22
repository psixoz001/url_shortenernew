import sqlite3
from hashids import Hashids
from flask import Flask, render_template, request, flash, redirect, url_for, session
from modules.init_db import create_db
from modules.db_functions import *

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.config.from_object('modules.config')
hashids = Hashids(min_length=4, salt=app.config['SECRET_KEY'])

@app.route('/', methods=('GET', 'POST'))
def index():
    conn = get_db_connection()
    if request.method == 'POST':
        url = request.form['url']
        if not url:
            flash('The URL is required!')
            return redirect(url_for('index'))
        url_data = conn.execute('INSERT INTO urls (original_url) VALUES (?)', (url,))
        conn.commit()

        url_id = url_data.lastrowid
        hashid = hashids.encode(url_id)
        short_url = hashid
        update_url(conn, short_url, request.form['access'], session['user']['id'] if 'user' in session else 0, url)
        conn.close()
        return render_template('index.html', short_url=request.host_url + short_url, logged='user' in session)

    return render_template('index.html', logged='user' in session)

@app.route('/<short_url>')
def url_redirect(short_url):
    conn = get_db_connection()

    url = full_url(conn, short_url)
    url_original = url['original_url']
    url_access = url['access']
    url_user_id = url['user_id']

    update_clicks(conn, short_url)

    conn.close()
    if url_access == 0:
        return redirect(url_original)
    elif url_access == 1:
        if 'user' in session:
            return redirect(url_original)
        else:
            return redirect(url_for('signin'))
    else:
        if 'user' in session and session['user']['id'] == url_user_id:
            return redirect(url_original)
        else:
            flash('Это приватная ссылка')
            return redirect(url_for('index'))

@app.route('/stats')
def stats():
    conn = get_db_connection()
    db_urls = all_urls (conn, session['user']['id'],)
    conn.close()

    urls = []
    for url in db_urls:
        url = dict(url)
        url['short_url'] = request.host_url + hashids.encode(url['id'])
        urls.append(url)

    return render_template('stats.html', logged='user' in session, urls=urls)

@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if 'user' in session:
        return redirect(url_for('stats'))
    if request.method == 'GET':
        return render_template('signup.html', logged='user' in session)
    else :
        conn = get_db_connection()
        if findUser(conn, request.form['email']):
            return redirect(url_for('signin'))
        else:
            reg(conn, request.form['email'], request.form['password'])
            flash('Успешная регистрация', category='success')
            return redirect(url_for('signin'))

@app.route('/signin', methods=('GET', 'POST'))
def signin():
    if 'user' in session:
        return redirect(url_for('stats'))
    if request.method == 'GET':
        return render_template('signin.html', logged='user' in session)
    else:
        conn = get_db_connection()
        if auth(conn, request.form['email'], request.form['password']):
            return redirect(url_for('stats'))
        else :
            flash('Неправильный пароль', category='warning')
            return redirect(url_for('signin'))

@app.route('/logout', methods=('GET', 'POST'))
def logout():
    session.pop('user')
    return redirect(url_for('index'))

if __name__ == '__main__':
    create_db(app.config['DATABASE'], app.config['DBSCRIPT'])
    app.run()


