"""AWS services integration for patient data management."""

import boto3
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional
import uuid
import os
from dotenv import load_dotenv

load_dotenv()


class AWSHealthServices:
    """Manages patient data using AWS services."""
    
    def __init__(self, region=None):
        """Initialize AWS clients."""
        if region is None:
            region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
        
        self.region = region
        self.s3 = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.cognito = boto3.client('cognito-idp', region_name=region)
        
        # Configuration
        self.bucket_name = 'health-companion-fhir-data'
        self.user_pool_id = None  # Set from environment
        self.users_table = self.dynamodb.Table('HealthCompanionUsers')
        self.documents_table = self.dynamodb.Table('MedicalDocuments')
    
    def create_patient_profile(self, username: str, email: str, user_id: str) -> Dict:
        """
        Create FHIR Patient resource when user registers.
        
        Args:
            username: User's username
            email: User's email
            user_id: Unique user ID from Cognito
            
        Returns:
            Patient FHIR resource
        """
        patient_id = f"patient-{user_id}"
        
        # Create FHIR Patient resource
        patient_resource = {
            "resourceType": "Patient",
            "id": patient_id,
            "identifier": [{
                "system": "health-companion",
                "value": user_id
            }],
            "name": [{
                "text": username,
                "family": username.split()[-1] if ' ' in username else username,
                "given": [username.split()[0]] if ' ' in username else [username]
            }],
            "telecom": [{
                "system": "email",
                "value": email,
                "use": "home"
            }],
            "active": True,
            "meta": {
                "lastUpdated": datetime.now().isoformat()
            }
        }
        
        # Save to S3
        s3_key = f"patients/{patient_id}/patient.json"
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=json.dumps(patient_resource, indent=2),
            ContentType='application/fhir+json'
        )
        
        # Save metadata to DynamoDB
        self.users_table.put_item(Item={
            'user_id': user_id,
            'patient_id': patient_id,
            'username': username,
            'email': email,
            's3_patient_key': s3_key,
            'created_at': datetime.now().isoformat(),
            'document_count': 0
        })
        
        return patient_resource
    
    def save_diagnostic_report(self, user_id: str, structured_data: Dict, 
                               file_name: str, file_data: bytes) -> Optional[str]:
        """
        Save lab report in FHIR format to S3.
        
        Args:
            user_id: User's ID
            structured_data: Parsed medical data
            file_name: Original file name
            file_data: Original file bytes
            
        Returns:
            Report ID if saved, None if duplicate
        """
        print(f"\n🔵 save_diagnostic_report called for user: {user_id}, file: {file_name}")
        print(f"🔵 Bucket: {self.bucket_name}, Region: {self.region}")
        print(f"🔵 Structured data keys: {structured_data.keys() if structured_data else 'None'}")
        
        # Get patient info or create if doesn't exist
        try:
            user_info = self.users_table.get_item(Key={'user_id': user_id})
            if 'Item' not in user_info:
                # Create patient profile if doesn't exist
                patient_id = f"patient-{user_id}"
                self.users_table.put_item(Item={
                    'user_id': user_id,
                    'patient_id': patient_id,
                    'username': 'user',
                    'email': '',
                    's3_patient_key': f"patients/{patient_id}/patient.json",
                    'created_at': datetime.now().isoformat(),
                    'document_count': 0
                })
            else:
                patient_id = user_info['Item']['patient_id']
        except Exception:
            patient_id = f"patient-{user_id}"
        
        # Check for duplicate
        doc_hash = hashlib.md5(file_data).hexdigest()
        print(f"🔵 Document hash: {doc_hash}")
        
        try:
            existing = self.documents_table.query(
                IndexName='user_id-doc_hash-index',
                KeyConditionExpression='user_id = :uid AND doc_hash = :hash',
                ExpressionAttributeValues={':uid': user_id, ':hash': doc_hash}
            )
            
            if existing.get('Items'):
                print(f"⚠️ Duplicate document detected")
                return None  # Duplicate
            print(f"✅ No duplicate found, proceeding...")
        except Exception as e:
            print(f"⚠️ Error checking duplicates (continuing anyway): {e}")
        
        # Generate IDs
        report_id = f"report-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now().isoformat()
        print(f"🔵 Generated report_id: {report_id}")
        
        # Create FHIR DiagnosticReport
        diagnostic_report = {
            "resourceType": "DiagnosticReport",
            "id": report_id,
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "LAB",
                    "display": "Laboratory"
                }]
            }],
            "code": {
                "text": "Laboratory Report"
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": structured_data.get('effectiveDateTime', timestamp),
            "issued": timestamp,
            "result": [],
            "meta": {
                "lastUpdated": timestamp
            }
        }
        
        # Save original file FIRST (always save this)
        original_key = f"patients/{patient_id}/originals/{timestamp}_{file_name}"
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=original_key,
                Body=file_data
            )
            print(f"✅ Saved original file: {original_key}")
        except Exception as e:
            print(f"❌ Error saving original file: {e}")
            raise
        
        # Create FHIR Observations for each test
        observations = []
        obs_list = structured_data.get('observations', [])
        print(f"🔵 Processing {len(obs_list)} observations...")
        
        if not obs_list:
            print("⚠️ No observations found in structured data - saving original file only")
            # Save minimal metadata to DynamoDB
            self.documents_table.put_item(Item={
                'user_id': user_id,
                'document_id': report_id,
                'patient_id': patient_id,
                'doc_hash': doc_hash,
                'document_type': 'medical_document',
                'file_name': file_name,
                's3_original_key': original_key,
                'upload_timestamp': timestamp,
                'observation_count': 0
            })
            return report_id
        
        for obs_data in obs_list:
            obs_id = f"obs-{uuid.uuid4().hex[:12]}"
            
            observation = {
                "resourceType": "Observation",
                "id": obs_id,
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                        "display": "Laboratory"
                    }]
                }],
                "code": {
                    "text": obs_data['code']['text']
                },
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "effectiveDateTime": structured_data.get('effectiveDateTime', timestamp),
                "issued": timestamp,
                "valueQuantity": {
                    "value": obs_data['valueQuantity'].get('value'),
                    "unit": obs_data['valueQuantity'].get('unit'),
                    "system": "http://unitsofmeasure.org"
                },
                "interpretation": [{
                    "coding": [{
                        "code": obs_data.get('interpretation', 'normal')
                    }]
                }],
                "referenceRange": [{
                    "text": obs_data['referenceRange'][0]['text']
                }]
            }
            
            observations.append(observation)
            diagnostic_report['result'].append({"reference": f"Observation/{obs_id}"})
            
            # Save observation to S3
            obs_key = f"patients/{patient_id}/observations/{obs_id}.json"
            try:
                self.s3.put_object(
                    Bucket=self.bucket_name,
                    Key=obs_key,
                    Body=json.dumps(observation, indent=2),
                    ContentType='application/fhir+json'
                )
                print(f"✅ Saved observation: {obs_key}")
            except Exception as e:
                print(f"❌ Error saving observation: {e}")
                raise
        
        # Save diagnostic report to S3
        report_key = f"patients/{patient_id}/diagnostic-reports/{report_id}.json"
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=report_key,
                Body=json.dumps(diagnostic_report, indent=2),
                ContentType='application/fhir+json'
            )
            print(f"✅ Saved report: {report_key}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")
            raise
        
        # Save metadata to DynamoDB
        self.documents_table.put_item(Item={
            'user_id': user_id,
            'document_id': report_id,
            'patient_id': patient_id,
            'doc_hash': doc_hash,
            'document_type': 'diagnostic_report',
            'file_name': file_name,
            's3_fhir_key': report_key,
            's3_original_key': original_key,
            'upload_timestamp': timestamp,
            'observation_count': len(observations),
            'test_date': structured_data.get('effectiveDateTime', timestamp)
        })
        
        # Update user document count
        self.users_table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET document_count = document_count + :inc',
            ExpressionAttributeValues={':inc': 1}
        )
        
        return report_id
    
    def get_patient_reports(self, user_id: str, limit: int = 10) -> list:
        """Get all diagnostic reports for a patient."""
        try:
            # Get patient_id
            user_info = self.users_table.get_item(Key={'user_id': user_id})
            if 'Item' not in user_info:
                return []
        except Exception:
            return []
        
        patient_id = user_info['Item']['patient_id']
        
        # List all reports from S3
        reports = []
        prefix = f"patients/{patient_id}/diagnostic-reports/"
        
        response = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix,
            MaxKeys=limit
        )
        
        for obj in response.get('Contents', []):
            # Get report content
            report_obj = self.s3.get_object(Bucket=self.bucket_name, Key=obj['Key'])
            report_data = json.loads(report_obj['Body'].read())
            
            # Get associated observations
            observations = []
            for result_ref in report_data.get('result', []):
                obs_id = result_ref['reference'].split('/')[-1]
                obs_key = f"patients/{patient_id}/observations/{obs_id}.json"
                
                try:
                    obs_obj = self.s3.get_object(Bucket=self.bucket_name, Key=obs_key)
                    obs_data = json.loads(obs_obj['Body'].read())
                    observations.append(obs_data)
                except:
                    pass
            
            reports.append({
                'report': report_data,
                'observations': observations
            })
        
        return reports
    
    def compare_reports(self, user_id: str) -> Optional[Dict]:
        """Compare last two reports for a patient."""
        try:
            reports = self.get_patient_reports(user_id, limit=2)
        except Exception:
            return None
        
        if len(reports) < 2:
            return None
        
        # Extract observations from both reports
        report1_obs = {obs['code']['text']: obs for obs in reports[1]['observations']}
        report2_obs = {obs['code']['text']: obs for obs in reports[0]['observations']}
        
        comparison = {
            'report1_date': reports[1]['report']['effectiveDateTime'],
            'report2_date': reports[0]['report']['effectiveDateTime'],
            'changes': []
        }
        
        for test_name, obs2 in report2_obs.items():
            if test_name in report1_obs:
                obs1 = report1_obs[test_name]
                
                val1 = obs1['valueQuantity'].get('value')
                val2 = obs2['valueQuantity'].get('value')
                
                if val1 and val2:
                    change = val2 - val1
                    comparison['changes'].append({
                        'test': test_name,
                        'previous': val1,
                        'current': val2,
                        'change': change,
                        'unit': obs2['valueQuantity'].get('unit'),
                        'trend': 'up' if change > 0 else 'down' if change < 0 else 'stable'
                    })
        
        return comparison
