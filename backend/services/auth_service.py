"""Authentication service."""

import boto3
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

class AuthService:
    def __init__(self):
        region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.users_table = self.dynamodb.Table('HealthCompanionUsers')
        self.bucket = 'health-companion-fhir-data'
    
    def register(self, username, email, password):
        """Register new user."""
        user_id = username
        patient_id = f"patient-{user_id}"
        
        try:
            # Create user
            self.users_table.put_item(Item={
                'user_id': user_id,
                'patient_id': patient_id,
                'username': username,
                'email': email,
                'password_hash': generate_password_hash(password),
                's3_patient_key': f"patients/{patient_id}/patient.json",
                'created_at': datetime.now().isoformat(),
                'document_count': 0
            })
            
            # Create patient folder
            patient_data = {
                "resourceType": "Patient",
                "id": patient_id,
                "name": [{"text": username}],
                "telecom": [{"system": "email", "value": email}],
                "active": True
            }
            
            self.s3.put_object(
                Bucket=self.bucket,
                Key=f"patients/{patient_id}/patient.json",
                Body=json.dumps(patient_data),
                ContentType='application/json'
            )
            
            return True, None
        except Exception as e:
            return False, str(e)
    
    def login(self, username, password):
        """Login user."""
        try:
            response = self.users_table.get_item(Key={'user_id': username})
            if 'Item' in response:
                user = response['Item']
                if check_password_hash(user['password_hash'], password):
                    return True, {
                        'user_id': user['user_id'],
                        'username': user['username'],
                        'patient_id': user['patient_id']
                    }
            return False, None
        except:
            return False, None
