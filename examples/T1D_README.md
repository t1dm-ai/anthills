# Type 1 Diabetes Simulation with Anthills

A multi-agent model of Type 1 Diabetes pathophysiology using emergent coordination.

## Why Anthills for T1D?

Type 1 Diabetes is a perfect use case for anthills because:

1. **No central controller** — Immune system, pancreas, glucose metabolism all coordinate without a "boss"
2. **Chemical signaling** — Agents communicate via pheromones (glucose, insulin, cytokines, antigens)
3. **Emergent behavior** — Complex disease dynamics emerge from simple local rules
4. **Feedback loops** — Beta cell death amplifies inflammation, which kills more cells

## The Model

### Agents

**BetaCells**
- Sense: Glucose level, inflammation
- Respond: Produce insulin (proportional to glucose and cell count)
- Deposit: Insulin pheromone

**ImmuneSystem**
- Sense: Beta cell autoantigen (from destroyed cells)
- Respond: Attack beta cells (proportional to activation level)
- Deposit: Inflammation pheromone (cytokines)

**Glucose Homeostasis**
- Glucose rises with meals (3x/day)
- Insulin lowers glucose
- Without insulin, glucose stays elevated

### Pheromones (Chemical Signals)

| Signal | Meaning | Range |
|--------|---------|-------|
| `glucose_level` | Blood sugar | 70-400 mg/dL |
| `insulin_level` | Circulating insulin | 0-50 mIU/L |
| `inflammation` | Cytokine levels (immune activation) | 0-100 |
| `autoimmune_activation` | T-cell attack intensity | 0-1 |
| `beta_cell_count` | Functional beta cells remaining | 0-1000 |

### Parameters

| Parameter | Description | Impact |
|-----------|-------------|--------|
| `genetic_risk` | HLA predisposition (0-1) | Higher = faster autoimmunity |
| `viral_trigger` | Environmental infection | Amplifies immune response 2x |
| `beta_cell_death_rate` | Attack rate per step | Controls T1D progression speed |

## The Pathophysiology

### Stage 1: Tolerance Break (Days 1-30)
- Genetic predisposition + environmental trigger (e.g., viral infection)
- Immune system begins recognizing beta cells as foreign
- Minimal beta cell loss (<5%)

### Stage 2: Progressive Autoimmunity (Days 30-180)
- T-cell infiltration increases
- Beta cell death accelerates
- Glucose starts rising (insulin deficiency)
- 20-50% beta cell loss

### Stage 3: Clinical Manifestation (Days 180-365)
- >50% beta cell loss → glucose dyscontrol
- >80% beta cell loss → diagnosis of T1D
- >90% beta cell loss → insulin-dependent for survival

## Run the Simulation

```bash
python t1d_simulation.py
```

### Output

For each checkpoint (day 0, 30, 60, 90, 180, 365):
```
📊 Day 90 Status:
   Beta Cells: 450/1000 (45%)
   Glucose: 145 mg/dL
   Insulin: 8.2 mIU/L
   Inflammation: 35.4/100
   Diagnosis: Autoimmune Stage (progressive)
```

Timeline of key events:
```
📈 Timeline of Key Events:
  • Day 0: Viral infection detected (environmental trigger)
  • Day 87: 50% beta cell destruction - glucose control impaired
  • Day 162: 80% beta cell destruction - T1D manifest
```

## Customizing the Simulation

### High-Risk Scenario (Fast T1D)
```python
env = simulate_t1d(days=365, genetic_risk=0.7, viral_trigger=True)
```
Result: T1D manifest by day ~150

### Low-Risk Scenario (Slow Progression)
```python
env = simulate_t1d(days=365, genetic_risk=0.2, viral_trigger=False)
```
Result: Slow autoimmunity, may not manifest in 1 year

### Very High Risk (Accelerated)
```python
env = simulate_t1d(days=365, genetic_risk=0.9, viral_trigger=True)
```
Result: T1D manifest by day ~60

## The Biology (Simplified)

### Normal Glucose Homeostasis
1. Meal → glucose rises
2. BetaCells sense glucose
3. BetaCells release insulin pheromone
4. Insulin lowers glucose
5. System back to baseline

### T1D Pathogenesis
1. Viral infection + genetic predisposition
2. Immune system loses tolerance to beta cells
3. T-cells attack → beta cells die → release antigens
4. More antigens → more immune activation (positive feedback)
5. Fewer beta cells → less insulin → glucose stays high
6. High glucose damages remaining beta cells
7. Spiral continues until >80% cell loss

### Key Insight
No agent "decides" to cause T1D. It emerges from local responses to chemical signals:
- Immune cells respond to antigens
- Beta cells respond to glucose
- Inflammation responds to immune activation

The system gets stuck in a feedback loop and autoimmunity emerges.

## Medical Relevance

This model captures key aspects of human T1D:

✅ **Accurately modeled:**
- Genetic + environmental factors (threshold effect)
- Progressive beta cell destruction
- Glucose dysregulation
- Autoimmune feedback loops
- Threshold for clinical manifestation (~80% cell loss)

⚠️ **Simplified:**
- No HLA protein dynamics (just mutation_rate)
- No T-regulatory cell dysfunction
- No GAD/IA2/ZnT8 antibody diversity
- No C-peptide preservation (LADA)
- No remission/honeymoon period

## Extending the Model

Ideas for enhancement:

1. **Add agents**: T-regulatory cells (suppress immune), beta cell stress (apoptosis), HLA-peptide presentation
2. **Multiple antigens**: GAD, IA2, ZnT8 (realistic epitope spreading)
3. **Intervention**: Insulin therapy, immunosuppression, beta cell regeneration
4. **Population dynamics**: Model 100+ agents with spatial structure
5. **Machine learning**: Train Claude to predict disease progression

## References

- Type 1 Diabetes pathogenesis: [JDRF](https://www.jdrf.org/)
- Autoimmune dynamics: Janeway's Immunology (Chapter 14)
- Agent-based models in immunology: PLoS Computational Biology

---

**Built with Anthills 🐜** — Multi-agent coordination through environmental traces, not explicit messaging.
