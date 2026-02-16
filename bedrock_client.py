"""AWS Bedrock client module for AI model interactions."""

import boto3
import json
import base64
from typing import Optional, List, Dict
from config import AWS_REGION, BEDROCK_MODEL_ID, MAX_TOKENS, TEMPERATURE, KNOWLEDGE_BASE_ID, KNOWLEDGE_BASE_ENABLED


class BedrockClient:
    """Handles all interactions with Amazon Bedrock AI models."""
    
    def __init__(self):
        """Initialize Bedrock runtime and agent runtime clients."""
        self.client = boto3.client('bedrock-runtime', region_name=AWS_REGION)
        self.agent_client = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
    
    def invoke_text(self, prompt: str, system_prompt: str = "") -> str:
        """
        Invoke Bedrock model with text-only input.
        
        Args:
            prompt: User's text prompt
            system_prompt: System instructions for the model
            
        Returns:
            Model's text response
        """
        messages = [{"role": "user", "content": prompt}]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": MAX_TOKENS,
            "messages": messages,
            "temperature": TEMPERATURE
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        response = self.client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body)
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
    
    def retrieve_from_knowledge_base(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Retrieve relevant information from Bedrock Knowledge Base.
        
        Args:
            query: Search query
            max_results: Maximum number of results to retrieve
            
        Returns:
            List of retrieved documents with content and metadata
        """
        if not KNOWLEDGE_BASE_ENABLED:
            return []
        
        response = self.agent_client.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={'text': query},
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': max_results
                }
            }
        )
        
        return response.get('retrievalResults', [])
    
    def invoke_with_knowledge_base(self, prompt: str, system_prompt: str = "") -> str:
        """
        Invoke model with knowledge base retrieval (RAG pattern).
        
        Args:
            prompt: User's question
            system_prompt: System instructions
            
        Returns:
            Model response enhanced with knowledge base context
        """
        # Retrieve relevant context from knowledge base
        retrieved_docs = self.retrieve_from_knowledge_base(prompt)
        
        # Build context from retrieved documents
        context = ""
        if retrieved_docs:
            context = "\n\nRelevant medical information from knowledge base:\n"
            for i, doc in enumerate(retrieved_docs, 1):
                content = doc.get('content', {}).get('text', '')
                context += f"\n[Source {i}]: {content}\n"
        
        # Combine prompt with retrieved context
        enhanced_prompt = f"{prompt}{context}"
        
        return self.invoke_text(enhanced_prompt, system_prompt)
    
    def invoke_with_image(self, prompt: str, image_data: bytes, 
                         media_type: str, system_prompt: str = "") -> str:
        """
        Invoke Bedrock model with image and text input.
        
        Args:
            prompt: User's text prompt
            image_data: Binary image data
            media_type: Image MIME type (e.g., 'image/jpeg')
            system_prompt: System instructions for the model
            
        Returns:
            Model's text response analyzing the image
        """
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": MAX_TOKENS,
            "messages": messages,
            "temperature": TEMPERATURE
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        response = self.client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(body)
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
