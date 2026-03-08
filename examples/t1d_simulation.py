"""
Example: Type 1 Diabetes Simulation with Stigmergy

Multi-agent model of T1D pathophysiology:
- BetaCells: Sense glucose, produce insulin
- ImmuneSystem: Sense antigens, attack beta cells
- No explicit messaging - agents sense chemical signals (pheromones)

This demonstrates emergent autoimmunity through stigmergy.
"""

import sys
sys.path.insert(0, '..')

from anthills import PheromoneBoard
from anthills.environments import T1DEnvironment


class BetaCellAgent:
    """
    Beta cell agent: Senses glucose, produces insulin.
    Deposits insulin pheromone.
    """
    
    def __init__(self, count: int):
        self.name = "BetaCells"
        self.count = count
    
    def sense(self, pheromones: dict) -> dict:
        """Sense chemical environment."""
        return {
            "glucose": pheromones.get("glucose_level", 100),
            "inflammation": pheromones.get("inflammation", 0),
            "self_count": pheromones.get("beta_cell_count", self.count)
        }
    
    def respond(self, sensed: dict) -> dict:
        """Respond to sensed signals."""
        glucose = sensed["glucose"]
        inflammation = sensed["inflammation"]
        
        # High glucose → produce insulin
        insulin_response = max(0, (glucose - 100) * 0.1)
        
        # High inflammation → stress/apoptosis
        stress_response = inflammation / 100.0
        
        return {
            "insulin_produced": insulin_response,
            "stress_level": stress_response,
            "cells_remaining": sensed["self_count"]
        }


class ImmuneSystemAgent:
    """
    Immune system agent: Senses beta cell antigens, attacks.
    Deposits inflammation pheromone.
    """
    
    def __init__(self):
        self.name = "ImmuneSystem"
        self.activated = False
    
    def sense(self, pheromones: dict) -> dict:
        """Sense chemical environment."""
        return {
            "beta_cell_destruction": 100 - pheromones.get("beta_cell_percent", 100),
            "autoimmune_activation": pheromones.get("autoimmune_activation", 0),
            "inflammation": pheromones.get("inflammation", 0)
        }
    
    def respond(self, sensed: dict) -> dict:
        """Respond to sensed signals."""
        destruction = sensed["beta_cell_destruction"]
        activation = sensed["autoimmune_activation"]
        
        # Beta cell antigens activate immune response
        if destruction > 5:
            self.activated = True
        
        # Positive feedback: more destruction → more activation
        attack_intensity = activation * 100
        
        return {
            "attack_intensity": attack_intensity,
            "activated": self.activated,
            "target_recognized": destruction > 0
        }


def simulate_t1d(days: int = 365, genetic_risk: float = 0.5, viral_trigger: bool = True):
    """
    Simulate Type 1 Diabetes progression.
    
    Args:
        days: Days to simulate
        genetic_risk: Genetic predisposition (0-1)
        viral_trigger: Environmental trigger (e.g., viral infection)
    """
    
    print("\n" + "=" * 70)
    print("  STIGMERGY-BASED TYPE 1 DIABETES SIMULATION")
    print("=" * 70)
    print(f"\n📋 Configuration:")
    print(f"   Genetic Risk: {genetic_risk:.0%}")
    print(f"   Viral Trigger: {viral_trigger}")
    print(f"   Duration: {days} days\n")
    
    # Initialize environment
    env = T1DEnvironment(
        initial_beta_cells=1000,
        glucose_level=100.0,
        mutation_rate=genetic_risk,
        viral_trigger=viral_trigger
    )
    
    # Initialize agents
    beta_cells = BetaCellAgent(count=1000)
    immune = ImmuneSystemAgent()
    
    # Shared pheromone board
    board = PheromoneBoard(default_ttl_hours=24)
    
    print(f"🧬 Initial Events:")
    for event in env.events:
        print(f"   {event}")
    print()
    
    # Run simulation with agent interactions
    checkpoint_days = [0, 30, 60, 90, 180, 365]
    
    for day in range(days):
        # Run environment for one day (24 steps)
        for hour in range(24):
            env.step()
        
        # Agents sense and respond (once per day)
        pheromones = env.get_pheromones()
        
        # Beta cells respond
        bc_sensed = beta_cells.sense(pheromones)
        bc_response = beta_cells.respond(bc_sensed)
        board.deposit(
            "beta_cell_activity",
            bc_response,
            source="BetaCells"
        )
        
        # Immune system responds
        imm_sensed = immune.sense(pheromones)
        imm_response = immune.respond(imm_sensed)
        board.deposit(
            "immune_activity",
            imm_response,
            source="ImmuneSystem"
        )
        
        # Print checkpoints
        if (day + 1) in checkpoint_days:
            state = env.get_state()
            print(f"📊 Day {state['day']} Status:")
            print(f"   Beta Cells: {state['beta_cells_remaining']}/1000 ({state['beta_cell_percent']}%)")
            print(f"   Glucose: {state['glucose_level']} mg/dL")
            print(f"   Insulin: {state['insulin_level']} mIU/L")
            print(f"   Inflammation: {state['inflammation_level']:.1f}/100")
            print(f"   Diagnosis: {state['diagnosis']}")
            
            if env.events and env.events[-1].startswith(f"Day {state['day']}"):
                print(f"   ⚠️  {env.events[-1].split(': ', 1)[1]}")
            print()
    
    print("=" * 70)
    print("  SIMULATION SUMMARY")
    print("=" * 70)
    print(env.summary())
    
    print("\n📈 Timeline of Key Events:")
    for event in env.events:
        print(f"  • {event}")
    
    print("\n🧬 Biology Behind the Simulation:")
    print("""
  Type 1 Diabetes emerges from anthills-like dynamics:
  
  1. GENETIC PREDISPOSITION
     Certain HLA types (like HLA-DR3/DR4) increase autoimmune risk
     → Higher "mutation_rate" in simulation
  
  2. ENVIRONMENTAL TRIGGER
     Viral infection (e.g., enterovirus) breaks immune tolerance
     → "viral_trigger" parameter amplifies immune response
  
  3. BETA CELL AUTOIMMUNITY
     Immune system attacks insulin-producing beta cells
     → No explicit messaging between immune cells
     → Emerges from local responses to chemical signals (cytokines, antigens)
     → Creates feedback loop: more beta cell death → more inflammation → more attack
  
  4. GLUCOSE DYSREGULATION
     Without insulin, glucose stays elevated
     → Further stresses remaining beta cells
     → Accelerates disease progression
  
  5. CLINICAL MANIFESTATION
     ~80% beta cell destruction → Type 1 Diabetes diagnosis
     Patients require insulin therapy for survival
    """)
    
    return env


if __name__ == "__main__":
    # Scenario 1: High-risk genetic + viral trigger (typical T1D)
    print("\n\n🔴 SCENARIO 1: High Genetic Risk + Viral Trigger")
    env1 = simulate_t1d(days=365, genetic_risk=0.7, viral_trigger=True)
    
    # Scenario 2: Lower risk (slower progression)
    print("\n\n🟡 SCENARIO 2: Moderate Genetic Risk (No Trigger)")
    env2 = simulate_t1d(days=365, genetic_risk=0.3, viral_trigger=False)
    
    print("\n" + "=" * 70)
    print("  COMPARISON")
    print("=" * 70)
    print(f"High-risk scenario: {env1.get_state()['diagnosis']}")
    print(f"Low-risk scenario:  {env2.get_state()['diagnosis']}")
    print("\nConclusion: Genetic + environmental factors determine T1D onset")
