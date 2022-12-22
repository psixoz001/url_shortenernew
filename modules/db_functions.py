from flask import session
from werkzeug.security import generate_password_hash, check_password_hash


def findUser(conn, email):
    return conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()

def reg(conn, email, password):
    password = generate_password_hash(password)
    conn.execute('INSERT INTO users (email,password) VALUES(?,?)', (email, password))
    conn.commit()

def auth(conn, email, password):
    user = findUser(conn, email)
    if user:
        if check_password_hash(user['password'], password):
            session['user'] = {'id': user['id'], 'email': user['email']}
            return True
        return False
    return False

def update_url(conn, short_url, access, user_id, url):
    conn.execute('UPDATE urls SET short_url = ?, access = ?, user_id = ? WHERE original_url = ?', (short_url, access, user_id, url,))
    conn.commit()

def update_clicks(conn, short_url):
    conn.execute('UPDATE urls SET clicks = clicks+1 WHERE short_url = ?', (short_url,))
    conn.commit()

def insert_url(conn, url):
    conn.execute('INSERT INTO urls (original_url) VALUES (?)', (url,))
    conn.commit()

def all_urls(conn, user_id):
    return conn.execute('SELECT id, created, original_url, clicks, user_id FROM urls WHERE user_id = ?', (user_id,)).fetchall()

def full_url(conn, short_url):
    return conn.execute('SELECT original_url, access, user_id FROM urls WHERE short_url=?', (short_url,)).fetchone()

