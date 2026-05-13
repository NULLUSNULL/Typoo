"""
Markdown utilities and processing.
"""

import re
from typing import List, Tuple


class MarkdownUtils:
    """Utilities for Markdown processing."""
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        # Remove code blocks and inline code
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]*`', '', text)
        # Remove markdown syntax
        text = re.sub(r'[#*_`\[\]()!-]', ' ', text)
        # Split by whitespace and filter
        words = [w for w in text.split() if w.strip()]
        return len(words)
    
    @staticmethod
    def extract_headings(text: str) -> List[Tuple[int, str]]:
        """
        Extract headings with their levels.
        
        Returns:
            List of tuples (level, heading_text)
        """
        headings = []
        for line in text.split('\n'):
            match = re.match(r'^(#+)\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text_content = match.group(2).strip()
                headings.append((level, text_content))
        return headings
    
    @staticmethod
    def markdown_to_plain_text(text: str) -> str:
        """Convert Markdown to plain text."""
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove links
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Remove images
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
        # Remove bold and italic
        text = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', text)
        # Remove headings
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        # Remove horizontal rules
        text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
        return text.strip()
    
    @staticmethod
    def get_markdown_stats(text: str) -> dict:
        """Get statistics for markdown text."""
        lines = text.split('\n')
        headings = MarkdownUtils.extract_headings(text)
        
        return {
            'words': MarkdownUtils.count_words(text),
            'characters': len(text),
            'lines': len(lines),
            'headings': len(headings),
            'paragraphs': len([l for l in lines if l.strip()])
        }
