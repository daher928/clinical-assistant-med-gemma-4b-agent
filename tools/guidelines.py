"""
Clinical guidelines tool for retrieving evidence-based treatment protocols.
"""
import glob
import asyncio
import random
import os
from typing import List, Dict
from config import Config
from tools.base import BaseTool


class GuidelinesTool(BaseTool):
    """Tool for searching clinical guidelines."""
    
    def __init__(self):
        super().__init__("Guidelines")
        
    async def _run(self, keyword: str) -> List[Dict]:
        """
        Search clinical guidelines for a specific keyword or condition.
        """
        # Simulate network delay
        await asyncio.sleep(random.uniform(0.3, 0.8))
        
        results = []
        pattern = os.path.join(Config.GUIDELINES_DIR, "*.txt")
        
        # Run file I/O in a separate thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, self._search_files, pattern, keyword)
        
        return results

    def _search_files(self, pattern: str, keyword: str) -> List[Dict]:
        """Helper to search files synchronously."""
        results = []
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

# Singleton instance
_guidelines_tool = GuidelinesTool()

async def search_guidelines(keyword: str) -> List[Dict]:
    """Wrapper for backward compatibility and easy import."""
    return await _guidelines_tool.execute(keyword)

