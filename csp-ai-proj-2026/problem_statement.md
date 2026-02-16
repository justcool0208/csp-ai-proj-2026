# Smart Home Energy Management System (SHEMS) - CSP Formalization 📐

This project models the residential energy scheduling problem as a **Constraint Satisfaction and Optimization Problem (CSOP)**. It utilizes the Google OR-Tools CP-SAT solver to find the global optimum for power dispatch across a 96-step daily horizon.

---

## 1. Mathematical Formulation

### 1.1 Decision Variables
- $S_i$: Start time index for appliance $i$ ($S_i \in [0, 95]$).
- $D_i$: Fixed duration in 15-min intervals.
- $X_{i,t} \in \{0,1\}$: binary variable; $1$ if appliance $i$ is active at time index $t$.

### 1.2 The Cost Calculation Model
Total expenditure is calculated by discretizing the 24-hour cycle.

#### **Individual Step Cost ($C_t$):**
For any time step $t$, the cost is derived from the net grid intake after solar and battery offsets:
$$ \text{NetLoad}_t = \max(0, \sum_i (P_i \cdot X_{i,t}) - \text{Solar}_t - \text{BatteryDischarge}_t) $$
$$ C_t = \text{NetLoad}_t \cdot 0.25 \text{ hrs} \cdot \text{Price}_t $$

#### **Savings Logic ($\Delta S$):**
To measure efficiency, the system compares the **Optimized Schedule** against a **Baseline Schedule** (where every appliance starts at its earliest possible time).

$$ \text{BaselineCost}_i = \sum_{t=ES_i}^{ES_i+D_i} P_i \cdot 0.25 \cdot \text{Price}_t $$
$$ \text{NetSaving} = \sum \text{BaselineCost} - \sum \text{OptimizedCost} $$

---

## 2. Constraints & Optimization

### 2.1 Hard Constraints (Non-Negotiable)
1.  **Temporal Consistency**: $S_i + D_i \le \text{LatestEnd}_i$
2.  **Grid Capacity**: $\text{NetLoad}_t \le \text{GridLimit}$ for all $t$.
3.  **Energy Continuity**: Appliances must operate without interruption once started.

### 2.2 Objective Function (The "Total Loss" Function)
The solver minimizes $Z$, a weighted sum of economic and operational factors:
$$ \min Z = \alpha \underbrace{\sum_t C_t}_{\text{Financial Cost}} + \beta \underbrace{\sum_t \text{GridPeak}_t^2}_{\text{Grid Smoothing}} + \gamma \underbrace{\sum_i (S_i - ES_i) \cdot \text{Pri}_i}_{\text{Wait Penalty}} $$

- **$\alpha$**: Weight for monetary savings.
- **$\beta$**: Penalty for quadratic peak demand (prevents all appliances starting at the same time).
- **$\gamma$**: Penalty for delaying high-priority ($Pri_i$) tasks.

---

## 3. Real-World Logic Examples
- **Case A (Solar Shifting)**: If $\text{Price}_{14:00}$ is high but $\text{Solar}_{14:00}$ is $5\text{kW}$, the solver will prioritize scheduling heavy loads here as $\text{NetLoad}_t \rightarrow 0$.
- **Case B (Peak Avoidance)**: If the $\text{GridLimit}$ is $10\text{kW}$ and the HVAC + EV-Charger = $12\text{kW}$, the solver forces a temporal stagger to maintain feasibility.

---
*This formulation ensures that the resulting schedule is not just valid, but mathematically optimal for the user's wallet and the grid's health.*
