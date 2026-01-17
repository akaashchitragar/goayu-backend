# Ayushya Backend API

AI-Powered Ayurvedic Consultation Platform - Python FastAPI Backend

## Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB Atlas
- **AI**: Google Gemini 3 Pro
- **Deployment**: Railway

## Setup Instructions

### 1. Install Dependencies

```bash
cd /Volumes/CODE/goayu-backend
pip3 install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the root directory (already created):

```bash
MONGODB_URI=mongodb+srv://goayu_db_user:5bIiDPi3i1jOVGpr@goayu-prod.2vquueo.mongodb.net/?appName=goayu-prod
MONGODB_DB_NAME=ayushya
GEMINI_API_KEY=AIzaSyDv6l9RHoNj2RswE3HbbwfmpRg6JoQANEM
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://goayu.life
```

### 3. Run Development Server

```bash
python3 main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Questionnaire
- `POST /api/v1/questionnaire/submit` - Submit questionnaire and get constitutional analysis
- `GET /api/v1/questionnaire/{questionnaire_id}` - Get questionnaire by ID
- `GET /api/v1/questionnaire/` - List all questionnaires

### Consultation
- `POST /api/v1/consultation/` - Create consultation with AI-powered remedy generation
- `GET /api/v1/consultation/{consultation_id}` - Get consultation by ID
- `GET /api/v1/consultation/` - List all consultations
- `GET /api/v1/consultation/by-questionnaire/{questionnaire_id}` - Get consultations by questionnaire

## Project Structure

```
goayu-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── questionnaire.py
│   │       └── consultation.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── questionnaire.py
│   │   └── consultation.py
│   └── services/
│       ├── ayurveda_service.py
│       └── ai_service.py
├── main.py
├── requirements.txt
├── Procfile
├── runtime.txt
└── .env
```

## Railway Deployment

1. Push code to GitHub
2. Connect repository to Railway
3. Railway will automatically detect Python and use the Procfile
4. Set environment variables in Railway dashboard
5. Deploy!

## MongoDB Collections

### questionnaires
Stores user questionnaire responses and constitutional analysis

### consultations
Stores AI-generated consultations with remedies and recommendations
