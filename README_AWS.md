## 🚀 AWS-Powered Health Companion Setup Guide

### Architecture Overview

```
User Registration → Create Patient Profile (FHIR) → Save to S3
User Upload → Textract Extract → Parse to FHIR → Save to S3 + DynamoDB
User Query → Retrieve from S3 → Compare/Analyze → AI Response
```

### AWS Services Used

1. **Amazon S3** - FHIR data storage
2. **Amazon DynamoDB** - Metadata & indexing
3. **Amazon Textract** - Document OCR
4. **Amazon Bedrock** - AI chat & knowledge base
5. **AWS IAM** - Access control

---

### Setup Instructions

#### Step 1: Run Infrastructure Setup

```bash
python setup_aws_infrastructure.py
```

This creates:
- S3 bucket: `health-companion-fhir-data`
- DynamoDB tables: `HealthCompanionUsers`, `MedicalDocuments`
- Prints IAM policy

#### Step 2: Configure IAM

1. Go to AWS Console → IAM
2. Create new policy with the printed JSON
3. Attach to your IAM user/role

#### Step 3: Update Environment

```bash
# .env file
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
KNOWLEDGE_BASE_ID=your_kb_id
```

#### Step 4: Run Application

```bash
streamlit run app_aws.py
```

---

### How It Works

#### 1. User Registration
```
Register → Create FHIR Patient resource → Save to S3
Location: s3://health-companion-fhir-data/patients/{patient_id}/patient.json
```

#### 2. Document Upload
```
Upload Lab Report
  ↓
Textract Extraction
  ↓
Parse to FHIR (DiagnosticReport + Observations)
  ↓
Save to S3:
  - s3://.../patients/{patient_id}/diagnostic-reports/{report_id}.json
  - s3://.../patients/{patient_id}/observations/{obs_id}.json
  - s3://.../patients/{patient_id}/originals/{timestamp}_{filename}
  ↓
Save metadata to DynamoDB
```

#### 3. Data Retrieval
```
User asks: "Compare my reports"
  ↓
Query DynamoDB for document list
  ↓
Retrieve FHIR resources from S3
  ↓
Parse and compare
  ↓
AI generates explanation
```

---

### FHIR Data Structure

#### Patient Resource
```json
{
  "resourceType": "Patient",
  "id": "patient-123",
  "name": [{"text": "John Doe"}],
  "telecom": [{"system": "email", "value": "john@example.com"}]
}
```

#### DiagnosticReport Resource
```json
{
  "resourceType": "DiagnosticReport",
  "id": "report-456",
  "subject": {"reference": "Patient/patient-123"},
  "effectiveDateTime": "2024-01-15",
  "result": [{"reference": "Observation/obs-789"}]
}
```

#### Observation Resource
```json
{
  "resourceType": "Observation",
  "id": "obs-789",
  "code": {"text": "Hemoglobin"},
  "valueQuantity": {"value": 14.5, "unit": "g/dL"},
  "referenceRange": [{"text": "13.5-17.5"}],
  "interpretation": [{"coding": [{"code": "normal"}]}]
}
```

---

### S3 Folder Structure

```
health-companion-fhir-data/
├── patients/
│   ├── patient-123/
│   │   ├── patient.json                    # Patient profile
│   │   ├── diagnostic-reports/
│   │   │   ├── report-456.json            # Lab report
│   │   │   └── report-789.json
│   │   ├── observations/
│   │   │   ├── obs-111.json               # Individual test
│   │   │   ├── obs-222.json
│   │   │   └── obs-333.json
│   │   └── originals/
│   │       ├── 2024-01-15_lab_report.pdf  # Original files
│   │       └── 2024-02-20_blood_test.jpg
│   └── patient-456/
│       └── ...
```

---

### DynamoDB Tables

#### HealthCompanionUsers
```
user_id (PK) | patient_id | username | email | document_count | created_at
```

#### MedicalDocuments
```
user_id (PK) | document_id (SK) | doc_hash | s3_fhir_key | upload_timestamp
```

---

### Features

✅ **Automatic Patient Profile Creation**
- FHIR Patient resource created on registration
- Stored in S3 with unique patient ID

✅ **FHIR-Compliant Data Storage**
- All medical data in standard FHIR format
- Interoperable with other healthcare systems

✅ **Duplicate Detection**
- MD5 hash prevents duplicate uploads
- Indexed in DynamoDB for fast lookup

✅ **Report Comparison**
- Retrieve last 2 reports from S3
- Calculate changes in test values
- Show trends (↑ UP, ↓ DOWN, → SAME)

✅ **Secure Storage**
- S3 encryption at rest
- Versioning enabled
- Lifecycle policies for cost optimization

---

### Cost Estimation (Monthly)

- **S3**: $0.023/GB (~$0.50 for 100 patients)
- **DynamoDB**: Pay-per-request (~$1.25 for 1M requests)
- **Textract**: $1.50/1000 pages (~$1.50 for 100 reports)
- **Bedrock**: $0.003/1K tokens (~$5 for 1M tokens)

**Total**: ~$10-20/month for 100 active users

---

### Next Steps

1. ✅ Setup AWS infrastructure
2. ✅ Test with sample lab reports
3. 🔄 Integrate AWS Bedrock Agent (optional)
4. 🔄 Add AWS HealthLake for advanced queries
5. 🔄 Implement AWS Comprehend Medical for entity extraction

---

### Troubleshooting

**Error: "Access Denied"**
- Check IAM policy is attached
- Verify AWS credentials in .env

**Error: "Bucket does not exist"**
- Run setup_aws_infrastructure.py
- Check bucket name matches in code

**Error: "Table not found"**
- DynamoDB tables not created
- Run setup script again

---

### Production Enhancements

1. **AWS Cognito** - Replace simple auth
2. **AWS Lambda** - Serverless processing
3. **AWS HealthLake** - Advanced FHIR queries
4. **AWS Comprehend Medical** - Entity extraction
5. **AWS CloudWatch** - Monitoring & alerts
6. **AWS KMS** - Enhanced encryption
7. **AWS CloudFront** - CDN for faster access

---

Your health data is now stored in AWS using industry-standard FHIR format! 🎉
