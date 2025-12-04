# 🚀 Complete Setup Guide - Disaster Management System

## 📋 Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Internet connection

## ⚡ Quick Setup (3 Steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
1. Get Groq API key from: https://console.groq.com/
2. Open `.env` file
3. Replace `your_groq_api_key_here` with your actual key:
```
GROQ_API_KEY=gsk_your_actual_api_key_here
```

### 3. Run Application
```bash
python app.py
```

## 🌐 Access Your Application
- **Main Website**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin/login
  - Username: `admin`
  - Password: `admin123`

## ✅ Features Working
- ✅ AI Chatbot (Groq + LangChain)
- ✅ SOS Emergency System
- ✅ Missing Persons Database
- ✅ Volunteer Management
- ✅ Rumor Verification
- ✅ Email Alerts
- ✅ Data Validation (Pydantic)
- ✅ Admin Dashboard

## 🔧 Troubleshooting
- **Port 5000 busy**: Change port in `app.py` (last line)
- **API not working**: Check your Groq API key in `.env`
- **Database errors**: Delete `users.db` and restart

## 📱 Ready for Presentation!
Your disaster management system is production-ready with AI chatbot and complete validation.