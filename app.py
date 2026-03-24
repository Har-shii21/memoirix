from flask import Flask, render_template, request, redirect, session
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Create database and table
def init_db():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY ,
        username TEXT,
        email TEXT,
        password TEXT
    )
    """)
    cursor.execute("""
CREATE TABLE IF NOT EXISTS entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    title TEXT,
    content TEXT,
    date TEXT,
    mood TEXT
)
""")

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # SAVE DATA INTO DATABASE
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()

        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username.strip(), email.strip(), password.strip()))

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()

        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect('/dashboard')
        else:
            return "Invalid Email or Password!"

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')

@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        mood = request.form['mood']
        date = datetime.now().strftime("%d-%m-%Y %H:%M")

        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        cursor = conn.cursor()

        cursor.execute("INSERT INTO entries (user_id, title, content, date, mood) VALUES (%s, %s, %s, %s, %s)",
                       (session.get('user_id'), title, content, date, mood))

        conn.commit()
        conn.close()

        return "Entry Saved Successfully!"

    return render_template('add_entry.html')

@app.route('/view')
def view_entries():
    search_date = request.args.get('search_date')

    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()

    if search_date:
        cursor.execute("SELECT * FROM entries WHERE user_id = %s AND date LIKE %s", (session.get('user_id'), '%' + search_date + '%'))
    else:
        cursor.execute("SELECT * FROM entries WHERE user_id = %s", (session.get('user_id'),))

    entries = cursor.execute("SELECT * FROM entries WHERE user_id = %s", (session.get('user_id'),)).fetchall()

    # 🔥 Mood count logic
    mood_count = {
        "Happy": 0,
        "Sad": 0,
        "Angry": 0,
        "Excited": 0,
        "Normal": 0
    }

    for entry in entries:
        mood = entry[5]
        mood_count[mood] = mood_count.get(mood, 0) + 1

    conn.close()

    return render_template('view_entries.html', entries=entries, mood_count=mood_count)

@app.route('/delete/<int:id>')
def delete_entry(id):
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()

    cursor.execute("DELETE FROM entries WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    return "Entry Deleted Successfully!"

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_entry(id):
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        cursor.execute("UPDATE entries SET title=%s, content=%s WHERE id=%s",
                       (title, content, id))

        conn.commit()
        conn.close()

        return "Entry Updated Successfully!"

    cursor.execute("SELECT * FROM entries WHERE id=%s", (id,))
    entry = cursor.fetchone()
    conn.close()

    return render_template('edit_entry.html', entry=entry)

