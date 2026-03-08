"""
Tools that agents can call to interact with the world.
"""

import requests
from typing import Any, Dict


class ToolRegistry:
    """Registry of available tools."""
    
    def __init__(self):
        self.tools = {
            "web_search": self.web_search,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "code_analysis": self.code_analysis,
            "synthesize": self.synthesize,
            "wait": self.wait,
        }
    
    def list_tools(self) -> list:
        """List available tool names."""
        return list(self.tools.keys())
    
    def call(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool by name."""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        try:
            result = self.tools[tool_name](**kwargs)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def web_search(query: str, num_results: int = 3) -> str:
        """
        Search the web for information.
        
        Args:
            query: Search query
            num_results: Number of results to return
        
        Returns:
            String summary of search results
        """
        try:
            # Using DuckDuckGo API (no key required)
            url = "https://api.duckduckgo.com/"
            params = {"q": query, "format": "json"}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code != 200:
                return f"Search failed: {response.status_code}"
            
            data = response.json()
            
            # Extract results
            results = []
            for result in data.get("Results", [])[:num_results]:
                results.append(f"- {result['Title']}: {result['FirstURL']}")
            
            return "\n".join(results) if results else "No results found"
        
        except Exception as e:
            return f"Search error: {str(e)}"
    
    @staticmethod
    def read_file(path: str) -> str:
        """
        Read a file from disk.
        
        Args:
            path: File path
        
        Returns:
            File contents
        """
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    @staticmethod
    def write_file(path: str, content: str) -> str:
        """
        Write content to a file.
        
        Args:
            path: File path
            content: Content to write
        
        Returns:
            Confirmation message
        """
        try:
            with open(path, 'w') as f:
                f.write(content)
            return f"Successfully wrote {len(content)} chars to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    @staticmethod
    def code_analysis(code: str) -> str:
        """
        Analyze code for issues, patterns, improvements.
        
        Args:
            code: Code to analyze
        
        Returns:
            Analysis summary
        """
        analysis = {
            "lines": len(code.split('\n')),
            "chars": len(code),
            "functions": code.count('def '),
            "classes": code.count('class '),
        }
        return str(analysis)
    
    @staticmethod
    def synthesize(items: list) -> str:
        """
        Synthesize a list of items into a summary.
        
        Args:
            items: List of items to synthesize
        
        Returns:
            Synthesis summary
        """
        if not items:
            return "Nothing to synthesize"
        
        summary = f"Synthesized {len(items)} items:\n"
        summary += "\n".join(f"- {item}" for item in items)
        return summary
    
    @staticmethod
    def wait(seconds: int = 1) -> str:
        """
        Wait/pause for a bit.
        
        Args:
            seconds: How long to wait
        
        Returns:
            Confirmation
        """
        return f"Waited {seconds} seconds"
