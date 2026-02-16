"""AWS service layer for S3, DynamoDB, Bedrock, and Textract."""

import boto3
import json
import hashlib
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

class AWSService:
    def __init__(self):
        region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
        self.s3 = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)
        self.textract = boto3.client('textract', region_name=region)
        
        self.bucket = 'health-companion-fhir-data'
        self.users_table = self.dynamodb.Table('HealthCompanionUsers')
        self.docs_table = self.dynamodb.Table('MedicalDocuments')
    
    def save_document(self, user_id, patient_id, file_name, file_data):
        """Save document to S3 and extract text."""
        doc_hash = hashlib.md5(file_data).hexdigest()
        
        # Check duplicate
        try:
            existing = self.docs_table.query(
                IndexName='user_id-doc_hash-index',
                KeyConditionExpression='user_id = :uid AND doc_hash = :hash',
                ExpressionAttributeValues={':uid': user_id, ':hash': doc_hash}
            )
            if existing.get('Items'):
                return None, "Duplicate document"
        except:
            pass
        
        # Save to S3
        doc_id = f"doc-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now().isoformat()
        s3_key = f"patients/{patient_id}/documents/{doc_id}_{file_name}"
        
        self.s3.put_object(Bucket=self.bucket, Key=s3_key, Body=file_data)
        
        # Extract text
        extracted_text = ""
        try:
            response = self.textract.detect_document_text(Document={'Bytes': file_data})
            extracted_text = "\n".join([b['Text'] for b in response['Blocks'] if b['BlockType'] == 'LINE'])
        except:
            extracted_text = "Text extraction failed"
        
        # Save metadata
        self.docs_table.put_item(Item={
            'user_id': user_id,
            'document_id': doc_id,
            'patient_id': patient_id,
            'doc_hash': doc_hash,
            'file_name': file_name,
            's3_key': s3_key,
            'upload_timestamp': timestamp,
            'extracted_text': extracted_text[:1000]
        })
        
        return doc_id, extracted_text
    
    def get_user_documents(self, user_id, limit=10):
        """Get user's documents from DynamoDB."""
        try:
            response = self.docs_table.query(
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id},
                Limit=limit,
                ScanIndexForward=False
            )
            return response.get('Items', [])
        except:
            return []
    
    def chat_with_context(self, message, user_id):
        """Chat with Bedrock using user's documents as context."""
        # Get documents
        docs = self.get_user_documents(user_id, limit=5)
        context = "\n\nPatient's Medical Documents:\n"
        for doc in docs:
            context += f"- {doc['file_name']}: {doc.get('extracted_text', '')[:200]}\n"
        
        prompt = f"""You are a health assistant. When comparing lab results or medical data, format comparisons as HTML tables. Use this exact format with NO extra newlines before or after the table:

<table><tr><th>Test</th><th>Date 1</th><th>Date 2</th></tr><tr><td>Hemoglobin</td><td>12.9</td><td>12.4</td></tr></table>

Patient asks: {message}{context}

Provide clear, empathetic response. Put tables directly after text with no blank lines."""
        
        try:
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            result = json.loads(response['body'].read())
            return result['content'][0]['text']
        except Exception as e:
            return f"Error: {str(e)}"
