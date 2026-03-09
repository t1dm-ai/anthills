"""Tests for colony templates."""

import pytest
from anthills.templates import (
    ColonyTemplate,
    WorkerSpec,
    TriggerSpec,
    ParameterSpec,
    TemplateCatalog,
    TemplateInstantiator,
    BUILTIN_TEMPLATES,
)


class TestColonyTemplate:
    """Tests for ColonyTemplate dataclass."""

    def test_create_minimal_template(self):
        """Test creating a template with minimal fields."""
        template = ColonyTemplate(
            name="test-template",
            description="A test template",
            workers=[
                WorkerSpec(
                    name="worker1",
                    reacts_to="event.a",
                    handler="module:handler",
                )
            ],
        )
        
        assert template.name == "test-template"
        assert template.description == "A test template"
        assert len(template.workers) == 1
        assert template.version == "1.0.0"
        assert template.tags == []
        assert template.parameters == []

    def test_create_full_template(self):
        """Test creating a template with all fields."""
        template = ColonyTemplate(
            name="full-template",
            description="A complete template",
            version="2.0.0",
            author="test-author",
            tags=["test", "demo"],
            parameters=[
                ParameterSpec(
                    name="param1",
                    type="string",
                    description="A parameter",
                    required=True,
                )
            ],
            workers=[
                WorkerSpec(
                    name="worker1",
                    reacts_to="event.a",
                    handler="module:handler",
                    emits=["event.b"],
                    requires=["connector1"],
                    config={"key": "value"},
                )
            ],
            triggers=[
                TriggerSpec(type="event.a", payload={"key": "value"})
            ],
        )
        
        assert template.version == "2.0.0"
        assert template.author == "test-author"
        assert "test" in template.tags
        assert len(template.parameters) == 1
        assert len(template.triggers) == 1

    def test_validate_valid_template(self):
        """Test validation passes for valid template."""
        template = ColonyTemplate(
            name="valid",
            description="Valid template",
            workers=[
                WorkerSpec(
                    name="worker1",
                    reacts_to="event.a",
                    handler="module:handler",
                )
            ],
        )
        
        errors = template.validate()
        assert errors == []

    def test_validate_no_workers(self):
        """Test validation fails when no workers defined."""
        template = ColonyTemplate(
            name="empty",
            description="Empty template",
            workers=[],
        )
        
        errors = template.validate()
        assert len(errors) == 1
        assert "at least one worker" in errors[0].lower()

    def test_validate_worker_missing_handler(self):
        """Test validation fails when worker has no handler."""
        template = ColonyTemplate(
            name="bad-handler",
            description="Missing handler",
            workers=[
                WorkerSpec(
                    name="worker1",
                    reacts_to="event.a",
                    handler="",
                )
            ],
        )
        
        errors = template.validate()
        assert len(errors) == 1
        assert "handler" in errors[0].lower()

    def test_validate_worker_missing_reacts_to(self):
        """Test validation fails when worker has no reacts_to."""
        template = ColonyTemplate(
            name="bad-trigger",
            description="Missing reacts_to",
            workers=[
                WorkerSpec(
                    name="worker1",
                    reacts_to="",
                    handler="module:handler",
                )
            ],
        )
        
        errors = template.validate()
        assert len(errors) == 1
        assert "reacts_to" in errors[0].lower()

    def test_to_dict(self):
        """Test serialization to dictionary."""
        template = ColonyTemplate(
            name="test",
            description="Test",
            workers=[
                WorkerSpec(
                    name="w1",
                    reacts_to="e.a",
                    handler="m:h",
                )
            ],
        )
        
        d = template.to_dict()
        assert d["name"] == "test"
        assert d["description"] == "Test"
        assert len(d["workers"]) == 1
        assert d["workers"][0]["name"] == "w1"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "from-dict",
            "description": "From dict",
            "workers": [
                {
                    "name": "worker1",
                    "reacts_to": "event.a",
                    "handler": "module:handler",
                }
            ],
            "parameters": [
                {
                    "name": "param1",
                    "type": "string",
                    "description": "A param",
                }
            ],
        }
        
        template = ColonyTemplate.from_dict(data)
        assert template.name == "from-dict"
        assert len(template.workers) == 1
        assert len(template.parameters) == 1


class TestTemplateCatalog:
    """Tests for TemplateCatalog."""

    def test_register_and_get(self):
        """Test registering and retrieving a template."""
        catalog = TemplateCatalog()
        template = ColonyTemplate(
            name="my-template",
            description="Test",
            workers=[
                WorkerSpec(name="w", reacts_to="e", handler="h")
            ],
        )
        
        catalog.register(template)
        retrieved = catalog.get("my-template")
        
        assert retrieved.name == "my-template"

    def test_get_nonexistent(self):
        """Test getting a template that doesn't exist."""
        catalog = TemplateCatalog()
        
        with pytest.raises(KeyError):
            catalog.get("nonexistent")

    def test_has(self):
        """Test checking if template exists."""
        catalog = TemplateCatalog()
        template = ColonyTemplate(
            name="exists",
            description="Test",
            workers=[
                WorkerSpec(name="w", reacts_to="e", handler="h")
            ],
        )
        
        catalog.register(template)
        
        assert catalog.has("exists") is True
        assert catalog.has("missing") is False

    def test_list(self):
        """Test listing all templates."""
        catalog = TemplateCatalog()
        
        for i in range(3):
            catalog.register(ColonyTemplate(
                name=f"template-{i}",
                description=f"Template {i}",
                workers=[
                    WorkerSpec(name="w", reacts_to="e", handler="h")
                ],
            ))
        
        templates = catalog.list()
        assert len(templates) == 3

    def test_search_by_tag(self):
        """Test searching templates by tag."""
        catalog = TemplateCatalog()
        
        catalog.register(ColonyTemplate(
            name="etl-pipeline",
            description="ETL",
            tags=["etl", "data"],
            workers=[WorkerSpec(name="w", reacts_to="e", handler="h")],
        ))
        catalog.register(ColonyTemplate(
            name="web-scraper",
            description="Scraper",
            tags=["web", "data"],
            workers=[WorkerSpec(name="w", reacts_to="e", handler="h")],
        ))
        catalog.register(ColonyTemplate(
            name="email-sender",
            description="Email",
            tags=["email", "notification"],
            workers=[WorkerSpec(name="w", reacts_to="e", handler="h")],
        ))
        
        # Search by single tag
        data_templates = catalog.search(tags=["data"])
        assert len(data_templates) == 2
        
        # Search by multiple tags (AND)
        etl_only = catalog.search(tags=["etl", "data"])
        assert len(etl_only) == 1
        assert etl_only[0].name == "etl-pipeline"

    def test_search_by_query(self):
        """Test searching templates by query string."""
        catalog = TemplateCatalog()
        
        catalog.register(ColonyTemplate(
            name="research-assistant",
            description="AI-powered research tool",
            workers=[WorkerSpec(name="w", reacts_to="e", handler="h")],
        ))
        catalog.register(ColonyTemplate(
            name="code-reviewer",
            description="Automated code review",
            workers=[WorkerSpec(name="w", reacts_to="e", handler="h")],
        ))
        
        # Search by name
        results = catalog.search(query="research")
        assert len(results) == 1
        assert results[0].name == "research-assistant"
        
        # Search by description
        results = catalog.search(query="code")
        assert len(results) == 1
        assert results[0].name == "code-reviewer"

    def test_register_builtins(self):
        """Test registering built-in templates."""
        catalog = TemplateCatalog()
        catalog.register_builtins()
        
        templates = catalog.list()
        assert len(templates) == len(BUILTIN_TEMPLATES)


class TestBuiltinTemplates:
    """Tests for built-in templates."""

    def test_all_builtins_are_valid(self):
        """Test that all built-in templates pass validation."""
        for template in BUILTIN_TEMPLATES:
            errors = template.validate()
            assert errors == [], f"Template {template.name} has errors: {errors}"

    def test_customer_inquiry_responder(self):
        """Test customer inquiry responder template."""
        template = next(t for t in BUILTIN_TEMPLATES if t.name == "customer_inquiry_responder")
        
        assert template.description
        assert len(template.workers) >= 1
        assert "customer-support" in template.tags or "support" in template.tags or "inquiry" in template.tags

    def test_weekly_sales_summary(self):
        """Test weekly sales summary template."""
        template = next(t for t in BUILTIN_TEMPLATES if t.name == "weekly_sales_summary")
        
        assert template.description
        assert len(template.workers) >= 1
        assert "sales" in template.tags or "reporting" in template.tags

    def test_research_assistant(self):
        """Test research assistant template."""
        template = next(t for t in BUILTIN_TEMPLATES if t.name == "research_assistant")
        
        assert template.description
        assert len(template.workers) >= 1
        assert "research" in template.tags


class TestTemplateInstantiator:
    """Tests for TemplateInstantiator."""

    def test_instantiate_simple_template(self):
        """Test instantiating a simple template."""
        catalog = TemplateCatalog()
        template = ColonyTemplate(
            name="simple",
            description="Simple template",
            workers=[
                WorkerSpec(
                    name="echo",
                    reacts_to="input.received",
                    handler="anthills.worker:Worker",
                    emits=["output.ready"],
                )
            ],
        )
        catalog.register(template)
        
        instantiator = TemplateInstantiator(catalog)
        colony = instantiator.instantiate("simple")
        
        assert colony is not None
        assert colony.name == "simple"

    def test_instantiate_with_colony_name(self):
        """Test instantiating with custom colony name."""
        catalog = TemplateCatalog()
        template = ColonyTemplate(
            name="template",
            description="Test",
            workers=[
                WorkerSpec(
                    name="w",
                    reacts_to="e",
                    handler="anthills.worker:Worker",
                )
            ],
        )
        catalog.register(template)
        
        instantiator = TemplateInstantiator(catalog)
        colony = instantiator.instantiate("template", colony_name="my-colony")
        
        assert colony.name == "my-colony"

    def test_instantiate_nonexistent_template(self):
        """Test instantiating a template that doesn't exist."""
        catalog = TemplateCatalog()
        instantiator = TemplateInstantiator(catalog)
        
        with pytest.raises(KeyError):
            instantiator.instantiate("nonexistent")


class TestWorkerSpec:
    """Tests for WorkerSpec."""

    def test_defaults(self):
        """Test default values."""
        spec = WorkerSpec(
            name="worker",
            reacts_to="event",
            handler="module:handler",
        )
        
        assert spec.emits == []
        assert spec.requires == []
        assert spec.config == {}
        assert spec.retry_count == 0
        assert spec.max_concurrency is None

    def test_full_spec(self):
        """Test full specification."""
        spec = WorkerSpec(
            name="worker",
            reacts_to="event.*",
            handler="my_module:my_handler",
            emits=["result.ready", "error.occurred"],
            requires=["database", "api"],
            config={"timeout": 30},
            retry_count=3,
            max_concurrency=5,
        )
        
        assert spec.reacts_to == "event.*"
        assert len(spec.emits) == 2
        assert len(spec.requires) == 2
        assert spec.config["timeout"] == 30
        assert spec.retry_count == 3
        assert spec.max_concurrency == 5


class TestParameterSpec:
    """Tests for ParameterSpec."""

    def test_required_parameter(self):
        """Test required parameter."""
        param = ParameterSpec(
            name="api_key",
            type="string",
            description="API key for authentication",
            required=True,
        )
        
        assert param.required is True
        assert param.default is None

    def test_optional_parameter_with_default(self):
        """Test optional parameter with default value."""
        param = ParameterSpec(
            name="timeout",
            type="integer",
            description="Request timeout in seconds",
            required=False,
            default=30,
        )
        
        assert param.required is False
        assert param.default == 30


class TestTriggerSpec:
    """Tests for TriggerSpec."""

    def test_simple_trigger(self):
        """Test simple trigger."""
        trigger = TriggerSpec(type="start.requested")
        
        assert trigger.type == "start.requested"
        assert trigger.payload == {}

    def test_trigger_with_payload(self):
        """Test trigger with payload."""
        trigger = TriggerSpec(
            type="task.created",
            payload={"priority": "high", "source": "api"},
        )
        
        assert trigger.payload["priority"] == "high"
        assert trigger.payload["source"] == "api"
