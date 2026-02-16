# AI Health Companion 🏥

Professional health assistant with AWS backend and clean architecture.

## Architecture

```
├── backend/
│   ├── api/
│   │   └── routes.py          # REST API endpoints
│   ├── services/
│   │   ├── auth_service.py    # Authentication logic
│   │   └── aws_service.py     # AWS integrations (S3, DynamoDB, Bedrock, Textract)
│   └── app.py                 # Flask application
├── frontend/
│   ├── templates/             # HTML templates
│   └── static/                # CSS, JS assets
├── run.py                     # Application entry point
└── requirements.txt           # Dependencies
```

## Features

- 🔐 **Authentication** - Secure login/register with DynamoDB
- 📤 **Document Upload** - Saves to S3, extracts text with Textract
- 💬 **AI Chat** - Bedrock Claude with patient document context
- 📁 **Document Management** - View all uploaded medical files

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials in .env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-west-2
FLASK_SECRET_KEY=your-secret-key

# Run application
python run.py
```

Open: **http://localhost:5000**

## API Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `POST /api/documents/upload` - Upload medical document
- `GET /api/documents/list` - Get user's documents
- `POST /api/chat` - Chat with AI assistant

## AWS Services

- **S3** - Document storage (`patients/{patient_id}/documents/`)
- **DynamoDB** - User profiles and document metadata
- **Bedrock** - Claude 3 Sonnet for AI responses
- **Textract** - OCR text extraction

## Security

- Password hashing with Werkzeug
- Session-based authentication
- AWS IAM permissions
- S3 encryption at rest
