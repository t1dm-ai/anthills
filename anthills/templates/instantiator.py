"""
Template Instantiator: Convert templates to runnable colonies.

Takes a template + user parameters + credentials and produces a live Colony.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .base import ColonyTemplate, WorkerSpec

if TYPE_CHECKING:
    from ..colony import Colony
    from ..connectors import ConnectorRegistry
    from ..worker import Worker


class TemplateMissingParamError(Exception):
    """
    Raised when a required template parameter is missing.
    
    The error message is user-facing — surfaces in onboarding UI.
    """
    pass


class TemplateInstantiator:
    """
    Converts ColonyTemplates to runnable Colony instances.
    
    Usage:
        instantiator = TemplateInstantiator(connector_registry)
        
        colony = instantiator.instantiate(
            template=my_template,
            params={"business_name": "Acme Corp", "reply_tone": "Friendly"},
            owner_id="user_123",
        )
        
        colony.run()
    """
    
    def __init__(self, connector_registry: "ConnectorRegistry | None" = None):
        """
        Initialize the instantiator.
        
        Args:
            connector_registry: Registry for resolving connectors
        """
        self._registry = connector_registry
    
    def instantiate(
        self,
        template: ColonyTemplate,
        params: dict[str, Any],
        owner_id: str,
        colony_name: str | None = None,
    ) -> "Colony":
        """
        Produce a runnable Colony from a template + user params.
        
        Args:
            template: The colony template
            params: User-provided parameter values
            owner_id: ID of the user/org instantiating
            colony_name: Optional custom colony name
            
        Returns:
            Configured Colony ready to run
            
        Raises:
            TemplateMissingParamError: If required params are missing
        """
        from ..colony import Colony
        
        # Validate parameters
        self._validate_params(template, params)
        
        # Fill in defaults
        full_params = self._apply_defaults(template, params)
        
        # Create colony with metadata
        colony = Colony(
            name=colony_name or template.name,
            connector_registry=self._registry,
        )
        
        # Store template metadata for audit/debugging
        colony._template_metadata = {
            "template_id": template.template_id,
            "template_version": template.version,
            "owner_id": owner_id,
            "params": {k: v for k, v in full_params.items() 
                      if not self._is_secret_param(template, k)},
        }
        
        # Build and register workers
        for worker_spec in template.workers:
            worker = self._build_worker(worker_spec, full_params)
            colony.register_worker(worker)
        
        return colony
    
    def _validate_params(
        self, template: ColonyTemplate, params: dict[str, Any]
    ) -> None:
        """Validate user-provided parameters."""
        errors = template.validate_params(params)
        if errors:
            raise TemplateMissingParamError("\n".join(errors))
    
    def _apply_defaults(
        self, template: ColonyTemplate, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply default values for missing optional parameters."""
        result = dict(params)
        
        for param in template.parameters:
            if param.name not in result and param.default is not None:
                result[param.name] = param.default
        
        return result
    
    def _is_secret_param(self, template: ColonyTemplate, name: str) -> bool:
        """Check if a parameter is marked as secret."""
        param = template.get_parameter(name)
        return param.secret if param else False
    
    def _build_worker(
        self, spec: WorkerSpec, params: dict[str, Any]
    ) -> "Worker":
        """
        Build a Worker from a WorkerSpec.
        
        Interpolates {param_name} placeholders in prompts.
        """
        from ..worker import Worker
        
        if spec.type == "claude":
            return self._build_claude_worker(spec, params)
        else:
            # For non-claude workers, create a basic worker
            # Future: support webhook, schedule, etc.
            return self._build_basic_worker(spec, params)
    
    def _build_claude_worker(
        self, spec: WorkerSpec, params: dict[str, Any]
    ) -> "Worker":
        """Build a ClaudeWorker from a WorkerSpec."""
        try:
            from ..integrations.claude import ClaudeWorker
        except ImportError:
            raise ImportError(
                "ClaudeWorker requires the anthropic package. "
                "Install it with: pip install anthills[claude]"
            )
        
        # Interpolate parameters into prompts
        try:
            system_prompt = spec.system_prompt.format(**params)
        except KeyError as e:
            system_prompt = spec.system_prompt  # Leave as-is if param missing
        
        try:
            prompt_template = spec.prompt_template.format(**params)
        except KeyError:
            prompt_template = spec.prompt_template
        
        # Create a dynamic worker class
        class _DynamicClaudeWorker(ClaudeWorker):
            pass
        
        # Set class attributes
        _DynamicClaudeWorker.reacts_to = spec.reacts_to
        _DynamicClaudeWorker.output_pheromone_type = spec.output_pheromone_type
        _DynamicClaudeWorker.system_prompt = system_prompt
        _DynamicClaudeWorker.model = spec.model
        _DynamicClaudeWorker.max_tokens = spec.max_tokens
        _DynamicClaudeWorker.retry_on_failure = spec.retry_on_failure
        _DynamicClaudeWorker.max_retries = spec.max_retries
        
        # Store prompt template for message building
        _DynamicClaudeWorker._prompt_template = prompt_template
        
        # Override build_messages to use the prompt template
        original_build_messages = _DynamicClaudeWorker.build_messages
        
        async def build_messages_with_template(self, pheromone):
            if hasattr(self, '_prompt_template') and self._prompt_template:
                try:
                    content = self._prompt_template.format(**pheromone.payload)
                except KeyError:
                    content = str(pheromone.payload)
                return [{"role": "user", "content": content}]
            return await original_build_messages(self, pheromone)
        
        _DynamicClaudeWorker.build_messages = build_messages_with_template
        
        # Instantiate
        worker = _DynamicClaudeWorker(name=spec.name)
        worker.id = spec.id
        worker.connectors = spec.connectors
        
        return worker
    
    def _build_basic_worker(
        self, spec: WorkerSpec, params: dict[str, Any]
    ) -> "Worker":
        """Build a basic Worker for non-claude types."""
        from ..worker import Worker
        
        async def placeholder_handler(ctx):
            # Placeholder for webhook/schedule workers
            # Future: implement actual webhook/schedule handling
            pass
        
        worker = Worker(
            name=spec.name,
            handler=placeholder_handler,
            reacts_to=spec.reacts_to,
            retry_on_failure=spec.retry_on_failure,
            max_retries=spec.max_retries,
        )
        worker.id = spec.id
        worker.connectors = spec.connectors
        
        return worker
