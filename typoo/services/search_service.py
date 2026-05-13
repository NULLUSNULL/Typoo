"""
Search service for finding text in projects.
"""

import re
from typing import List, Tuple, Optional
from pathlib import Path

from typoo.logger import Logger
from typoo.models import Project, Document

logger = Logger.get()


class SearchResult:
    """Represents a search result."""
    
    def __init__(self, document: Document, line_number: int, line_text: str, match_start: int, match_end: int):
        self.document = document
        self.line_number = line_number
        self.line_text = line_text
        self.match_start = match_start
        self.match_end = match_end


class SearchService:
    """Service for searching within projects."""
    
    @staticmethod
    def search_in_document(document: Document, query: str, use_regex: bool = False, 
                          case_sensitive: bool = False) -> List[SearchResult]:
        """
        Search within a single document.
        
        Args:
            document: Document to search in
            query: Search query
            use_regex: Whether to use regex search
            case_sensitive: Whether search is case sensitive
            
        Returns:
            List of search results
        """
        results = []
        
        if not document.content:
            return results
        
        try:
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(query, flags)
            else:
                if not case_sensitive:
                    query = query.lower()
            
            lines = document.content.split('\n')
            for line_num, line in enumerate(lines, 1):
                if use_regex:
                    matches = pattern.finditer(line)
                    for match in matches:
                        results.append(SearchResult(
                            document, line_num, line,
                            match.start(), match.end()
                        ))
                else:
                    search_line = line if case_sensitive else line.lower()
                    start = 0
                    while True:
                        pos = search_line.find(query, start)
                        if pos == -1:
                            break
                        results.append(SearchResult(
                            document, line_num, line,
                            pos, pos + len(query)
                        ))
                        start = pos + 1
        
        except Exception as e:
            logger.error(f"Search error in document {document.name}: {str(e)}")
        
        return results
    
    @staticmethod
    def search_in_project(project: Project, query: str, use_regex: bool = False,
                         case_sensitive: bool = False, max_results: int = 1000) -> List[SearchResult]:
        """
        Search throughout entire project.
        
        Args:
            project: Project to search in
            query: Search query
            use_regex: Whether to use regex search
            case_sensitive: Whether search is case sensitive
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        results = []
        
        def search_recursive(document: Document) -> None:
            if len(results) >= max_results:
                return
            
            doc_results = SearchService.search_in_document(
                document, query, use_regex, case_sensitive
            )
            results.extend(doc_results[:max_results - len(results)])
            
            for child in document.children:
                search_recursive(child)
        
        for document in project.documents:
            search_recursive(document)
        
        logger.debug(f"Search completed: found {len(results)} results")
        return results
    
    @staticmethod
    def replace_in_document(document: Document, query: str, replacement: str,
                           use_regex: bool = False, case_sensitive: bool = False,
                           replace_all: bool = False) -> Tuple[str, int]:
        """
        Replace text in a document.
        
        Args:
            document: Document to modify
            query: Text to search for
            replacement: Text to replace with
            use_regex: Whether to use regex replacement
            case_sensitive: Whether search is case sensitive
            replace_all: Whether to replace all occurrences
            
        Returns:
            Tuple of (modified_content, number_replaced)
        """
        try:
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                count = 0 if replace_all else 1
                new_content, num_replaced = re.subn(
                    query, replacement, document.content, count=count, flags=flags
                )
            else:
                if not case_sensitive:
                    # Case-insensitive replacement
                    import string
                    parts = []
                    content = document.content
                    last_end = 0
                    
                    for match in re.finditer(re.escape(query), content, re.IGNORECASE):
                        parts.append(content[last_end:match.start()])
                        parts.append(replacement)
                        last_end = match.end()
                    
                    parts.append(content[last_end:])
                    new_content = "".join(parts)
                    num_replaced = len([m for m in re.finditer(re.escape(query), content, re.IGNORECASE)])
                    if not replace_all and num_replaced > 1:
                        new_content = content.replace(query, replacement, 1)
                        num_replaced = 1
                else:
                    count = -1 if replace_all else 1
                    new_content = document.content.replace(query, replacement, count)
                    num_replaced = document.content.count(query)
            
            document.content = new_content
            logger.debug(f"Replaced {num_replaced} occurrences in {document.name}")
            return new_content, num_replaced
        
        except Exception as e:
            logger.error(f"Replace error: {str(e)}")
            return document.content, 0
