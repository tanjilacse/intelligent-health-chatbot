"""Script to setup AWS infrastructure for Health Companion."""

import boto3
import json


def setup_s3_bucket(bucket_name='health-companion-fhir-data', region='us-west-2'):
    """Create S3 bucket with proper structure."""
    s3 = boto3.client('s3', region_name=region)
    
    try:
        # Create bucket with location constraint for non-us-east-1 regions
        if region == 'us-east-1':
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        print(f"✅ Created S3 bucket: {bucket_name} in {region}")
        
        # Enable versioning
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print("✅ Enabled versioning")
        
        # Enable encryption
        s3.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [{
                    'ApplyServerSideEncryptionByDefault': {
                        'SSEAlgorithm': 'AES256'
                    }
                }]
            }
        )
        print("✅ Enabled encryption")
        
        # Set lifecycle policy
        s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={
                'Rules': [{
                    'ID': 'MoveOldReportsToIA',
                    'Status': 'Enabled',
                    'Transitions': [{
                        'Days': 90,
                        'StorageClass': 'STANDARD_IA'
                    }],
                    'Filter': {'Prefix': 'patients/'}
                }]
            }
        )
        print("✅ Set lifecycle policy")
        
    except Exception as e:
        print(f"❌ Error creating S3 bucket: {e}")


def setup_dynamodb_tables():
    """Create DynamoDB tables."""
    dynamodb = boto3.client('dynamodb')
    
    # Users table
    try:
        dynamodb.create_table(
            TableName='HealthCompanionUsers',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("✅ Created HealthCompanionUsers table")
    except Exception as e:
        print(f"⚠️  HealthCompanionUsers table: {e}")
    
    # Documents table
    try:
        dynamodb.create_table(
            TableName='MedicalDocuments',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'document_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'document_id', 'AttributeType': 'S'},
                {'AttributeName': 'doc_hash', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[{
                'IndexName': 'user_id-doc_hash-index',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'doc_hash', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }],
            BillingMode='PAY_PER_REQUEST'
        )
        print("✅ Created MedicalDocuments table")
    except Exception as e:
        print(f"⚠️  MedicalDocuments table: {e}")


def setup_iam_policy():
    """Print IAM policy for the application."""
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    "arn:aws:s3:::health-companion-fhir-data",
                    "arn:aws:s3:::health-companion-fhir-data/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                    "dynamodb:UpdateItem"
                ],
                "Resource": [
                    "arn:aws:dynamodb:*:*:table/HealthCompanionUsers",
                    "arn:aws:dynamodb:*:*:table/MedicalDocuments",
                    "arn:aws:dynamodb:*:*:table/MedicalDocuments/index/*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "textract:DetectDocumentText",
                    "textract:AnalyzeDocument"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:Retrieve"
                ],
                "Resource": [
                    "arn:aws:bedrock:*::foundation-model/*",
                    "arn:aws:bedrock:*:*:knowledge-base/*"
                ]
            }
        ]
    }
    
    print("\n📋 IAM Policy (attach to your IAM user/role):")
    print(json.dumps(policy, indent=2))


if __name__ == "__main__":
    print("🚀 Setting up AWS Infrastructure for Health Companion\n")
    
    setup_s3_bucket()
    print()
    setup_dynamodb_tables()
    print()
    setup_iam_policy()
    
    print("\n✅ Setup complete!")
    print("\n📝 Next steps:")
    print("1. Attach the IAM policy to your AWS credentials")
    print("2. Update .env with your AWS credentials")
    print("3. Run: streamlit run app.py")
