from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
from transformers import pipeline
from datetime import datetime
from typing import Dict, Any
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import requests
from models import (
    SOSRequest, SOSResponse, ChatRequest, ChatResponse, RumorCheckRequest, RumorCheckResponse,
    UserRegistration, UserLogin, AdminLogin, AdminAlert, MissingPersonReport, SightingReport,
    VolunteerRegistration, VolunteerRoleApplication, MissingPersonSearch, StatusUpdate,
    StandardResponse, ValidationErrorResponse, validate_request_data
)
from pydantic import ValidationError

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_strong_secret_key_here'  # Change this to a random string
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
db = SQLAlchemy(app)

# Initialize Groq API
groq_api_key = os.getenv('GROQ_API_KEY')
if not groq_api_key:
    print("Warning: GROQ_API_KEY not found in environment variables")

def call_groq_api(message):
    """Direct API call to Groq"""
    if not groq_api_key:
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "You are DisasterBot, an AI assistant specialized in disaster management and emergency preparedness. Help with emergency procedures, safety tips, evacuation plans, and disaster response. Keep responses concise and practical."
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"Groq API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return None


# -------------------------------------------------
# SQLAlchemy models for missing persons feature
# -------------------------------------------------

class MissingPerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    last_location = db.Column(db.String(255), nullable=False)
    last_seen_date = db.Column(db.Date)
    description = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    photo_path = db.Column(db.String(255))
    reporter_name = db.Column(db.String(120), nullable=False)
    reporter_contact = db.Column(db.String(120), nullable=False)
    reporter_relation = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, verified, found, deceased
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Sighting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    missing_person_id = db.Column(db.Integer, db.ForeignKey('missing_person.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=False)
    contact_info = db.Column(db.String(120), nullable=False)
    media_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    missing_person = db.relationship('MissingPerson', backref='sightings')


class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    skills = db.Column(db.Text)
    availability = db.Column(db.String(50), nullable=False)
    interests = db.Column(db.String(255))
    role_applied = db.Column(db.String(120))
    experience = db.Column(db.Text)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()

# -------------------------------------------------
# Pretrained fake-news classifier (Hugging Face)
# -------------------------------------------------
try:
    # Public RoBERTa model for fake-news detection
    rumor_classifier = pipeline(
        "text-classification",
        model="raima2001/Fake-News-Detection-Roberta",
        truncation=True
    )
except Exception as model_error:
    rumor_classifier = None
    print(f"[RumorClassifier] Failed to load model: {model_error}")

POSITIVE_LABELS = {'real', 'true', 'reliable', 'label_1'}
NEGATIVE_LABELS = {'fake', 'false', 'hoax', 'misleading', 'rumor', 'label_0'}


def analyze_rumor(message: str) -> Dict[str, Any]:
    """Run NLP model on rumor message and normalize the output."""
    if not rumor_classifier:
        return heuristic_classification(message)

    prediction = rumor_classifier(message, truncation=True)
    # pipeline returns list of dicts; we care about top result
    top = prediction[0] if isinstance(prediction, list) else prediction
    raw_label = str(top.get("label", "UNKNOWN"))
    score = float(top.get("score", 0))
    normalized = raw_label.lower()

    if normalized in POSITIVE_LABELS:
        classification = "Real" if score >= 0.55 else "Suspicious"
    elif normalized in NEGATIVE_LABELS:
        classification = "Fake" if score >= 0.55 else "Suspicious"
    else:
        classification = "Real" if score >= 0.75 else "Suspicious"

    advice_map = {
        "Real": "Looks credible. Still cross-check with official bulletins before acting.",
        "Suspicious": "Mixed signals. Share only after confirming with trusted authorities.",
        "Fake": "Likely misinformation. Do not forward it—report to local admins instead."
    }

    return {
        "classification": classification,
        "confidence": round(score * 100, 1),
        "raw_label": raw_label,
        "advice": advice_map[classification],
        "reasons": [
            f"Model label: {raw_label}",
            f"Confidence: {round(score * 100, 1)}%"
        ]
    }


def heuristic_classification(message: str) -> Dict[str, Any]:
    """Fallback heuristic when transformer model is unavailable."""
    lowered = message.lower()
    fake_signals = [
        "forward this to",
        "share this immediately",
        "free money",
        "relief camp closing",
        "pay to get aid",
        "army confirms via whatsapp",
        "unverified"
    ]
    real_signals = [
        "government",
        "official",
        "ndma",
        "imd",
        "who",
        "reliefweb",
        "press release",
        "echo daily flash",
        "un ocha",
        "ministry"
    ]

    fake_hits = sum(1 for token in fake_signals if token in lowered)
    real_hits = sum(1 for token in real_signals if token in lowered)
    length = len(message.split())

    if fake_hits >= 2 and real_hits == 0:
        classification = "Fake"
        confidence = 68 + fake_hits * 5
        advice = "Strong misinformation cues detected. Treat as fake and do not share."
    elif real_hits >= 2 and fake_hits == 0 and length > 25:
        classification = "Real"
        confidence = 60 + real_hits * 6
        advice = "Contains multiple credible authority cues. Still verify with official alerts."
    else:
        classification = "Suspicious"
        confidence = 45 + (real_hits - fake_hits) * 4
        advice = "Mixed credibility signals. Cross-check with official bulletins before sharing."

    confidence = max(10, min(confidence, 95))

    return {
        "classification": classification,
        "confidence": round(confidence, 1),
        "raw_label": "HEURISTIC_ENGINE",
        "advice": advice,
        "reasons": [
            f"Heuristic fallback active (model unavailable).",
            f"Authority cues: {real_hits}",
            f"Misinformation cues: {fake_hits}"
        ]
    }
# Database setup
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
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
        c.execute('''CREATE TABLE IF NOT EXISTS sos_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    latitude REAL,
                    longitude REAL,
                    address TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )''')
        try:
            c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", 
                     ('admin', generate_password_hash('admin123')))
        except sqlite3.IntegrityError:
            pass
        conn.commit()

init_db()

# Email configuration 
EMAIL_CONFIG = {
    'sender_email': "nayamatemeet@gmail.com",
    'sender_password': "tjoy glyv olws wdxv",
    'smtp_server': "smtp.gmail.com",
    'smtp_port': 465,
    'use_ssl': True
}

# Admin email for SOS alerts
ADMIN_EMAIL = "nayamatemeet@gmail.com"  

def send_alert_email(to_email, location, alert_message):
    """Send emergency alert email to a user"""
    subject = f"🚨 Emergency Alert for {location} 🚨"
    body = f"""
    Emergency Alert Notification
    
    Location: {location}
    Message: {alert_message}
    
    Please take necessary precautions and follow local authorities' instructions.
    
    Stay safe,
    Disaster Management Team
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_CONFIG['sender_email']
    msg['To'] = to_email
    
    try:
        # Try STARTTLS first
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], 587) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
            print(f"Email sent to {to_email} using STARTTLS.")
        return True
    except Exception as e:
        print(f"STARTTLS failed: {e}")
    
    try:
        # Fallback to SSL
        with smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
            print(f"Email sent to {to_email} using SMTP_SSL.")
        return True
    except Exception as e:
        print(f"SMTP_SSL also failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_sos_email(latitude, longitude, address):
    """Send SOS emergency email to admin"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = "🚨 SOS EMERGENCY ALERT - IMMEDIATE ACTION REQUIRED 🚨"
        
        # Create email body
        google_maps_link = f"https://maps.google.com/?q={latitude},{longitude}"
        
        body = f"""
🚨 SOS EMERGENCY ALERT 🚨

A user has triggered an SOS signal and needs immediate assistance!

LOCATION DETAILS:
• Coordinates: {latitude}, {longitude}
• Address: {address}
• Google Maps: {google_maps_link}
• Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

URGENT ACTION REQUIRED:
Please dispatch emergency services to this location immediately.

This is an automated emergency alert from the Disaster Relief System.

---
Emergency Response Protocol:
1. Verify location accuracy
2. Contact local emergency services
3. Dispatch nearest response team
4. Maintain communication with the user if possible
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Try STARTTLS first
        try:
            with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], 587) as server:
                server.starttls()
                server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
                server.send_message(msg)
                print("SOS email sent to admin using STARTTLS")
                return True
        except Exception as e:
            print(f"STARTTLS failed: {e}")
        
        # Fallback to SSL
        try:
            with smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
                server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
                server.send_message(msg)
                print("SOS email sent to admin using SMTP_SSL")
                return True
        except Exception as e:
            print(f"SMTP_SSL also failed: {e}")
            return False
            
    except Exception as e:
        print(f"Error sending SOS email: {e}")
        return False

@app.route('/api/send-sos', methods=['POST'])
def send_sos():
    """API endpoint to receive SOS alerts from frontend"""
    try:
        data = request.get_json() or {}
        
        # Validate request data
        is_valid, validated_data, errors = validate_request_data(SOSRequest, data)
        if not is_valid:
            return jsonify(ValidationErrorResponse(
                error="Invalid SOS request data",
                details=errors
            ).dict()), 400
        
        latitude = validated_data['latitude']
        longitude = validated_data['longitude']
        address = validated_data.get('address', 'Address not available')
        
        # Send SOS email to admin
        email_sent = send_sos_email(latitude, longitude, address)
        
        # Store SOS alert in database
        with get_db() as conn:
            conn.execute(
                "INSERT INTO sos_alerts (latitude, longitude, address) VALUES (?, ?, ?)",
                (latitude, longitude, address)
            )
            conn.commit()
        
        if email_sent:
            response = SOSResponse(
                success=True,
                message='SOS alert sent successfully! Help is on the way.',
                coordinates=f"{latitude}, {longitude}",
                address=address
            )
            return jsonify(response.dict())
        else:
            response = SOSResponse(
                success=False,
                message='Failed to send SOS email, but alert has been logged',
                error='Email delivery failed'
            )
            return jsonify(response.dict()), 500
            
    except Exception as e:
        print(f"Error in send_sos: {e}")
        response = SOSResponse(
            success=False,
            message='Internal server error',
            error=str(e)
        )
        return jsonify(response.dict()), 500

@app.route('/admin/sos-alerts')
def admin_sos_alerts():
    """Admin page to view SOS alerts"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    with get_db() as conn:
        alerts = conn.execute(
            "SELECT * FROM sos_alerts ORDER BY timestamp DESC LIMIT 50"
        ).fetchall()
    
    return render_template('admin_sos_alerts.html', alerts=alerts)

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    with get_db() as conn:
        users = conn.execute(
            "SELECT id, email, location FROM users ORDER BY email"
        ).fetchall()
    
    if request.method == 'POST':
        location = request.form.get('location')
        message = request.form.get('message')
        
        if not location or not message:
            return render_template('admin_dashboard.html', 
                                users=users,
                                error="Both location and message are required!")
        
        try:
            with get_db() as conn:
                target_users = conn.execute(
                    "SELECT email FROM users WHERE location = ?", 
                    (location,)
                ).fetchall()
                
                if not target_users:
                    return render_template('admin_dashboard.html', 
                                        users=users,
                                        error=f"No users found in location: {location}")
                
                success_count = 0
                failed_emails = []
                
                for user in target_users:
                    if send_alert_email(user['email'], location, message):
                        success_count += 1
                    else:
                        failed_emails.append(user['email'])
                
                result = {
                    'success': f"Alert sent to {success_count}/{len(target_users)} users in {location}",
                    'failed': failed_emails
                }
                
                return render_template('admin_dashboard.html', 
                                    users=users,
                                    result=result['success'],
                                    last_location=location,
                                    last_message=message)
        
        except Exception as e:
            print(f"Error in admin_dashboard: {str(e)}")  # Debug print
            return render_template('admin_dashboard.html', 
                                users=users,
                                error=f"An error occurred: {str(e)}")

    return render_template('admin_dashboard.html', users=users)


@app.route('/admin/missing')
def admin_missing():
    """Admin view: list and manage all missing person reports."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    persons = MissingPerson.query.order_by(MissingPerson.created_at.desc()).all()
    status_choices = ["pending", "verified", "found", "deceased"]
    return render_template(
        'admin_missing.html',
        persons=persons,
        status_choices=status_choices,
    )


@app.route('/admin/missing/<int:person_id>')
def admin_missing_detail(person_id):
    """Admin view: details for a single missing person and their sightings."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    person = MissingPerson.query.get_or_404(person_id)
    sightings = (
        Sighting.query.filter_by(missing_person_id=person_id)
        .order_by(Sighting.date.desc())
        .all()
    )
    status_choices = ["pending", "verified", "found", "deceased"]
    return render_template(
        'admin_missing_detail.html',
        person=person,
        sightings=sightings,
        status_choices=status_choices,
    )


@app.route('/admin/missing/<int:person_id>/status', methods=['POST'])
def admin_update_missing_status(person_id):
    """Admin action: update status (e.g., found, deceased) of a missing person."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    status = request.form.get('status')
    person = MissingPerson.query.get_or_404(person_id)
    try:
        person.status = status
        db.session.commit()
        flash(f"Status for {person.full_name} updated to {status}.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"[admin_update_missing_status] Error: {e}")
        flash("Could not update status. Please try again.", "error")

    return redirect(request.referrer or url_for('admin_missing'))


@app.route('/admin/missing/<int:person_id>/delete', methods=['POST'])
def admin_delete_missing(person_id):
    """Admin action: permanently delete a missing person record."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    person = MissingPerson.query.get_or_404(person_id)
    try:
        db.session.delete(person)
        db.session.commit()
        flash(f"Record for {person.full_name} has been deleted.", "success")
    except Exception as e:

        db.session.rollback()
        print(f"[admin_delete_missing] Error: {e}")
        flash("Could not delete record. Please try again.", "error")

    return redirect(url_for('admin_missing'))


@app.route('/admin/volunteers')
def admin_volunteers():
    """Admin view: list and manage volunteer applications."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    volunteers = Volunteer.query.order_by(Volunteer.created_at.desc()).all()
    status_choices = ["pending", "approved", "rejected"]
    return render_template(
        'admin_volunteers.html',
        volunteers=volunteers,
        status_choices=status_choices,
    )


@app.route('/admin/volunteers/<int:vol_id>/status', methods=['POST'])
def admin_update_volunteer_status(vol_id):
    """Admin action: approve/reject a volunteer."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    status = request.form.get('status')
    vol = Volunteer.query.get_or_404(vol_id)
    try:
        vol.status = status
        db.session.commit()
        flash(f"Volunteer {vol.full_name} marked as {status}.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"[admin_update_volunteer_status] Error: {e}")
        flash("Could not update volunteer status. Please try again.", "error")

    return redirect(url_for('admin_volunteers'))


@app.route('/admin/volunteers/<int:vol_id>/delete', methods=['POST'])
def admin_delete_volunteer(vol_id):
    """Admin action: delete a volunteer record."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    vol = Volunteer.query.get_or_404(vol_id)
    try:
        db.session.delete(vol)
        db.session.commit()
        flash(f"Volunteer {vol.full_name} deleted.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"[admin_delete_volunteer] Error: {e}")
        flash("Could not delete volunteer. Please try again.", "error")

    return redirect(url_for('admin_volunteers'))
@app.route('/api/chat', methods=['POST'])
def chat_with_bot():
    """API endpoint for AI chatbot powered by Groq."""
    try:
        data = request.get_json() or {}
        
        # Validate request data
        is_valid, validated_data, errors = validate_request_data(ChatRequest, data)
        if not is_valid:
            return jsonify(ValidationErrorResponse(
                error="Invalid chat request",
                details=errors
            ).dict()), 400
        
        user_message = validated_data['message']
        
        # Try Groq API first
        ai_response = call_groq_api(user_message)
        
        if ai_response:
            return jsonify(ChatResponse(response=ai_response).dict())
        
        # Fallback responses if API fails
        fallback_responses = {
            'hello': "Hello! I'm your AI DisasterBot. I can help with disaster management questions.",
            'earthquake': "For earthquakes: DROP, COVER, and HOLD ON. Stay away from windows and heavy objects. Check for injuries and gas leaks after.",
            'flood': "For floods: Move to higher ground immediately. Avoid walking through flood water. Turn off utilities if instructed.",
            'fire': "For fires: Evacuate immediately if ordered. Close all windows and doors. Have an escape plan ready.",
            'emergency': "In emergencies, call local emergency services (911) or use the SOS button on this website.",
            'kit': "Emergency kit should include: water (1 gal/person/day), non-perishable food, flashlight, batteries, first aid supplies, medications, radio, and important documents.",
            'missing': "To report missing persons, use our Missing Persons page or contact local authorities immediately.",
            'evacuation': "Know your evacuation routes in advance. Have a family meeting point. Keep important documents ready."
        }
        
        user_lower = user_message.lower()
        response_text = "I'm your AI disaster management assistant. I can help with earthquakes, floods, fires, emergency kits, evacuation procedures, and missing persons. What would you like to know?"
        
        for key, value in fallback_responses.items():
            if key in user_lower:
                response_text = value
                break
        
        return jsonify(ChatResponse(response=response_text).dict())
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify(ChatResponse(
            response='I apologize, but I\'m having trouble right now. Please try again or contact emergency services if this is urgent.'
        ).dict()), 500

@app.route('/api/rumor-check', methods=['POST'])
def rumor_check():
    """API endpoint to classify disaster-related rumors."""
    try:
        data = request.get_json() or {}
        
        # Validate request data
        is_valid, validated_data, errors = validate_request_data(RumorCheckRequest, data)
        if not is_valid:
            return jsonify(ValidationErrorResponse(
                error="Invalid rumor check request",
                details=errors
            ).dict()), 400
        
        message = validated_data['message']
        context = validated_data.get('context', '')
        source = validated_data.get('source', '')

        combined_text = message
        if context:
            combined_text = f"{message}\nContext: {context}"
        if source:
            combined_text = f"{combined_text}\nSource: {source}"

        result = analyze_rumor(combined_text)
        status_code = 200 if result.get("classification") != "Unavailable" else 503

        response = RumorCheckResponse(
            classification=result["classification"],
            confidence=result["confidence"],
            advice=result["advice"],
            raw_label=result["raw_label"],
            reasons=result["reasons"],
            evaluated_at=datetime.utcnow().isoformat() + "Z"
        )
        
        return jsonify(response.dict()), status_code
        
    except Exception as e:
        print(f"Rumor check error: {e}")
        response = RumorCheckResponse(
            classification="Error",
            confidence=0.0,
            advice="Unable to process request at this time",
            raw_label="ERROR",
            reasons=["System error occurred"],
            evaluated_at=datetime.utcnow().isoformat() + "Z",
            error=str(e)
        )
        return jsonify(response.dict()), 500
@app.route('/')
def home():
    return render_template('index.html')
def get_initials(email):
    try:
        name = email.split("@")[0]
        parts = name.replace('.', ' ').split()
        initials = "".join([p[0].upper() for p in parts])
        return initials[:2]  # max 2 letters
    except:
        return "U"
@app.context_processor
def inject_user():
    email = session.get('user_email')
    initials = get_initials(email) if email else None
    return dict(user_email=email, user_initials=initials)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = {
            'email': request.form.get('email'),
            'location': request.form.get('location')
        }
        
        # Validate request data
        is_valid, validated_data, errors = validate_request_data(UserRegistration, data)
        if not is_valid:
            error_msg = "Registration failed: " + "; ".join(errors.values())
            flash(error_msg, "error")
            return redirect(url_for('register'))
        
        try:
            with get_db() as conn:
                conn.execute("INSERT INTO users (email, location) VALUES (?, ?)", 
                           (validated_data['email'], validated_data['location']))
                conn.commit()
                
            session['user_email'] = validated_data['email']
            flash("Registration successful! You'll now receive alerts.", "success")
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            flash("This email is already registered!", "error")
            return redirect(url_for('register'))
        except Exception as e:
            print(f"Registration error: {e}")
            flash("Registration failed. Please try again.", "error")
            return redirect(url_for('register'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login existing user by email only."""
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash("Email is required to login.", "error")
            return redirect(url_for('login'))

        with get_db() as conn:
            user = conn.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()

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
    admin_error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        with get_db() as conn:
            admin = conn.execute(
                "SELECT password FROM admins WHERE username = ?", 
                (username,)
            ).fetchone()
        
        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            admin_error = "Invalid credentials!"
    
    return render_template('login.html', admin_error=admin_error)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

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

@app.route('/missing', methods=['GET'])
def missing():
    """Public page: search and list missing persons."""
    name = request.args.get('name', '').strip()
    location = request.args.get('location', '').strip()
    age_range = request.args.get('age_range', '').strip()

    query = MissingPerson.query.filter(
        MissingPerson.status.in_(["pending", "verified"])
    )

    if name:
        query = query.filter(MissingPerson.full_name.ilike(f"%{name}%"))
    if location:
        query = query.filter(MissingPerson.last_location.ilike(f"%{location}%"))

    if age_range:
        if age_range == "0-12":
            query = query.filter(MissingPerson.age >= 0, MissingPerson.age <= 12)
        elif age_range == "13-17":
            query = query.filter(MissingPerson.age >= 13, MissingPerson.age <= 17)
        elif age_range == "18-59":
            query = query.filter(MissingPerson.age >= 18, MissingPerson.age <= 59)
        elif age_range == "60+":
            query = query.filter(MissingPerson.age >= 60)

    persons = query.order_by(MissingPerson.created_at.desc()).all()

    return render_template(
        'missing.html',
        persons=persons,
        name=name,
        location=location,
        age_range=age_range,
    )


@app.route('/missing/report', methods=['POST'])
def report_missing():
    """Handle submission of a new missing person report."""
    form = request.form
    photo = request.files.get('missing-photo')

    # Prepare data for validation
    data = {
        'full_name': form.get('missing-name'),
        'age': int(form.get('missing-age')) if form.get('missing-age') else None,
        'gender': form.get('missing-gender'),
        'last_location': form.get('missing-location'),
        'last_seen_date': form.get('missing-date'),
        'description': form.get('missing-description'),
        'notes': form.get('missing-notes'),
        'reporter_name': form.get('reporter-name'),
        'reporter_contact': form.get('reporter-contact'),
        'reporter_relation': form.get('reporter-relation')
    }
    
    # Validate request data
    is_valid, validated_data, errors = validate_request_data(MissingPersonReport, data)
    if not is_valid:
        error_msg = "Report submission failed: " + "; ".join(errors.values())
        flash(error_msg, "error")
        return redirect(url_for('missing'))

    photo_path = None
    if photo and photo.filename:
        filename = secure_filename(photo.filename)
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, filename)
        photo.save(save_path)
        photo_path = os.path.join('uploads', filename)

    try:
        person = MissingPerson(
            full_name=validated_data['full_name'],
            age=validated_data.get('age'),
            gender=validated_data.get('gender'),
            last_location=validated_data['last_location'],
            last_seen_date=validated_data.get('last_seen_date'),
            description=validated_data['description'],
            notes=validated_data.get('notes'),
            photo_path=photo_path,
            reporter_name=validated_data['reporter_name'],
            reporter_contact=validated_data['reporter_contact'],
            reporter_relation=validated_data['reporter_relation'],
            status='pending',
        )
        db.session.add(person)
        db.session.commit()
        flash('Missing person report submitted successfully. Admin will review it.', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"[report_missing] Error: {e}")
        flash('There was an error submitting the report. Please try again.', 'error')

    return redirect(url_for('missing'))


@app.route('/sighting/report', methods=['POST'])
def report_sighting():
    """Handle submission of a sighting report for a missing person."""
    form = request.form
    media = request.files.get('sighting-photo')

    media_path = None
    if media and media.filename:
        filename = secure_filename(media.filename)
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, filename)
        media.save(save_path)
        media_path = os.path.join('uploads', filename)

    try:
        date_str = form.get('sighting-date')
        sighting_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else None

        sighting = Sighting(
            missing_person_id=int(form.get('missing_person_id')),
            date=sighting_date,
            location=form.get('sighting-location'),
            details=form.get('sighting-details'),
            contact_info=form.get('sighting-contact'),
            media_path=media_path,
        )
        db.session.add(sighting)
        db.session.commit()
        flash(
            'Thank you for reporting this sighting. This information could be crucial.',
            'success',
        )
    except Exception as e:
        db.session.rollback()
        print(f"[report_sighting] Error: {e}")
        flash('There was an error submitting the sighting. Please try again.', 'error')

    return redirect(url_for('missing'))

@app.route('/protection')
def protection():
    return render_template('protecthome.html')  

@app.route('/routes')
def routes():
    return render_template('routes.html')

@app.route('/user')
def user():
    return render_template('user.html')


@app.route('/volunteer/register', methods=['POST'])
def register_volunteer():
    """Handle general volunteer registration."""
    if not session.get('user_email'):
        flash('Please register or log in before applying as a volunteer.', 'error')
        return redirect(url_for('register'))

    form = request.form
    try:
        interests_list = form.getlist('vol-interests')
        interests = ",".join(interests_list) if interests_list else None

        volunteer = Volunteer(
            full_name=form.get('vol-name'),
            email=form.get('vol-email'),
            phone=form.get('vol-phone'),
            location=form.get('vol-location'),
            skills=form.get('vol-skills'),
            availability=form.get('vol-availability'),
            interests=interests,
        )
        db.session.add(volunteer)
        db.session.commit()
        flash('Thank you for your volunteer application!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"[register_volunteer] Error: {e}")
        flash('There was an error submitting your application. Please try again.', 'error')

    return redirect(url_for('missing'))


@app.route('/volunteer/apply-role', methods=['POST'])
def apply_role():
    """Handle volunteer applications for specific roles from the modal."""
    if not session.get('user_email'):
        flash('Please register or log in before applying as a volunteer.', 'error')
        return redirect(url_for('register'))

    form = request.form
    try:
        # location/skills are optional for role-based applications, but the model
        # requires a non-null location, so store a placeholder description.
        volunteer = Volunteer(
            full_name=form.get('vol-specific-name'),
            email=form.get('vol-specific-email'),
            phone=form.get('vol-specific-phone'),
            location=form.get('vol-location') or 'Not specified',
            skills=None,
            availability='immediate' if form.get('immediate') == 'yes' else 'flexible',
            interests=None,
            role_applied=form.get('role_name'),
            experience=form.get('vol-specific-experience'),
            notes=form.get('vol-specific-notes'),
        )
        db.session.add(volunteer)
        db.session.commit()
        flash(
            f"Application submitted for {form.get('role_name')}. We'll contact you soon.",
            'success',
        )
    except Exception as e:
        db.session.rollback()
        print(f"[apply_role] Error: {e}")
        flash('There was an error submitting your application. Please try again.', 'error')

    return redirect(url_for('missing'))

if __name__ == '__main__':
    app.run(debug=True)