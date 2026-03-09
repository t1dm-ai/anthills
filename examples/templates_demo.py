#!/usr/bin/env python3
"""
Demonstration of Colony Templates in Anthills.

This example shows how to:
1. Use the TemplateCatalog to discover templates
2. Create a custom template
3. Instantiate and run a template-based colony
"""

import asyncio
from anthills import Colony, Pheromone
from anthills.templates import (
    ColonyTemplate,
    WorkerSpec,
    TriggerSpec,
    ParameterSpec,
    TemplateCatalog,
    TemplateInstantiator,
)


def list_builtin_templates():
    """Show all available built-in templates."""
    print("=" * 60)
    print("BUILT-IN TEMPLATES")
    print("=" * 60)
    
    catalog = TemplateCatalog()
    catalog.register_builtins()
    
    for template in catalog.list():
        print(f"\n📋 {template.name}")
        print(f"   {template.description}")
        print(f"   Version: {template.version}")
        print(f"   Tags: {', '.join(template.tags)}")
        print(f"   Workers: {len(template.workers)}")
        if template.parameters:
            print(f"   Parameters:")
            for param in template.parameters:
                req = "(required)" if param.required else f"(default: {param.default})"
                print(f"     - {param.name}: {param.description} {req}")


def create_custom_template():
    """Create a custom template for a data processing pipeline."""
    print("\n" + "=" * 60)
    print("CREATING CUSTOM TEMPLATE")
    print("=" * 60)
    
    # Define a template for a simple ETL pipeline
    etl_template = ColonyTemplate(
        name="simple_etl_pipeline",
        description="Extract, transform, and load data through workers",
        version="1.0.0",
        author="anthills-demo",
        tags=["etl", "data", "pipeline"],
        parameters=[
            ParameterSpec(
                name="source_type",
                type="string",
                description="Type of data source (csv, json, api)",
                required=True,
            ),
            ParameterSpec(
                name="destination",
                type="string",
                description="Where to write output",
                default="stdout",
            ),
            ParameterSpec(
                name="transform_uppercase",
                type="boolean",
                description="Transform text to uppercase",
                default=True,
            ),
        ],
        workers=[
            WorkerSpec(
                name="extractor",
                reacts_to="etl.extract.requested",
                handler="examples.etl_handlers:extract_handler",
                emits=["etl.data.extracted"],
                config={"batch_size": 100},
            ),
            WorkerSpec(
                name="transformer",
                reacts_to="etl.data.extracted",
                handler="examples.etl_handlers:transform_handler",
                emits=["etl.data.transformed"],
            ),
            WorkerSpec(
                name="loader",
                reacts_to="etl.data.transformed",
                handler="examples.etl_handlers:load_handler",
                emits=["etl.complete"],
            ),
        ],
        triggers=[
            TriggerSpec(
                type="etl.extract.requested",
                payload={"source": "{{ source_type }}"},
            ),
        ],
    )
    
    print(f"\n✅ Created template: {etl_template.name}")
    print(f"   Workers: {[w.name for w in etl_template.workers]}")
    print(f"   Parameters: {[p.name for p in etl_template.parameters]}")
    
    # Add to catalog
    catalog = TemplateCatalog()
    catalog.register(etl_template)
    
    # Search for it
    found = catalog.search(tags=["etl"])
    print(f"\n🔍 Search for 'etl' tag found: {[t.name for t in found]}")
    
    return catalog, etl_template


async def run_simple_template_colony():
    """Run a simple colony using inline worker definitions."""
    print("\n" + "=" * 60)
    print("RUNNING TEMPLATE-INSPIRED COLONY")
    print("=" * 60)
    
    # Create a colony that mirrors what a template would generate
    colony = Colony(name="template-demo")
    
    @colony.worker(reacts_to="etl.extract.requested")
    async def extractor(ctx):
        print(f"📥 Extractor received: {ctx.pheromone.payload}")
        await ctx.board.deposit(Pheromone(
            type="etl.data.extracted",
            payload={"records": ["item1", "item2", "item3"]},
            deposited_by="extractor",
        ))
    
    @colony.worker(reacts_to="etl.data.extracted")
    async def transformer(ctx):
        records = ctx.pheromone.payload.get("records", [])
        transformed = [r.upper() for r in records]
        print(f"🔄 Transformer: {records} -> {transformed}")
        await ctx.board.deposit(Pheromone(
            type="etl.data.transformed",
            payload={"records": transformed},
            deposited_by="transformer",
        ))
    
    @colony.worker(reacts_to="etl.data.transformed")
    async def loader(ctx):
        records = ctx.pheromone.payload.get("records", [])
        print(f"📤 Loader output: {records}")
        await ctx.board.deposit(Pheromone(
            type="etl.complete",
            payload={"count": len(records), "status": "success"},
            deposited_by="loader",
        ))
    
    @colony.worker(reacts_to="etl.complete")
    async def reporter(ctx):
        print(f"✅ ETL Complete: {ctx.pheromone.payload}")
    
    # Trigger the pipeline
    colony.deposit(
        type="etl.extract.requested",
        payload={"source": "csv", "path": "/data/input.csv"},
    )
    
    print("\n🚀 Running colony...")
    await colony.run(auto_halt=True)
    print("\n🏁 Colony finished!")


def demonstrate_template_validation():
    """Show template validation features."""
    print("\n" + "=" * 60)
    print("TEMPLATE VALIDATION")
    print("=" * 60)
    
    # Valid template
    valid_template = ColonyTemplate(
        name="valid_template",
        description="A valid template",
        workers=[
            WorkerSpec(
                name="worker1",
                reacts_to="event.a",
                handler="module:handler",
            )
        ],
    )
    
    errors = valid_template.validate()
    print(f"\n✅ Valid template errors: {errors}")
    
    # Template with no workers
    empty_template = ColonyTemplate(
        name="empty_template",
        description="No workers defined",
        workers=[],
    )
    
    errors = empty_template.validate()
    print(f"\n❌ Empty template errors: {errors}")
    
    # Template with missing handler
    bad_handler_template = ColonyTemplate(
        name="bad_handler",
        description="Worker missing handler",
        workers=[
            WorkerSpec(
                name="broken_worker",
                reacts_to="event.x",
                handler="",  # Empty handler
            )
        ],
    )
    
    errors = bad_handler_template.validate()
    print(f"\n❌ Bad handler template errors: {errors}")


def main():
    """Run all demonstrations."""
    print("\n🐜 ANTHILLS TEMPLATES DEMO 🐜\n")
    
    # 1. List built-in templates
    list_builtin_templates()
    
    # 2. Create a custom template
    create_custom_template()
    
    # 3. Show validation
    demonstrate_template_validation()
    
    # 4. Run a template-based colony
    asyncio.run(run_simple_template_colony())
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
