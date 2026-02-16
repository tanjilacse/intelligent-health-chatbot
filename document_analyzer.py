"""Document analysis module for categorizing and processing medical documents."""

from bedrock_client import BedrockClient
from textract_extractor import TextractExtractor
from config import DOCUMENT_CATEGORIES


class DocumentAnalyzer:
    """Analyzes and categorizes medical documents and images."""
    
    def __init__(self):
        """Initialize with Bedrock client and Textract extractor."""
        self.bedrock = BedrockClient()
        self.textract = TextractExtractor()
    
    def categorize_document(self, image_data: bytes, media_type: str) -> dict:
        """
        Categorize uploaded medical document by analyzing its content.
        
        Args:
            image_data: Binary image data
            media_type: Image MIME type
            
        Returns:
            Dictionary with category and confidence
        """
        # First extract text using Textract
        extracted_text = self.textract.extract_text(image_data)
        
        # Use both image and extracted text for better categorization
        prompt = f"""Extracted text from document:
{extracted_text[:1000]}

Categorize this medical document into ONE of these types:
1. PRESCRIPTION - Contains medication names, dosages, doctor's signature
2. LAB_REPORT - Contains test results, lab values, pathology findings
3. MEDICAL_IMAGE - X-ray, MRI, CT scan, ultrasound, or other diagnostic imaging

Respond with ONLY: PRESCRIPTION, LAB_REPORT, or MEDICAL_IMAGE"""
        
        system_prompt = "You are a medical document classifier. Respond only with the category name."
        
        category = self.bedrock.invoke_text(
            prompt=prompt,
            system_prompt=system_prompt
        ).strip().upper()
        
        # Map to lowercase for consistency
        category_map = {
            'PRESCRIPTION': 'prescription',
            'LAB_REPORT': 'lab_report',
            'MEDICAL_IMAGE': 'medical_image'
        }
        
        return {
            'category': category_map.get(category, 'lab_report'),  # Default to lab_report if unclear
            'category_display': category
        }
    
    def explain_prescription(self, image_data: bytes, media_type: str) -> str:
        """
        Explain prescription details in patient-friendly language.
        
        Args:
            image_data: Binary prescription image
            media_type: Image MIME type
            
        Returns:
            Detailed explanation of the prescription
        """
        # Extract text using Textract for better accuracy
        extracted_data = self.textract.extract_structured_data(image_data)
        extracted_text = extracted_data['raw_text']
        key_values = extracted_data['key_value_pairs']
        
        # Build context from extracted data
        context = f"Extracted Text:\n{extracted_text}\n\n"
        if key_values:
            context += "Key Information:\n"
            for key, value in key_values.items():
                context += f"- {key}: {value}\n"
        
        prompt = f"""{context}

Based on the extracted prescription data above, explain:
1. Medications prescribed (names and purposes)
2. Dosage instructions in simple terms
3. Duration of treatment
4. Important precautions or side effects
5. When to take each medication

Use simple, patient-friendly language."""
        
        system_prompt = "You are a compassionate healthcare assistant explaining prescriptions to patients."
        
        return self.bedrock.invoke_text(
            prompt=prompt,
            system_prompt=system_prompt
        )
    
    def explain_lab_report(self, image_data: bytes, media_type: str) -> str:
        """
        Explain lab report results in understandable terms.
        
        Args:
            image_data: Binary lab report image
            media_type: Image MIME type
            
        Returns:
            Detailed explanation of lab results
        """
        # Extract structured data using Textract
        extracted_data = self.textract.extract_structured_data(image_data)
        extracted_text = extracted_data['raw_text']
        tables = extracted_data['tables']
        key_values = extracted_data['key_value_pairs']
        
        # Build context from extracted data
        context = f"Extracted Lab Report Data:\n{extracted_text}\n\n"
        
        if key_values:
            context += "Patient/Test Information:\n"
            for key, value in key_values.items():
                context += f"- {key}: {value}\n"
            context += "\n"
        
        if tables:
            context += "Lab Test Results (Tables):\n"
            for i, table in enumerate(tables, 1):
                context += f"Table {i}:\n"
                for row in table:
                    context += " | ".join(row) + "\n"
                context += "\n"
        
        prompt = f"""{context}

Based on the extracted lab report data above, explain:
1. What tests were performed
2. Key findings and values
3. Which values are normal vs abnormal
4. What abnormal values might indicate
5. General health implications

Use simple language that patients can understand."""
        
        system_prompt = "You are a healthcare assistant explaining lab results to patients in simple terms."
        
        return self.bedrock.invoke_text(
            prompt=prompt,
            system_prompt=system_prompt
        )
    
    def explain_medical_image(self, image_data: bytes, media_type: str) -> str:
        """
        Explain medical imaging results.
        
        Args:
            image_data: Binary medical image
            media_type: Image MIME type
            
        Returns:
            Explanation of the medical image
        """
        prompt = """Analyze this medical image and explain:
1. Type of imaging (X-ray, MRI, CT, etc.)
2. Body part or area being examined
3. Visible findings or abnormalities
4. What these findings might mean
5. General observations

Use simple, reassuring language."""
        
        system_prompt = "You are a healthcare assistant explaining medical images to patients."
        
        return self.bedrock.invoke_with_image(
            prompt=prompt,
            image_data=image_data,
            media_type=media_type,
            system_prompt=system_prompt
        )
    
    def analyze_document(self, image_data: bytes, media_type: str) -> dict:
        """
        Complete document analysis pipeline: categorize and explain.
        
        Args:
            image_data: Binary image data
            media_type: Image MIME type
            
        Returns:
            Dictionary with category and explanation
        """
        # Step 1: Categorize the document
        categorization = self.categorize_document(image_data, media_type)
        category = categorization['category']
        
        # Step 2: Generate appropriate explanation based on category
        try:
            if category == 'prescription':
                explanation = self.explain_prescription(image_data, media_type)
            elif category == 'lab_report':
                explanation = self.explain_lab_report(image_data, media_type)
            elif category == 'medical_image':
                explanation = self.explain_medical_image(image_data, media_type)
            else:
                # Fallback: try lab report analysis
                explanation = self.explain_lab_report(image_data, media_type)
        except Exception as e:
            # If Textract or analysis fails, use vision model as fallback
            explanation = self.bedrock.invoke_with_image(
                prompt="Analyze this medical document and explain all visible information in simple, patient-friendly terms.",
                image_data=image_data,
                media_type=media_type,
                system_prompt="You are a healthcare assistant explaining medical documents to patients."
            )
        
        return {
            'category': category,
            'category_display': categorization['category_display'],
            'explanation': explanation
        }
