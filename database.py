# database.py (вставьте сюда код из предыдущего сообщения)
import pysqlite3 as sqlite3
import logging

DB_NAME = 'bot_database.db'


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            question TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            answer TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_admin_responses (
            admin_id INTEGER PRIMARY KEY,
            question_id INTEGER NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    logging.info("База данных инициализирована")


def add_question(user_id: int, username: str, first_name: str, question: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO questions (user_id, username, first_name, question) 
        VALUES (?, ?, ?, ?)''',
        (user_id, username or None, first_name, question
         )  # username может быть None
    )
    conn.commit()
    question_id = cursor.lastrowid
    conn.close()
    return question_id


def get_pending_questions():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, user_id, question FROM questions WHERE status = "pending"')
    questions = cursor.fetchall()
    conn.close()
    return questions


def get_question_by_id(question_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, user_id, username, first_name, question 
        FROM questions WHERE id = ?''', (question_id, ))
    question = cursor.fetchone()
    conn.close()
    return question


def save_admin_pending_response(admin_id: int, question_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'REPLACE INTO pending_admin_responses (admin_id, question_id) VALUES (?, ?)',
        (admin_id, question_id))
    conn.commit()
    conn.close()


def get_admin_pending_response(admin_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT question_id FROM pending_admin_responses WHERE admin_id = ?',
        (admin_id, ))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def clear_admin_pending_response(admin_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM pending_admin_responses WHERE admin_id = ?',
                   (admin_id, ))
    conn.commit()
    conn.close()


def save_answer(question_id: int, answer: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE questions SET answer = ?, status = "answered" WHERE id = ?',
        (answer, question_id))
    conn.commit()
    conn.close()


def get_user_data(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT user_id, username, first_name 
        FROM questions 
        WHERE user_id = ? 
        ORDER BY id DESC 
        LIMIT 1''', (user_id, ))
    data = cursor.fetchone()
    conn.close()
    return data
