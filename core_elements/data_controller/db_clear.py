import os

from peewee import *


def create_database(db_filename):

    if os.path.exists(db_filename):
        os.remove(db_filename)

    conn = SqliteDatabase(db_filename)
    curs = conn.cursor()

    curs.execute("""
        CREATE TABLE user (
            id INTEGER NOT NULL,
            balance INTEGER,
            experience INTEGER,
            voice_activity INTEGER,
            biography TEXT,
            mute_end_at INTEGER,
            warn INTEGER,
            on_server BOOLEAN NOT NULL,
            PRIMARY KEY (id AUTOINCREMENT),
            CHECK (balance >= 0)
        );
        """)

    curs.execute("""
        CREATE TABLE user_roles (
            id INTEGER NOT NULL,
            user INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            PRIMARY KEY (id AUTOINCREMENT),
            FOREIGN KEY (user)
                REFERENCES user (id)
        );
        """)

    curs.execute("""
        CREATE TABLE likes (
            id INTEGER NOT NULL,
            user INTEGER NOT NULL,
            to_user INTEGER NOT NULL,
            type INTEGER,
            PRIMARY KEY (id)
        );
        """)

    curs.execute("""
        CREATE TABLE relationship (
            id INTEGER NOT NULL,
            user INTEGER NOT NULL,
            soul_mate INTEGER NOT NULL,
            married_time INTEGER,
            PRIMARY KEY (id),
            FOREIGN KEY (user)
                REFERENCES user (id),
            FOREIGN KEY (soul_mate)
                REFERENCES user (id)
        );
        """)

    curs.execute("""
        CREATE TABLE user_personal_voice (
            id INTEGER NOT NULL,
            user INTEGER NOT NULL,
            voice_id INTEGER NOT NULL,
            slots INTEGER NOT NULL,
            max_bitrate INTEGER NOT NULL,
            PRIMARY KEY (id AUTOINCREMENT),
            FOREIGN KEY (user)
                REFERENCES user (id)
        );
        """)

    curs.execute("""
        CREATE TABLE mod_log (
            id INTEGER NOT NULL,
            moderator INTEGER,
            action TEXT,
            reason TEXT,
            duration INT,
            creation_time INTEGER, 
            PRIMARY KEY (id AUTOINCREMENT)
        );
        """)

    curs.execute("""
        CREATE TABLE mod_log_target (
            id INTEGER NOT NULL,
            mod_log INTEGER,
            target INTEGER,
            PRIMARY KEY (id AUTOINCREMENT),
            FOREIGN KEY (mod_log)
                REFERENCES mod_log (id)
        );
        """)

    curs.execute("""
        CREATE TABLE shop_roles (
            id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            price INTEGER NOT NULL,
            PRIMARY KEY (id AUTOINCREMENT)
        );
        """)

    curs.execute("""
        CREATE TABLE suggestions (
            message_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            url TEXT,
            author INTEGER NOT NULL,
            PRIMARY KEY (message_id)
        );
        """)

    conn.commit()
    conn.close()