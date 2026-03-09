"""
Template Data Models: Declarative specifications for colonies and workers.

These data structures define a complete multi-agent workflow without any code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ParameterSpec:
    """
    Defines a user-configurable parameter for a template.
    
    Parameters are filled in by the user when instantiating a template.
    Values can be interpolated into worker prompts using {param_name} syntax.
    
    Attributes:
        name: Machine-readable name (used in interpolation)
        display_name: Human-readable label for UI
        description: Help text explaining what the parameter is for
        type: Data type - "string", "number", "boolean", "select"
        required: Whether the parameter must be provided
        default: Default value if not provided
        options: For type="select", the list of valid choices
        secret: If True, value is masked in UI (for API keys, passwords)
    """
    name: str
    display_name: str
    description: str
    type: str  # "string", "number", "boolean", "select"
    required: bool = True
    default: Any = None
    options: list[str] = field(default_factory=list)
    secret: bool = False
    
    def validate(self, value: Any) -> bool:
        """Check if a value is valid for this parameter."""
        if value is None:
            return not self.required or self.default is not None
        
        if self.type == "string":
            return isinstance(value, str)
        elif self.type == "number":
            return isinstance(value, (int, float))
        elif self.type == "boolean":
            return isinstance(value, bool)
        elif self.type == "select":
            return value in self.options
        
        return True


@dataclass
class WorkerSpec:
    """
    Declarative worker definition — no Python class required.
    
    WorkerSpecs are converted to actual Worker instances during instantiation.
    Prompts can contain {param_name} placeholders that are filled from user params.
    
    Attributes:
        id: Stable identifier within the template
        name: Human-readable name
        type: Worker type - "claude", "webhook", "schedule", etc.
        reacts_to: Pheromone types this worker responds to
        output_pheromone_type: Type of pheromone this worker deposits
        system_prompt: System prompt for LLM workers (may contain {param_name})
        prompt_template: User message template (may contain {param_name})
        connectors: Required connector types
        model: LLM model name for claude workers
        max_tokens: Max response tokens for LLM workers
        retry_on_failure: Whether to retry on exception
        max_retries: Max retry attempts
    """
    id: str
    name: str
    type: str  # "claude", "webhook", "schedule"
    reacts_to: list[str]
    output_pheromone_type: str
    system_prompt: str = ""
    prompt_template: str = ""
    connectors: list[str] = field(default_factory=list)
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    retry_on_failure: bool = True
    max_retries: int = 3


@dataclass
class TriggerSpec:
    """
    How a colony is initially activated.
    
    Triggers define what kicks off a colony run:
    - manual: User explicitly starts via API/UI
    - schedule: Cron-based schedule
    - webhook: HTTP endpoint receives external event
    - connector_event: Event from a connected service (e.g. new email)
    
    Attributes:
        type: Trigger type
        config: Type-specific configuration
    """
    type: str  # "manual", "schedule", "webhook", "connector_event"
    config: dict[str, Any] = field(default_factory=dict)
    
    # Config examples:
    # type="schedule"       config={"cron": "0 9 * * MON"}
    # type="webhook"        config={"path": "/webhooks/new-order"}
    # type="connector_event" config={"connector": "gmail", "event": "email.received"}


@dataclass
class ColonyTemplate:
    """
    A complete, reusable colony definition.
    
    Templates are:
    - Authored by developers and published to a catalog
    - Discovered by users browsing the marketplace
    - Instantiated by users supplying parameters and credentials
    - Executed by the Anthills cloud runner
    
    Attributes:
        template_id: Stable, slugified identifier
        name: Human-readable name
        description: Shown in catalog/marketplace
        category: Classification for browsing
        version: Semantic version
        author: Creator handle or "anthills"
        workers: List of worker specifications
        triggers: How the colony is activated
        required_connectors: External services needed
        parameters: User-configurable fields
        tags: Search/filter tags
        icon: Emoji or URL for display
        estimated_cost_per_run: Human-readable cost hint
        preview_video_url: Demo video (Phase 3)
        example_output: Sample result (Phase 3)
        required_plan: Minimum subscription tier (Phase 3)
    """
    template_id: str
    name: str
    description: str
    category: str  # "customer-support", "sales", "finance", "ops"
    version: str
    author: str
    
    workers: list[WorkerSpec]
    triggers: list[TriggerSpec]
    required_connectors: list[str]
    parameters: list[ParameterSpec]
    
    tags: list[str] = field(default_factory=list)
    icon: str = ""
    estimated_cost_per_run: str = ""
    
    # Phase 3 fields (stored for future use)
    preview_video_url: str = ""
    example_output: str = ""
    required_plan: str = "starter"
    
    def get_parameter(self, name: str) -> ParameterSpec | None:
        """Get a parameter specification by name."""
        for param in self.parameters:
            if param.name == name:
                return param
        return None
    
    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """
        Validate user-provided parameters.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        for param in self.parameters:
            value = params.get(param.name, param.default)
            
            if param.required and value is None:
                errors.append(
                    f"Parameter '{param.display_name}' is required. {param.description}"
                )
            elif value is not None and not param.validate(value):
                errors.append(
                    f"Parameter '{param.display_name}' has invalid value: {value}"
                )
        
        return errors
