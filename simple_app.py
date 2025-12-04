from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_strong_secret_key_here'

# Database helper
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    location TEXT
                )''')
        c.execute('''CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
        c.execute('''CREATE TABLE IF NOT EXISTS govs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
        c.execute('''CREATE TABLE IF NOT EXISTS disaster_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    severity TEXT,
                    affected_areas TEXT,
                    timeframe TEXT,
                    advisory TEXT,
                    reported_by TEXT,
                    created_at TEXT
                )''')
        try:
            c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", 
                     ('admin', generate_password_hash('admin123')))
        except sqlite3.IntegrityError:
            pass
        try:
            c.execute("INSERT INTO govs (username, password) VALUES (?, ?)",
                      ('govuser', generate_password_hash('govpass123')))
        except sqlite3.IntegrityError:
            pass
        conn.commit()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        location = request.form.get('location')
        if not email or not location:
            flash("Both email and location are required!", "error")
            return redirect(url_for('register'))
        try:
            with get_db() as conn:
                conn.execute("INSERT INTO users (email, location) VALUES (?, ?)", (email, location))
                conn.commit()
            session['user_email'] = email
            flash("Registration successful! You'll now receive alerts.", "success")
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            flash("This email is already registered!", "error")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash("Email is required to login.", "error")
            return redirect(url_for('login'))
        with get_db() as conn:
            user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if user:
            session['user_email'] = email
            flash("Logged in successfully.", "success")
            return redirect(url_for('home'))
        else:
            flash("This email is not registered. Please register first.", "error")
            return redirect(url_for('register'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('home'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with get_db() as conn:
            admin = conn.execute("SELECT password FROM admins WHERE username = ?", (username,)).fetchone()
        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid credentials!")
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    with get_db() as conn:
        users = conn.execute("SELECT id, email, location FROM users ORDER BY email").fetchall()
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

@app.route('/gov/login', methods=['GET', 'POST'])
def gov_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        with get_db() as conn:
            gov = conn.execute("SELECT * FROM govs WHERE username = ?", (username,)).fetchone()
        if gov and check_password_hash(gov['password'], password):
            session['gov_logged_in'] = True
            session['gov_username'] = username
            next_url = request.args.get('next') or url_for('gov_report_form')
            return redirect(next_url)
        else:
            return render_template('gov_login.html', error="Invalid government credentials!")
    return render_template('gov_login.html')

@app.route('/gov/report', methods=['GET', 'POST'])
def gov_report_form():
    if not session.get('gov_logged_in'):
        return redirect(url_for('gov_login', next=url_for('gov_report_form')))
    if request.method == 'POST':
        title = request.form.get('title')
        severity = request.form.get('severity') or 'LOW'
        affected_areas = request.form.get('affected_areas')
        timeframe = request.form.get('timeframe')
        advisory = request.form.get('advisory')
        reported_by = session.get('gov_username', 'gov')
        created_at = datetime.utcnow().isoformat()

        if not title or not affected_areas or not advisory:
            flash("Please fill required fields (title, affected areas, advisory).", "error")
            return render_template('report_disaster.html')

        with get_db() as conn:
            conn.execute("""INSERT INTO disaster_reports
                            (title, severity, affected_areas, timeframe, advisory, reported_by, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)""",
                         (title, severity, affected_areas, timeframe, advisory, reported_by, created_at))
            conn.commit()

        flash("Report added successfully!", "success")
        return redirect(url_for('home'))
    return render_template('report_disaster.html')

# Static pages
@app.route('/about')
def about():
    return render_template('aboutus.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/donation')
def donation():
    return render_template('donation.html')

@app.route('/emergency')
def emergency():
    return render_template('emergency.html')

@app.route('/firstaid')
def firstaid():
    return render_template('firstaid.html')

@app.route('/missing')
def missing():
    return render_template('missing.html')

@app.route('/protection')
def protection():
    return render_template('protecthome.html')

@app.route('/routes')
def routes():
    return render_template('routes.html')

@app.route('/user')
def user():
    with get_db() as conn:
        alerts = conn.execute("SELECT * FROM disaster_reports ORDER BY created_at DESC").fetchall()
    return render_template('user.html', alerts=alerts)

if __name__ == '__main__':
    print("🚀 Starting Simple Disaster Management System...")
    print("✅ Server running at: http://localhost:5000")
    print("📋 Default credentials:")
    print("   Admin: admin / admin123")
    print("   Government: govuser / govpass123")
    app.run(debug=True, port=5000)