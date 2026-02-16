# Knowledge Base Integration Guide

## Overview
This chatbot integrates with Amazon Bedrock Knowledge Base to provide accurate medical information from your curated knowledge sources.

## Setup Steps

### 1. Create Knowledge Base in AWS Console

1. Go to **Amazon Bedrock Console** → **Knowledge Bases**
2. Click **Create knowledge base**
3. Configure:
   - **Name**: `medical-knowledge-base`
   - **Description**: Medical information for health chatbot
   - **IAM Role**: Create new or use existing

### 2. Add Data Source

1. Choose data source type:
   - **S3**: Upload medical documents, PDFs, text files
   - **Web Crawler**: Index medical websites
   - **Confluence/SharePoint**: Connect to existing knowledge repositories

2. For S3 data source:
   ```bash
   # Create S3 bucket
   aws s3 mb s3://medical-knowledge-base-docs
   
   # Upload medical documents
   aws s3 cp ./medical_docs/ s3://medical-knowledge-base-docs/ --recursive
   ```

3. Configure chunking strategy:
   - **Default chunking**: Automatic
   - **Fixed-size chunking**: 300 tokens with 20% overlap (recommended)

### 3. Configure Embeddings

1. Select embedding model:
   - **Recommended**: `amazon.titan-embed-text-v1`
   - **Alternative**: `cohere.embed-english-v3`

2. Choose vector database:
   - **Amazon OpenSearch Serverless** (recommended)
   - **Pinecone**
   - **Redis Enterprise Cloud**

### 4. Sync Knowledge Base

1. Click **Sync** to ingest documents
2. Wait for sync to complete (may take several minutes)
3. Copy the **Knowledge Base ID** (format: `XXXXXXXXXX`)

### 5. Configure Application

1. Add Knowledge Base ID to `.env`:
   ```bash
   KNOWLEDGE_BASE_ID=XXXXXXXXXX
   ```

2. Update IAM permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
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
   ```

## How It Works

### RAG (Retrieval-Augmented Generation) Pattern

1. **User asks question** → "What are the side effects of metformin?"
2. **System retrieves** → Searches knowledge base for relevant documents
3. **Context injection** → Adds retrieved information to prompt
4. **AI generates** → Claude responds with knowledge-base-backed answer

### Example Flow

```python
# User query
"What is the normal range for blood glucose?"

# System retrieves from KB
[Source 1]: Normal fasting blood glucose: 70-100 mg/dL
[Source 2]: Pre-diabetes range: 100-125 mg/dL
[Source 3]: Diabetes diagnosis: ≥126 mg/dL

# AI response (with KB context)
"Normal fasting blood glucose levels are between 70-100 mg/dL..."
```

## Knowledge Base Content Recommendations

### Medical Documents to Include

1. **Drug Information**
   - Medication guides
   - Side effects databases
   - Drug interaction charts

2. **Lab Test References**
   - Normal value ranges
   - Test interpretation guides
   - Pathology references

3. **Medical Conditions**
   - Disease descriptions
   - Symptom guides
   - Treatment protocols

4. **Health Guidelines**
   - CDC guidelines
   - WHO recommendations
   - Clinical practice guidelines

### Document Format Tips

- Use clear, structured text
- Include headers and sections
- Add metadata (date, source, category)
- Keep documents focused and concise
- Update regularly for accuracy

## Testing Knowledge Base

```python
# Test retrieval directly
from bedrock_client import BedrockClient

client = BedrockClient()
results = client.retrieve_from_knowledge_base("diabetes symptoms")

for doc in results:
    print(doc['content']['text'])
```

## Monitoring & Optimization

### Check Retrieval Quality

1. Test common queries
2. Review retrieved documents
3. Adjust chunking strategy if needed
4. Update knowledge base content

### Performance Tuning

- **numberOfResults**: Increase for more context (default: 5)
- **Chunking size**: Smaller chunks = more precise, larger = more context
- **Overlap**: 10-20% recommended for continuity

## Troubleshooting

### Knowledge Base Not Working

1. Verify `KNOWLEDGE_BASE_ID` in `.env`
2. Check IAM permissions include `bedrock:Retrieve`
3. Ensure knowledge base sync completed
4. Verify data source has documents

### Poor Retrieval Results

1. Improve document quality and structure
2. Adjust chunking parameters
3. Add more relevant documents
4. Use better search queries

### Cost Optimization

- Use appropriate chunk sizes
- Limit `numberOfResults` to necessary amount
- Cache frequent queries (future enhancement)
- Monitor usage in CloudWatch

## Security Best Practices

1. **Data Privacy**: Only upload de-identified medical information
2. **Access Control**: Use IAM roles with least privilege
3. **Encryption**: Enable encryption at rest and in transit
4. **Audit**: Enable CloudTrail logging
5. **Compliance**: Ensure HIPAA compliance if handling PHI

## Next Steps

1. Create and populate knowledge base
2. Add Knowledge Base ID to `.env`
3. Test with sample queries
4. Monitor and refine content
5. Expand knowledge base over time
