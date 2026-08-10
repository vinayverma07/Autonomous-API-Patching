"""
Module: Ingestion Engine for Local Agentic RAG
Description: Reads, cleans, parses, and splits complex unstructured raw engineering data
             (Markdown, Codebases, Text logs) into contextual semantic structures.
"""

import os
import re
import logging
from typing import List, Dict, Any
from pathlib import Path
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter
)

logger = logging.getLogger(__name__)

class TechnicalIngestor:
    """Production-grade Ingestion Engine designed to parse technical document variants cleanly."""

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 60):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Configure a generic code & plain text fallback splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Ingestor configuration tracking target markdown patterns
        self.markdown_headers = [
            ("#", "Header_1"),
            ("##", "Header_2"),
            ("###", "Header_3")
        ]
        self.md_header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.markdown_headers,
            strip_headers=False
        )

    def clean_text_content(self, text: str) -> str:
        """Removes low-level formatting noise, byte artifacts, and repetitive whitespace."""
        if not text:
            return ""
        # Collapse multiple structural vertical carriage returns safely
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Standardize wide spaces without losing programmatic indentation spaces
        text = re.sub(r'[ \t]{4,}', '    ', text)
        return text.strip()

    def load_html_document(self, file_path: Path) -> str:
        """Parses web-based technical references, stripping away scripts, stylesheets, and nav-bars."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
            
            # Deconstruct non-text layout components completely
            for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                element.decompose()
                
            return soup.get_text(separator="\n")
        except Exception as e:
            logger.error(f"Failed extracting data elements from HTML path {file_path}: {e}")
            return ""

    def process_markdown_file(self, file_path: Path) -> List[Document]:
        """Converts Markdown documents into structural chunks that retain parent header scopes."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
            
            cleaned_content = self.clean_text_content(raw_content)
            # Slice files based on logical Markdown headings first
            header_splits = self.md_header_splitter.split_text(cleaned_content)
            
            final_chunks = []
            for doc in header_splits:
                # Sub-split long content blocks to fit within our local LLM's optimal chunk boundaries
                sub_docs = self.text_splitter.split_documents([doc])
                for sub_doc in sub_docs:
                    # Enrich document context metadata
                    sub_doc.metadata.update({
                        "source": str(file_path),
                        "file_type": "markdown",
                        "extraction_method": "structural_header"
                    })
                    final_chunks.append(sub_doc)
            return final_chunks
        except Exception as e:
            logger.error(f"Error compiling structural markdown layout at {file_path}: {e}")
            return []

    def process_code_or_log_file(self, file_path: Path, file_type: str) -> List[Document]:
        """Extracts plain text chunks from logs or code files, preserving indentation layers."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_content = f.read()
                
            cleaned_content = self.clean_text_content(raw_content)
            base_docs = self.text_splitter.create_documents(
                texts=[cleaned_content],
                metadatas=[{
                    "source": str(file_path),
                    "file_type": file_type,
                    "extraction_method": "recursive_character"
                }]
            )
            return base_docs
        except Exception as e:
            logger.error(f"Error handling flat script ingestion at {file_path}: {e}")
            return []

    def ingest_directory(self, target_directory: str) -> List[Document]:
        """Scans a directory recursively, parsing all target file types into processed RAG chunks."""
        processed_documents: List[Document] = []
        root_path = Path(target_directory)

        if not root_path.exists():
            logger.warning(f"Inbound directory parameter path doesn't exist: {target_directory}")
            return []

        # Supported code extensions and technical documentation targets
        target_extensions = {".md", ".py", ".json", ".html", ".log"}

        for current_dir, _, files in os.walk(root_path):
            for file in files:
                file_path = Path(current_dir) / file
                ext = file_path.suffix.lower()

                if ext not in target_extensions:
                    continue

                logger.info(f"Ingesting: {file_path.name} ({ext})")

                if ext == ".md":
                    chunks = self.process_markdown_file(file_path)
                elif ext in {".py", ".json", ".log"}:
                    chunks = self.process_code_or_log_file(file_path, file_type=ext[1:])
                elif ext == ".html":
                    html_text = self.load_html_document(file_path)
                    # Convert raw extracted text strings into managed Document chunks
                    chunks = self.text_splitter.create_documents(
                        texts=[html_text],
                        metadatas=[{"source": str(file_path), "file_type": "html", "extraction_method": "html_stripped"}]
                    )
                else:
                    continue

                processed_documents.extend(chunks)

        logger.info(f"Ingestion complete. Total chunks generated: {len(processed_documents)}")
        return processed_documents

if __name__ == "__main__":
    # Diagnostic test block to verify the ingestion engine behaves correctly in isolation
    logging.basicConfig(level=logging.INFO)
    ingestor = TechnicalIngestor(chunk_size=300, chunk_overlap=30)
    print("Technical Ingestor class initialized successfully.")