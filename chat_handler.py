"""Chat handler module for managing patient conversations."""

from bedrock_client import BedrockClient
from config import KNOWLEDGE_BASE_ENABLED


class ChatHandler:
    """Manages conversational interactions with patients."""
    
    def __init__(self):
        """Initialize with Bedrock client."""
        self.bedrock = BedrockClient()
        self.system_prompt = """You are a compassionate AI health companion assistant. Your role:

1. Interact with patients in a friendly, empathetic manner
2. Answer health-related questions clearly and simply
3. Provide general health information and wellness advice
4. Help patients understand their medical documents
5. Offer emotional support and encouragement

Important guidelines:
- Use simple, non-technical language
- Be warm and reassuring
- Never diagnose or replace professional medical advice
- Encourage patients to consult healthcare providers for serious concerns
- Maintain patient privacy and confidentiality"""
    
    def get_response(self, user_message: str, context: str = "") -> str:
        """
        Generate AI response to patient's message.
        
        Args:
            user_message: Patient's question or message
            context: Additional context (e.g., previous analysis)
            
        Returns:
            AI assistant's response
        """
        prompt = user_message
        if context:
            prompt = f"Context: {context}\n\nPatient: {user_message}"
        
        # Use knowledge base if enabled, otherwise standard text invocation
        if KNOWLEDGE_BASE_ENABLED:
            return self.bedrock.invoke_with_knowledge_base(
                prompt=prompt,
                system_prompt=self.system_prompt
            )
        else:
            return self.bedrock.invoke_text(
                prompt=prompt,
                system_prompt=self.system_prompt
            )
