"""
Anthills: Multi-agent coordination inspired by ant colonies.

Agents coordinate through pheromones (environmental traces),
not explicit messaging. Emergent intelligence from simple local rules.
"""

from .agent import Agent
from .pheromone import PheromoneBoard

__version__ = "0.1.0"
__all__ = ["Agent", "PheromoneBoard"]
