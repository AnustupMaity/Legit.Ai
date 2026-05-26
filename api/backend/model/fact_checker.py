from __future__ import annotations

import json
import os
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

import config


# Simple in-memory knowledge base (in production, use a proper vector database)
_knowledge_base: list[dict] = []
_embedding_model = None
_load_error: str | None = None


def load_embedding_model() -> bool:
    """Load the sentence transformer model for embeddings."""
    global _embedding_model, _load_error
    if _embedding_model is not None:
        return True
    
    try:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device="cpu")
        _load_error = None
        return True
    except Exception as exc:
        _load_error = str(exc)
        _embedding_model = None
        return False


def is_embedding_model_loaded() -> bool:
    return _embedding_model is not None


def get_embedding_load_error() -> str | None:
    return _load_error


def initialize_knowledge_base() -> bool:
    """
    Initialize the knowledge base with sample fact-checked articles.
    In production, this would load from a database or API.
    """
    global _knowledge_base
    
    # Sample knowledge base (in production, load from Wikipedia, news archives, etc.)
    sample_articles = [
        {
            "id": 1,
            "title": "Climate Change Scientific Consensus",
            "content": "Scientific consensus on climate change is that Earth's climate is warming due to human activities, primarily greenhouse gas emissions.",
            "source": "IPCC",
            "url": "https://www.ipcc.ch",
            "category": "science",
            "reliability": 0.98
        },
        {
            "id": 2,
            "title": "Vaccine Safety and Efficacy",
            "content": "Extensive clinical trials and post-market monitoring have established that vaccines are safe and effective for preventing infectious diseases.",
            "source": "WHO",
            "url": "https://www.who.int",
            "category": "health",
            "reliability": 0.97
        },
        {
            "id": 3,
            "title": "Moon Landing Historical Fact",
            "content": "The Apollo 11 mission landed on the Moon on July 20, 1969, with Neil Armstrong becoming the first human to walk on the lunar surface.",
            "source": "NASA",
            "url": "https://www.nasa.gov",
            "category": "history",
            "reliability": 0.99
        },
        {
            "id": 4,
            "title": "Earth Shape Scientific Consensus",
            "content": "The Earth is an oblate spheroid, approximately spherical but slightly flattened at the poles and bulging at the equator.",
            "source": "Scientific Consensus",
            "url": "https://nssdc.gsfc.nasa.gov",
            "category": "science",
            "reliability": 0.99
        },
        {
            "id": 5,
            "title": "5G Network Technology",
            "content": "5G is the fifth generation of mobile networks, offering faster speeds and lower latency than previous generations, but does not cause COVID-19.",
            "source": "ITU",
            "url": "https://www.itu.int",
            "category": "technology",
            "reliability": 0.95
        }
    ]
    
    _knowledge_base = sample_articles
    return True


def get_knowledge_base() -> list[dict]:
    """Return the current knowledge base."""
    return _knowledge_base


def add_to_knowledge_base(article: dict) -> None:
    """Add an article to the knowledge base."""
    article["id"] = len(_knowledge_base) + 1
    _knowledge_base.append(article)


def compute_embedding(text: str) -> np.ndarray | None:
    """Compute embedding for a given text."""
    if not load_embedding_model() or _embedding_model is None:
        return None
    
    try:
        return _embedding_model.encode(text, convert_to_numpy=True)
    except Exception as exc:
        print(f"Embedding computation failed: {exc}")
        return None


def compute_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Compute cosine similarity between two embeddings."""
    try:
        # Cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)
    except Exception as exc:
        print(f"Similarity computation failed: {exc}")
        return 0.0


def search_knowledge_base(query: str, top_k: int = 3) -> list[dict]:
    """
    Search the knowledge base for articles similar to the query.
    
    Args:
        query: The query text
        top_k: Number of top results to return
    
    Returns:
        List of relevant articles with similarity scores
    """
    if not _knowledge_base:
        return []
    
    query_embedding = compute_embedding(query)
    if query_embedding is None:
        return []
    
    # Compute similarities for all articles
    results = []
    for article in _knowledge_base:
        # Combine title and content for better matching
        article_text = f"{article.get('title', '')} {article.get('content', '')}"
        article_embedding = compute_embedding(article_text)
        
        if article_embedding is not None:
            similarity = compute_similarity(query_embedding, article_embedding)
            results.append({
                **article,
                "similarity_score": similarity
            })
    
    # Sort by similarity and return top_k
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:top_k]


def check_facts(text: str) -> dict:
    """
    Check the factual consistency of the given text against the knowledge base.
    
    Args:
        text: The text to check
    
    Returns:
        Fact checking result with sources and analysis
    """
    if not _knowledge_base:
        initialize_knowledge_base()
    
    # Search for relevant articles
    relevant_articles = search_knowledge_base(text, top_k=3)
    
    if not relevant_articles:
        return {
            "fact_check_available": False,
            "reason": "No relevant articles found in knowledge base",
            "sources": [],
            "overall_reliability": 0.5,
        }
    
    # Analyze results
    avg_similarity = np.mean([article["similarity_score"] for article in relevant_articles])
    avg_reliability = np.mean([article.get("reliability", 0.5) for article in relevant_articles])
    
    # Determine if content is factually consistent
    # High similarity with reliable sources suggests factual consistency
    factually_consistent = avg_similarity > 0.6 and avg_reliability > 0.7
    
    # Format sources
    sources = [
        {
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "url": article.get("url", ""),
            "similarity": round(article["similarity_score"], 3),
            "reliability": article.get("reliability", 0.5)
        }
        for article in relevant_articles
    ]
    
    return {
        "fact_check_available": True,
        "factually_consistent": factually_consistent,
        "overall_similarity": round(avg_similarity, 3),
        "overall_reliability": round(avg_reliability, 3),
        "sources": sources,
        "analysis": f"Found {len(relevant_articles)} relevant articles with average similarity {avg_similarity:.3f}. "
                   f"Content appears {'factually consistent' if factually_consistent else 'potentially inconsistent'} with reliable sources."
    }


def integrate_fact_check(detection_result: dict, text: str) -> dict:
    """
    Integrate fact checking results with the detection result.
    
    Args:
        detection_result: Original detection result
        text: The text that was analyzed
    
    Returns:
        Enhanced detection result with fact checking
    """
    fact_check = check_facts(text)
    
    # Add fact checking to labels
    fact_check_labels = []
    if fact_check["fact_check_available"]:
        if fact_check["factually_consistent"]:
            fact_check_labels.append({"label": "factually-consistent", "score": fact_check["overall_reliability"]})
        else:
            fact_check_labels.append({"label": "potentially-inaccurate", "score": 1.0 - fact_check["overall_similarity"]})
    
    # Update result
    enhanced_result = {
        **detection_result,
        "labels": detection_result.get("labels", []) + fact_check_labels,
        "fact_check": fact_check,
    }
    
    # Adjust confidence based on fact checking
    if fact_check["fact_check_available"]:
        if not fact_check["factually_consistent"] and detection_result.get("fake"):
            # Boost confidence if both classifier and fact check agree it's fake
            enhanced_result["confidence"] = min(99.0, enhanced_result["confidence"] + 10)
            enhanced_result["reason"] += f" Fact check confirms potential inaccuracy."
        elif fact_check["factually_consistent"] and detection_result.get("fake"):
            # Reduce confidence if fact check disagrees
            enhanced_result["confidence"] = max(5.0, enhanced_result["confidence"] - 15)
            enhanced_result["reason"] += f" However, fact check finds similar reliable sources."
    
    return enhanced_result
