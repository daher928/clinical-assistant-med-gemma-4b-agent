"""
Clinical guidelines tool for retrieving evidence-based treatment protocols.
"""
import glob
import time
import random
import os
from typing import List, Dict
from config import Config


def search_guidelines(keyword: str) -> List[Dict]:
    """
    Search clinical guidelines for a specific keyword or condition.
    
    Args:
        keyword: Medical condition, symptom, or treatment to search for
        
    Returns:
        List of guideline dictionaries with title, snippet, and source
    """
    # Simulate network delay
    time.sleep(random.uniform(0.3, 0.8))
    
    results = []
    pattern = os.path.join(Config.GUIDELINES_DIR, "*.txt")
    
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, 'r') as f:
                text = f.read()
                if keyword.lower() in text.lower():
                    filename = os.path.basename(filepath)
                    results.append({
                        "title": filename.replace("_", " ").replace(".txt", ""),
                        "snippet": text[:200] + "..." if len(text) > 200 else text,
                        "source": filepath
                    })
        except Exception as e:
            # Log error but continue searching other files
            print(f"Warning: Error reading {filepath}: {e}")
            continue
    
    return results

