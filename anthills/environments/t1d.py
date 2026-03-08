"""
Type 1 Diabetes Simulation Environment.

A multi-agent model of T1D pathophysiology using stigmergy.

Key agents:
- BetaCells: Sense glucose, produce insulin
- ImmuneSystem: Sense beta cells, attack them
- Glucose: Circulates, regulated by insulin

Pheromones (chemical signals):
- glucose_level: Blood glucose (70-180 mg/dL normal)
- insulin_level: Circulating insulin
- inflammation: Cytokine levels (immune activation)
- beta_cell_autoantigen: Beta cell fragments (triggers immune)
"""

import random
from typing import Dict, Any, List
from datetime import datetime, timedelta


class T1DEnvironment:
    """
    Simulates Type 1 Diabetes pathophysiology.
    
    Models the progression from healthy glucose homeostasis
    to autoimmune destruction of beta cells.
    """
    
    def __init__(
        self,
        initial_beta_cells: int = 1000,
        glucose_level: float = 100.0,
        mutation_rate: float = 0.01,  # Genetic risk
        viral_trigger: bool = False   # Environmental trigger
    ):
        """
        Initialize T1D environment.
        
        Args:
            initial_beta_cells: Starting functional beta cell count
            glucose_level: Starting blood glucose (mg/dL)
            mutation_rate: Genetic predisposition (0-1)
            viral_trigger: Environmental trigger for autoimmunity
        """
        self.time_step = 0
        self.day = 0
        
        # State
        self.beta_cells = initial_beta_cells
        self.max_beta_cells = initial_beta_cells
        self.glucose_level = glucose_level
        self.insulin_level = 0.0
        self.inflammation = 0.0  # Cytokine level
        self.autoimmune_activation = 0.0
        
        # Parameters
        self.mutation_rate = mutation_rate
        self.viral_trigger = viral_trigger
        self.beta_cell_death_rate = 0.05 if viral_trigger else 0.01
        
        # History
        self.history: List[Dict[str, float]] = []
        self.events: List[str] = []
        
        if viral_trigger:
            self.events.append("Day 0: Viral infection detected (environmental trigger)")
        if mutation_rate > 0.3:
            self.events.append("Day 0: Strong genetic predisposition detected")
    
    def step(self) -> Dict[str, Any]:
        """
        Simulate one time step (1 hour).
        
        Returns state of the system.
        """
        self.time_step += 1
        if self.time_step % 24 == 0:
            self.day += 1
        
        # ===== GLUCOSE DYNAMICS =====
        # Glucose rises with meals (simulate 3x/day)
        hour_of_day = self.time_step % 24
        meal_times = [8, 12, 18]  # Breakfast, lunch, dinner
        
        if hour_of_day in meal_times:
            # Meal: glucose rises 40-60 mg/dL
            glucose_rise = random.uniform(40, 60)
            self.glucose_level += glucose_rise
        
        # Basal glucose decay (naturally falling)
        basal_decay = 0.5
        self.glucose_level = max(70, self.glucose_level - basal_decay)
        
        # ===== INSULIN DYNAMICS =====
        # Beta cells sense glucose and produce insulin
        if self.beta_cells > 0:
            # Beta cell response to high glucose
            glucose_stimulus = max(0, self.glucose_level - 100)
            insulin_produced = (self.beta_cells / self.max_beta_cells) * glucose_stimulus * 0.01
            self.insulin_level += insulin_produced
        
        # Insulin clears over time
        self.insulin_level *= 0.95
        self.insulin_level = max(0, self.insulin_level)
        
        # Insulin lowers glucose
        glucose_lowering = self.insulin_level * 0.2
        self.glucose_level = max(70, self.glucose_level - glucose_lowering)
        
        # ===== IMMUNE DYNAMICS =====
        # Immune system activation (triggered by beta cell antigens)
        autoantigen_level = (self.max_beta_cells - self.beta_cells) / self.max_beta_cells
        
        # Viral trigger or genetic predisposition increases immune activation
        base_activation = autoantigen_level
        if self.viral_trigger:
            base_activation *= 2.0  # Viral amplifies response
        base_activation *= (1.0 + self.mutation_rate)
        
        self.autoimmune_activation = min(1.0, base_activation)
        
        # Inflammation follows autoimmune activation
        self.inflammation = self.autoimmune_activation * 100
        
        # ===== BETA CELL DEATH =====
        # High inflammation kills beta cells
        inflammation_effect = self.inflammation / 100.0
        
        # Autoimmune T-cell attack
        attack_rate = self.autoimmune_activation * self.beta_cell_death_rate
        beta_cells_killed = int(self.beta_cells * attack_rate)
        
        # Stochastic death (some variability)
        if random.random() < (inflammation_effect * 0.3):
            beta_cells_killed += random.randint(5, 20)
        
        self.beta_cells = max(0, self.beta_cells - beta_cells_killed)
        
        # ===== MILESTONE EVENTS =====
        percent_destroyed = 100 * (1 - self.beta_cells / self.max_beta_cells)
        
        if percent_destroyed > 50 and not any("50%" in e for e in self.events):
            self.events.append(f"Day {self.day}: 50% beta cell destruction - glucose control impaired")
        
        if percent_destroyed > 80 and not any("80%" in e for e in self.events):
            self.events.append(f"Day {self.day}: 80% beta cell destruction - T1D manifest")
        
        if percent_destroyed > 90 and not any("90%" in e for e in self.events):
            self.events.append(f"Day {self.day}: 90% beta cell destruction - insulin-dependent")
        
        # ===== RECORD STATE =====
        state = {
            "time_step": self.time_step,
            "day": self.day,
            "glucose_level": round(self.glucose_level, 2),
            "insulin_level": round(self.insulin_level, 2),
            "beta_cells": self.beta_cells,
            "beta_cell_percent": round(100 * self.beta_cells / self.max_beta_cells, 1),
            "inflammation": round(self.inflammation, 2),
            "autoimmune_activation": round(self.autoimmune_activation, 3),
            "beta_cells_killed_this_step": beta_cells_killed
        }
        
        self.history.append(state)
        
        return state
    
    def run(self, days: int = 365) -> List[Dict[str, Any]]:
        """
        Run the simulation for N days.
        
        Returns history of all states.
        """
        steps_per_day = 24
        total_steps = days * steps_per_day
        
        for _ in range(total_steps):
            self.step()
        
        return self.history
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state as a snapshot."""
        percent_destroyed = 100 * (1 - self.beta_cells / self.max_beta_cells)
        
        # Diagnose T1D
        diagnosis = "Healthy"
        if percent_destroyed > 50:
            diagnosis = "Autoimmune T1D (manifest)"
        elif percent_destroyed > 20:
            diagnosis = "Autoimmune Stage (progressive)"
        
        return {
            "day": self.day,
            "glucose_level": round(self.glucose_level, 2),
            "insulin_level": round(self.insulin_level, 2),
            "beta_cells_remaining": self.beta_cells,
            "beta_cell_percent": round(100 * self.beta_cells / self.max_beta_cells, 1),
            "inflammation_level": round(self.inflammation, 2),
            "autoimmune_activation": round(self.autoimmune_activation, 3),
            "diagnosis": diagnosis,
            "days_simulated": self.day
        }
    
    def summary(self) -> str:
        """Human-readable summary of the simulation."""
        state = self.get_state()
        
        summary = f"""
═══════════════════════════════════════
    TYPE 1 DIABETES SIMULATION
    Day {state['day']} Summary
═══════════════════════════════════════

📊 PANCREATIC STATUS:
  Beta Cells Remaining: {state['beta_cells_remaining']}/{self.max_beta_cells} ({state['beta_cell_percent']}%)
  Diagnosis: {state['diagnosis']}

🩸 GLUCOSE HOMEOSTASIS:
  Blood Glucose: {state['glucose_level']} mg/dL
  Circulating Insulin: {state['insulin_level']} mIU/L
  
🛡️ IMMUNE STATUS:
  Inflammation Level: {state['inflammation_level']}/100
  Autoimmune Activation: {state['autoimmune_activation']:.1%}
  
📅 KEY EVENTS:
"""
        for event in self.events:
            summary += f"  • {event}\n"
        
        summary += "\n═══════════════════════════════════════\n"
        
        return summary
    
    def get_pheromones(self) -> Dict[str, float]:
        """
        Return current state as 'pheromones' for agents to sense.
        
        This bridges the environment to the agent framework.
        """
        return {
            "glucose_level": self.glucose_level,
            "insulin_level": self.insulin_level,
            "inflammation": self.inflammation,
            "autoimmune_activation": self.autoimmune_activation,
            "beta_cell_count": self.beta_cells,
            "beta_cell_percent": 100 * self.beta_cells / self.max_beta_cells
        }
