"""
Anthills Templates: Declarative, reusable colony configurations.

Templates are the foundation of the SMB agent marketplace. Every agent a small 
business "installs" is a template being instantiated with their parameters and credentials.
"""

from .base import (
    ColonyTemplate,
    WorkerSpec,
    TriggerSpec,
    ParameterSpec,
)
from .catalog import TemplateCatalog
from .instantiator import TemplateInstantiator, TemplateMissingParamError
from .builtins import (
    BUILTIN_TEMPLATES,
    CUSTOMER_INQUIRY_RESPONDER,
    WEEKLY_SALES_SUMMARY,
    RESEARCH_ASSISTANT,
    register_builtins,
)

__all__ = [
    # Data models
    "ColonyTemplate",
    "WorkerSpec",
    "TriggerSpec",
    "ParameterSpec",
    # Catalog & Instantiation
    "TemplateCatalog",
    "TemplateInstantiator",
    "TemplateMissingParamError",
    # Built-in templates
    "BUILTIN_TEMPLATES",
    "CUSTOMER_INQUIRY_RESPONDER",
    "WEEKLY_SALES_SUMMARY",
    "RESEARCH_ASSISTANT",
    "register_builtins",
]
