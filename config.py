"""Configuration module for AWS Bedrock and application settings."""

import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Bedrock Model Configuration
BEDROCK_MODEL_ID = 'anthropic.claude-3-5-sonnet-20241022-v2:0'
MAX_TOKENS = 2048
TEMPERATURE = 0.7

# Knowledge Base Configuration
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID', '')
KNOWLEDGE_BASE_ENABLED = bool(KNOWLEDGE_BASE_ID)

# Document Categories
DOCUMENT_CATEGORIES = {
    'PRESCRIPTION': 'prescription',
    'LAB_REPORT': 'lab_report',
    'MEDICAL_IMAGE': 'medical_image',
    'UNKNOWN': 'unknown'
}
