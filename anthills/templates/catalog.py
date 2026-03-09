"""
Template Catalog: Store and search for colony templates.

In Phase 1, this is an in-memory registry.
In Phase 3, it becomes a DynamoDB-backed marketplace with search, ratings, etc.
"""

from __future__ import annotations

from typing import Any

from .base import ColonyTemplate


class TemplateCatalog:
    """
    Registry for discovering and retrieving colony templates.
    
    Usage:
        catalog = TemplateCatalog()
        catalog.register(my_template)
        
        # Browse by category
        support_templates = catalog.list(category="customer-support")
        
        # Find templates needing a specific connector
        gmail_templates = catalog.list(connector="gmail")
        
        # Search by keyword
        results = catalog.search("email responder")
    """
    
    def __init__(self):
        self._templates: dict[str, ColonyTemplate] = {}
    
    def register(self, template: ColonyTemplate) -> None:
        """
        Register a template in the catalog.
        
        Args:
            template: ColonyTemplate to register
        """
        self._templates[template.template_id] = template
    
    def unregister(self, template_id: str) -> bool:
        """
        Remove a template from the catalog.
        
        Args:
            template_id: ID of template to remove
            
        Returns:
            True if removed, False if not found
        """
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False
    
    def get(self, template_id: str) -> ColonyTemplate | None:
        """
        Get a template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            ColonyTemplate if found, None otherwise
        """
        return self._templates.get(template_id)
    
    def list(
        self,
        category: str | None = None,
        connector: str | None = None,
        tags: list[str] | None = None,
        author: str | None = None,
    ) -> list[ColonyTemplate]:
        """
        List templates with optional filters.
        
        Args:
            category: Filter by category
            connector: Filter by required connector
            tags: Filter by tags (any match)
            author: Filter by author
            
        Returns:
            List of matching templates
        """
        results = list(self._templates.values())
        
        if category:
            results = [t for t in results if t.category == category]
        
        if connector:
            results = [t for t in results if connector in t.required_connectors]
        
        if tags:
            results = [
                t for t in results 
                if any(tag in t.tags for tag in tags)
            ]
        
        if author:
            results = [t for t in results if t.author == author]
        
        return results
    
    def search(self, query: str) -> list[ColonyTemplate]:
        """
        Search templates by keyword.
        
        Searches name, description, and tags.
        
        Args:
            query: Search query
            
        Returns:
            List of matching templates
        """
        query = query.lower()
        results = []
        
        for template in self._templates.values():
            if (
                query in template.name.lower()
                or query in template.description.lower()
                or any(query in tag.lower() for tag in template.tags)
            ):
                results.append(template)
        
        return results
    
    def list_categories(self) -> list[str]:
        """Get all unique categories in the catalog."""
        categories = set()
        for template in self._templates.values():
            categories.add(template.category)
        return sorted(categories)
    
    def list_connectors(self) -> list[str]:
        """Get all unique connectors required by templates."""
        connectors = set()
        for template in self._templates.values():
            connectors.update(template.required_connectors)
        return sorted(connectors)
    
    def count(self) -> int:
        """Get total number of templates in catalog."""
        return len(self._templates)
