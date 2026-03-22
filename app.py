from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Create database and table
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT
    )
    ''')
    cursor.execute('''
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT,
    date TEXT,
    mood TEXT
)
''')

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # SAVE DATA INTO DATABASE
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                       (name, email, password))

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()

        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect('/dashboard')
        else:
            return "Invalid Email or Password!"

    return render_template('login.html')

@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        mood = request.form['mood']
        date = datetime.now().strftime("%d-%m-%Y %H:%M")

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO entries (user_id, title, content, date, mood) VALUES (?, ?, ?, ?, ?)",
                       (session['user_id'], title, content, date, mood))

        conn.commit()
        conn.close()

        return "Entry Saved Successfully!"

    return render_template('add_entry.html')

@app.route('/view')
def view_entries():
    search_date = request.args.get('search_date')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if search_date:
        cursor.execute("SELECT * FROM entries WHERE user_id = ? AND date LIKE ?", (session['user_id'], '%' + search_date + '%')).fetchall()
    else:
        cursor.execute("SELECT * FROM entries WHERE user_id=?", (session['user_id'],)).fetchall()

    entries = cursor.execute("SELECT * FROM entries WHERE user_id = ?", (session['user_id'],)).fetchall()

    # 🔥 Mood count logic
    mood_count = {
        "Happy": 0,
        "Sad": 0,
        "Angry": 0,
        "Excited": 0,
        "Normal": 0
    }

    for entry in entries:
        mood = entry[4]
        if mood in mood_count:
            mood_count[mood] += 1

    conn.close()

    return render_template('view_entries.html', entries=entries, mood_count=mood_count)

@app.route('/delete/<int:id>')
def delete_entry(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM entries WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return "Entry Deleted Successfully!"

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_entry(id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        cursor.execute("UPDATE entries SET title=?, content=? WHERE id=?",
                       (title, content, id))

        conn.commit()
        conn.close()

        return "Entry Updated Successfully!"

    cursor.execute("SELECT * FROM entries WHERE id=?", (id,))
    entry = cursor.fetchone()
    conn.close()

    return render_template('edit_entry.html', entry=entry)

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
