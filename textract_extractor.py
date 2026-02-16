"""Amazon Textract module for robust text extraction from medical documents."""

import boto3
from typing import Dict, List
from config import AWS_REGION


class TextractExtractor:
    """Extracts text and structured data from medical documents using AWS Textract."""
    
    def __init__(self):
        """Initialize Textract client."""
        self.client = boto3.client('textract', region_name=AWS_REGION)
    
    def extract_text(self, image_data: bytes) -> str:
        """
        Extract all text from document image using Textract.
        
        Args:
            image_data: Binary image data
            
        Returns:
            Extracted text content
        """
        response = self.client.detect_document_text(
            Document={'Bytes': image_data}
        )
        
        # Combine all detected text
        text_lines = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_lines.append(block['Text'])
        
        return '\n'.join(text_lines)
    
    def extract_structured_data(self, image_data: bytes) -> Dict:
        """
        Extract structured data (key-value pairs, tables) from medical documents.
        
        Args:
            image_data: Binary image data
            
        Returns:
            Dictionary with extracted text, key-value pairs, and tables
        """
        response = self.client.analyze_document(
            Document={'Bytes': image_data},
            FeatureTypes=['FORMS', 'TABLES']
        )
        
        blocks = response.get('Blocks', [])
        
        # Extract raw text
        text_lines = []
        key_value_pairs = {}
        tables = []
        
        # Build block map for relationships
        block_map = {block['Id']: block for block in blocks}
        
        # Extract text lines
        for block in blocks:
            if block['BlockType'] == 'LINE':
                text_lines.append(block['Text'])
        
        # Extract key-value pairs (forms)
        for block in blocks:
            if block['BlockType'] == 'KEY_VALUE_SET':
                if 'KEY' in block.get('EntityTypes', []):
                    key_text = self._get_text_from_block(block, block_map)
                    value_block = self._get_value_block(block, block_map)
                    if value_block:
                        value_text = self._get_text_from_block(value_block, block_map)
                        if key_text and value_text:
                            key_value_pairs[key_text] = value_text
        
        # Extract tables
        table_blocks = [b for b in blocks if b['BlockType'] == 'TABLE']
        for table_block in table_blocks:
            table_data = self._extract_table(table_block, block_map)
            if table_data:
                tables.append(table_data)
        
        return {
            'raw_text': '\n'.join(text_lines),
            'key_value_pairs': key_value_pairs,
            'tables': tables
        }
    
    def _get_text_from_block(self, block: Dict, block_map: Dict) -> str:
        """Extract text from a block using relationships."""
        text = ''
        if 'Relationships' in block:
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        child_block = block_map.get(child_id)
                        if child_block and child_block['BlockType'] == 'WORD':
                            text += child_block['Text'] + ' '
        return text.strip()
    
    def _get_value_block(self, key_block: Dict, block_map: Dict) -> Dict:
        """Get the value block associated with a key block."""
        if 'Relationships' in key_block:
            for relationship in key_block['Relationships']:
                if relationship['Type'] == 'VALUE':
                    for value_id in relationship['Ids']:
                        return block_map.get(value_id)
        return None
    
    def _extract_table(self, table_block: Dict, block_map: Dict) -> List[List[str]]:
        """Extract table data as 2D array."""
        if 'Relationships' not in table_block:
            return []
        
        cells = {}
        for relationship in table_block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for cell_id in relationship['Ids']:
                    cell_block = block_map.get(cell_id)
                    if cell_block and cell_block['BlockType'] == 'CELL':
                        row = cell_block.get('RowIndex', 0)
                        col = cell_block.get('ColumnIndex', 0)
                        text = self._get_text_from_block(cell_block, block_map)
                        cells[(row, col)] = text
        
        if not cells:
            return []
        
        # Convert to 2D array
        max_row = max(r for r, c in cells.keys())
        max_col = max(c for r, c in cells.keys())
        
        table = []
        for row in range(1, max_row + 1):
            row_data = []
            for col in range(1, max_col + 1):
                row_data.append(cells.get((row, col), ''))
            table.append(row_data)
        
        return table
