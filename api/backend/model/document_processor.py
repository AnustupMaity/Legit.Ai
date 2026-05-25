from __future__ import annotations

import io
import os
from typing import List

import config


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF file bytes.
    
    Args:
        file_bytes: PDF file content
    
    Returns:
        Extracted text content
    """
    try:
        import pypdf
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except ImportError:
        raise ImportError("pypdf library not installed. Install with: pip install pypdf")
    except Exception as exc:
        raise Exception(f"PDF text extraction failed: {str(exc)}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extract text from DOCX file bytes.
    
    Args:
        file_bytes: DOCX file content
    
    Returns:
        Extracted text content
    """
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except ImportError:
        raise ImportError("python-docx library not installed. Install with: pip install python-docx")
    except Exception as exc:
        raise Exception(f"DOCX text extraction failed: {str(exc)}")


def extract_text_from_txt(file_bytes: bytes) -> str:
    """
    Extract text from plain text file bytes.
    
    Args:
        file_bytes: Text file content
    
    Returns:
        Extracted text content
    """
    try:
        return file_bytes.decode('utf-8').strip()
    except UnicodeDecodeError:
        try:
            return file_bytes.decode('latin-1').strip()
        except Exception as exc:
            raise Exception(f"Text file decoding failed: {str(exc)}")


def extract_text_from_document(file_bytes: bytes, filename: str) -> dict:
    """
    Extract text from various document formats.
    
    Args:
        file_bytes: Document file content
        filename: Original filename to determine format
    
    Returns:
        Dictionary with extracted text and metadata
    """
    if not filename:
        return {
            "success": False,
            "text": "",
            "error": "No filename provided to determine document type"
        }
    
    filename_lower = filename.lower()
    
    try:
        if filename_lower.endswith('.pdf'):
            text = extract_text_from_pdf(file_bytes)
            doc_type = "pdf"
        elif filename_lower.endswith('.docx'):
            text = extract_text_from_docx(file_bytes)
            doc_type = "docx"
        elif filename_lower.endswith('.txt'):
            text = extract_text_from_txt(file_bytes)
            doc_type = "txt"
        else:
            return {
                "success": False,
                "text": "",
                "error": f"Unsupported document type: {filename}"
            }
        
        if not text or len(text.strip()) < 10:
            return {
                "success": False,
                "text": "",
                "error": "Could not extract sufficient text from document"
            }
        
        return {
            "success": True,
            "text": text,
            "doc_type": doc_type,
            "char_count": len(text),
            "word_count": len(text.split()),
        }
        
    except Exception as exc:
        return {
            "success": False,
            "text": "",
            "error": f"Document extraction failed: {str(exc)}"
        }


def detect_document(file_bytes: bytes, filename: str, detection_fn) -> dict:
    """
    Analyze document for misinformation by extracting text and running detection.
    
    Args:
        file_bytes: Document file content
        filename: Original filename
        detection_fn: Function to run text detection (e.g., fake_detection.detect)
    
    Returns:
        Detection result with document analysis
    """
    # Extract text from document
    extraction_result = extract_text_from_document(file_bytes, filename)
    
    if not extraction_result["success"]:
        return {
            "fake": False,
            "confidence": 0.0,
            "reason": extraction_result.get("error", "Document extraction failed"),
            "model": "document-processor",
            "labels": [],
            "doc_analysis": extraction_result
        }
    
    text = extraction_result["text"]
    doc_type = extraction_result["doc_type"]
    
    # Run text detection on extracted content
    try:
        detection_result = detection_fn(text, type_="text")
        
        # Add document-specific metadata
        detection_result["doc_analysis"] = {
            "doc_type": doc_type,
            "char_count": extraction_result["char_count"],
            "word_count": extraction_result["word_count"],
            "extracted_text_preview": text[:200] + "..." if len(text) > 200 else text
        }
        
        detection_result["labels"] = [
            {"label": f"document:{doc_type}", "score": 1.0},
            *detection_result.get("labels", [])
        ]
        
        detection_result["reason"] = f"Analyzed {doc_type} document ({extraction_result['word_count']} words). {detection_result['reason']}"
        
        return detection_result
        
    except Exception as exc:
        return {
            "fake": False,
            "confidence": 0.0,
            "reason": f"Document detection failed: {str(exc)}",
            "model": "document-processor",
            "labels": [],
            "doc_analysis": extraction_result
        }


def analyze_document_batch(file_bytes_list: list[bytes], filename_list: list[str], detection_fn) -> list[dict]:
    """
    Analyze multiple documents in batch.
    
    Args:
        file_bytes_list: List of document file contents
        filename_list: List of corresponding filenames
        detection_fn: Function to run text detection
    
    Returns:
        List of detection results for each document
    """
    if len(file_bytes_list) != len(filename_list):
        raise ValueError("file_bytes_list and filename_list must have the same length")
    
    results = []
    for file_bytes, filename in zip(file_bytes_list, filename_list):
        result = detect_document(file_bytes, filename, detection_fn)
        results.append(result)
    
    return results
