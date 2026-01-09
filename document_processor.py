import os
from pathlib import Path
from typing import List, Dict

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader
import docx
import re


class DocumentProcessor:
    """Handles document ingestion and intelligent chunking"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document processor

        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}"
        except Exception as e:
            raise Exception(f"Error reading PDF {file_path}: {str(e)}")
        return text

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX {file_path}: {str(e)}")

    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error reading TXT {file_path}: {str(e)}")

    def extract_text(self, file_path: str) -> str:
        """Extract text based on file extension"""
        extension = Path(file_path).suffix.lower()

        if extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif extension == '.docx':
            return self.extract_text_from_docx(file_path)
        elif extension == '.txt':
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    def intelligent_chunk(self, text: str, source: str) -> List[Dict]:
        """
        Intelligently chunk text based on semantic boundaries

        Strategy:
        1. Split on double newlines (paragraph boundaries)
        2. Split on section headers (lines with all caps or numbered sections)
        3. Use sliding window for large paragraphs
        4. Maintain overlap between chunks for context continuity
        """
        chunks = []

        # Clean text
        text = re.sub(r'\n{3,}', '\n\n', text)  # Normalize multiple newlines
        text = re.sub(r' {2,}', ' ', text)  # Normalize spaces

        # First, try to split on clear section boundaries
        # Look for patterns like "1.", "Section 1:", "LEAVE POLICY", etc.
        section_pattern = r'\n(?=(?:\d+\.|\d+\)|\w+\s+\d+:|[A-Z][A-Z\s]{5,}:))'
        sections = re.split(section_pattern, text)

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # If section is small enough, keep it as one chunk
            if len(section) <= self.chunk_size:
                chunks.append({
                    'text': section,
                    'metadata': {
                        'source': source,
                        'chunk_type': 'section'
                    }
                })
            else:
                # Split large sections into paragraphs
                paragraphs = section.split('\n\n')
                current_chunk = ""

                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    if not paragraph:
                        continue

                    # If adding this paragraph exceeds chunk size
                    if len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                        if current_chunk:
                            chunks.append({
                                'text': current_chunk.strip(),
                                'metadata': {
                                    'source': source,
                                    'chunk_type': 'paragraph_group'
                                }
                            })

                        # Start new chunk with overlap from previous
                        if self.chunk_overlap > 0 and current_chunk:
                            overlap_text = current_chunk[-self.chunk_overlap:]
                            current_chunk = overlap_text + "\n\n" + paragraph
                        else:
                            current_chunk = paragraph
                    else:
                        # Add paragraph to current chunk
                        if current_chunk:
                            current_chunk += "\n\n" + paragraph
                        else:
                            current_chunk = paragraph

                # Add remaining chunk
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'metadata': {
                            'source': source,
                            'chunk_type': 'paragraph_group'
                        }
                    })

        return chunks

    def process_documents(self, file_paths: List[str]) -> List[Dict]:
        """
        Process multiple documents and return chunks

        Args:
            file_paths: List of file paths to process

        Returns:
            List of chunk dictionaries with text and metadata
        """
        all_chunks = []

        for file_path in file_paths:
            try:
                # Extract text
                text = self.extract_text(file_path)

                # Chunk text
                chunks = self.intelligent_chunk(text, Path(file_path).name)
                all_chunks.extend(chunks)

            except Exception as e:
                print(f"Warning: Could not process {file_path}: {str(e)}")
                continue

        return all_chunks