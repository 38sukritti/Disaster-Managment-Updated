# 🛡️ सुरक्षासेतु - Disaster Management System

<div align="center">

![Disaster Management](https://img.shields.io/badge/Disaster-Management-red?style=for-the-badge)
![AI Powered](https://img.shields.io/badge/AI-Powered-blue?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge)

**Empowering Resilience Through Preparedness & Action**

*A comprehensive AI-powered disaster management platform for emergency response, community support, and real-time assistance.*

</div>

---

## 👥 **Team Members**

<table align="center">
<tr>
<td align="center"><b>🌟 Richa</b></td>
<td align="center"><b>🌟 Nayamat</b></td>
<td align="center"><b>🌟 Sukriti</b></td>
<td align="center"><b>🌟 Vanya</b></td>
</tr>
</table>

---

## 🚀 **Features**

### 🤖 **AI-Powered Chatbot**
- **Groq LLaMA Integration** for intelligent disaster guidance
- Real-time emergency assistance and safety tips
- Contextual responses for earthquake, flood, fire emergencies

### 🆘 **SOS Emergency System**
- One-click GPS-based emergency alerts
- Automatic email notifications to authorities
- Real-time location tracking and mapping

### 👥 **Missing Persons Database**
- Report and search missing persons
- Photo uploads and detailed descriptions
- Sighting reports with location tracking
- Admin verification system

### 🤝 **Volunteer Management**
- Volunteer registration and skill matching
- Role-based applications (Medical, Rescue, Support)
- Availability tracking and coordination

### 📰 **Rumor Verification**
- AI-powered fake news detection
- Real-time credibility analysis
- Source verification and fact-checking

### 📧 **Alert System**
- Location-based emergency notifications
- Email alerts for registered users
- Admin dashboard for mass communications

### 🔒 **Data Validation**
- Pydantic-powered input validation
- Secure API endpoints
- Type safety and error handling

---

## 🛠️ **Technology Stack**

| Component | Technology |
|-----------|------------|
| **Backend** | Flask 2.3.3, SQLAlchemy |
| **AI/ML** | Groq API, Transformers, PyTorch |
| **Validation** | Pydantic 2.5.0 |
| **Database** | SQLite |
| **Frontend** | HTML5, CSS3, JavaScript |
| **Maps** | Leaflet.js |
| **Email** | SMTP Integration |

---

## ⚡ **Quick Start**

### 1. **Clone & Install**
```bash
git clone <repository-url>
cd Movathon
pip install -r requirements.txt
```

### 2. **Configure API Key**
```bash
# Get API key from: https://console.groq.com/
# Edit .env file:
GROQ_API_KEY=your_groq_api_key_here
```

### 3. **Run Application**
```bash
python app.py
```

### 4. **Access System**
- **Website**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin/login
  - Username: `admin` | Password: `admin123`

---

## 📱 **Screenshots**

### 🏠 **Homepage with Live Threat Dashboard**
- Interactive disaster map with real-time alerts
- AI chatbot integration
- Quick access to emergency features

### 🆘 **SOS Emergency Interface**
- One-click emergency button
- GPS location detection
- Instant alert dispatch

### 🤖 **AI Disaster Assistant**
- Intelligent conversation interface
- Context-aware emergency guidance
- Multi-language support ready

### 👥 **Missing Persons Portal**
- Advanced search and filtering
- Photo upload and verification
- Sighting report system

---

## 🔧 **API Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | AI chatbot interaction |
| `/api/send-sos` | POST | Emergency SOS alerts |
| `/api/rumor-check` | POST | Fake news verification |
| `/missing/report` | POST | Missing person reports |
| `/volunteer/register` | POST | Volunteer registration |

---

## 🏆 **Key Achievements**

✅ **Real-time AI assistance** for disaster scenarios  
✅ **GPS-based emergency response** system  
✅ **Comprehensive data validation** with Pydantic  
✅ **Multi-modal communication** (Email, Web, Mobile-ready)  
✅ **Scalable architecture** for high-traffic scenarios  
✅ **Security-first design** with input sanitization  
✅ **Admin dashboard** for emergency coordination  
✅ **Community-driven** missing persons database  

---

## 🌟 **Innovation Highlights**

### 🧠 **AI-Powered Decision Making**
- LLaMA model integration for contextual emergency guidance
- Real-time rumor detection and fact-checking
- Intelligent volunteer-task matching

### 🗺️ **Geospatial Intelligence**
- Interactive disaster mapping with Leaflet.js
- GPS-based emergency location services
- Location-aware alert distribution

### 🔐 **Enterprise-Grade Security**
- Pydantic data validation for all inputs
- SQL injection prevention
- Secure API authentication

---

## 📊 **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask Backend  │    │   External APIs │
│   (HTML/CSS/JS) │◄──►│   + Pydantic     │◄──►│   Groq AI       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │   SQLite DB      │
                       │   + File Storage │
                       └──────────────────┘
```

---

## 🚀 **Future Enhancements**

- 📱 **Mobile App** (React Native)
- 🌐 **Multi-language Support** (Hindi, Regional languages)
- 📡 **IoT Integration** (Sensor data, Weather APIs)
- 🤖 **Advanced ML Models** (Disaster prediction)
- 🔔 **Push Notifications** (Real-time alerts)
- 📊 **Analytics Dashboard** (Response metrics)

---

## 🤝 **Contributing**

We welcome contributions! Please feel free to submit issues, feature requests, or pull requests.

---

## 📄 **License**

This project is developed for educational and humanitarian purposes.

---

<div align="center">

### 🌟 **Built with ❤️ by Team Richa, Nayamat, Sukriti & Vanya**

**Making communities safer, one click at a time** 🛡️

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue?style=flat-square&logo=python)](https://python.org)
[![Powered by AI](https://img.shields.io/badge/Powered%20by-AI-red?style=flat-square&logo=openai)](https://groq.com)
[![Built with Flask](https://img.shields.io/badge/Built%20with-Flask-green?style=flat-square&logo=flask)](https://flask.palletsprojects.com)

</div>