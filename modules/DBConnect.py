import hashlib
import random
import sqlite3 as sql

from flask import session
from werkzeug.security import generate_password_hash, check_password_hash


class DBConnect:
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        with sql.connect(self.db_path) as db:
            db.row_factory = sql.Row
            return db

    def findUser(self, email):
        db = self.connect()
        return db.cursor().execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()

    def register_user(self, email, password):
        if not self.findUser(email):
            password = generate_password_hash(password)
            db = self.connect()
            db.cursor().execute('INSERT INTO users (email,password) VALUES(?,?)', (email, password))
            db.commit()
            return True
        return False

    def login(self, email, password):
        user = self.find_user(email)
        if user:
            if check_password_hash(user['password'], password):
                session['user'] = {'id': user['id'], 'email': user['email']}
                return True
            return False
        return False

    def new_link(self, source_link, access_level, user_id=0):
        while True:
            generated_link = self.hash_link(source_link)
            if self.link_unique(generated_link):
                db = self.connect()
                db.cursor().execute(
                    'INSERT INTO links (source_link, shortened_link, access_level, visit_counter, user_created_id) '
                    'VALUES (?, ?, ?, ?, ?)',
                    (source_link, generated_link, access_level, 0, user_id if user_id > 0 else 'NULL'))
                db.commit()
                return generated_link

    def last_link_id(self):
        db = self.connect()
        return db.cursor().execute('SELECT MAX id FROM links').fetchone()['id']

    def hash_link(self, link):
        return hashlib.md5(link.encode()).hexdigest()[:random.randint(8, 12)]

    def link_unique(self, hash_link):
        return not self.connect().cursor().execute('SELECT id from links where shortened_link=?',
                                                   (hash_link,)).fetchone()

    def increment_visit_counter(self, link_id):
        db = self.connect()
        db.cursor().execute('UPDATE links set visit_counter = visit_counter + 1 where id=?', (link_id,))
        db.commit()

    def get_source_link(self, short_link):
        link_obj = self.connect().cursor().execute('SELECT * from links where shortened_link=?',
                                                   (short_link,)).fetchone()
        self.increment_visit_counter(link_obj['id'])
        return link_obj

    def get_user_links(self, user_id):
        return self.connect().cursor().execute('SELECT * from links where user_created_id=?', (user_id,)).fetchall()