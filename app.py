
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DB_PATH = "veikkaukset.db"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$nTHkUhIFqajKwpgC$5f2f69bad7406472ea6961a3ac39789a704811f73f54841bcc94ea447a72fb7c7df50da96d43f06b77d530d87ef63477f0ac55dc6d3c35bddffe835f261d2998"

def init_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE veikkaukset (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    game_FIN_CAN TEXT,
                    game_SWE_USA TEXT,
                    quarter_finals TEXT,
                    semi_finals TEXT,
                    medalists TEXT,
                    relegated TEXT,
                    top_scorer TEXT,
                    first_goal_fi TEXT,
                    last_goal_fi TEXT,
                    first_penalty_reason TEXT,
                    top_fi_scorer TEXT,
                    points INTEGER DEFAULT 0
                )
            ''')
            c.execute('''
                CREATE TABLE results (
                    game_FIN_CAN TEXT,
                    game_SWE_USA TEXT
                )
            ''')
            c.execute("INSERT INTO results (game_FIN_CAN, game_SWE_USA) VALUES (?, ?)", ("", ""))
            conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = (
        request.form.get("name"),
        request.form.get("game_FIN_CAN"),
        request.form.get("game_SWE_USA"),
        request.form.get("quarter_finals"),
        request.form.get("semi_finals"),
        request.form.get("medalists"),
        request.form.get("relegated"),
        request.form.get("top_scorer"),
        request.form.get("first_goal_fi"),
        request.form.get("last_goal_fi"),
        request.form.get("first_penalty_reason"),
        request.form.get("top_fi_scorer")
    )
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO veikkaukset (
                name, game_FIN_CAN, game_SWE_USA, quarter_finals, semi_finals,
                medalists, relegated, top_scorer, first_goal_fi,
                last_goal_fi, first_penalty_reason, top_fi_scorer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
    return render_template('thankyou.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin'] = True
            return redirect('/admin')
        else:
            error = "Väärä käyttäjätunnus tai salasana"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'):
        return redirect('/login')

    message = ""
    if request.method == 'POST':
        result_FIN_CAN = request.form.get('result_FIN_CAN')
        result_SWE_USA = request.form.get('result_SWE_USA')
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("UPDATE results SET game_FIN_CAN=?, game_SWE_USA=?", (result_FIN_CAN, result_SWE_USA))
            conn.commit()
            message = "Tulokset päivitetty"

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM results")
        results = c.fetchone()
    return render_template('admin.html', results=results, message=message)

@app.route('/score')
def score():
    if not session.get('admin'):
        return redirect('/login')

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM results")
        results = c.fetchone()
        c.execute("SELECT * FROM veikkaukset")
        veikkaajat = c.fetchall()
        for v in veikkaajat:
            points = 0
            if v[2] == results[0]: points += 1
            if v[3] == results[1]: points += 1
            c.execute("UPDATE veikkaukset SET points=? WHERE id=?", (points, v[0]))
        conn.commit()
    return redirect('/results')

@app.route('/results')
def results():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT name, points FROM veikkaukset ORDER BY points DESC")
        data = c.fetchall()
    return render_template('results.html', data=data)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
