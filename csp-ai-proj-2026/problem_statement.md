# Smart Home Energy Management System (SHEMS) - CSP Formalization

This project models the energy scheduling problem as a **Constraint Satisfaction and Optimization Problem (CSOP)**. The goal is to schedule household appliances to minimize costs and maximize renewable energy usage while respecting power limits and user preferences.

## 1. Mathematical Formulation

### 1.1 Decision Variables
- $S_i$: Start time for appliance $i$ (Integer, $0 \le S_i \le 95$).
- $E_i$: End time for appliance $i$ (Integer, $E_i = S_i + D_i$).
- $X_{i,t}$: Boolean indicator variable ($X_{i,t} = 1$ if appliance $i$ is active at time $t$).

### 1.2 Constraints
1. **Time Window Constraint**:
   - $S_i \ge \text{EarliestStart}_i$
   - $E_i \le \text{LatestEnd}_i$
2. **Resource Constraint (Power Limit)**:
   - For every interval $t$: $\sum_i (P_i \times X_{i,t}) \le \text{GridLimit} + \text{SolarAvailable}(t)$
3. **Task Continuity**:
   - Appliances must run continuously for $D_i$ intervals (modeled using OR-Tools `IntervalVar`).

### 1.3 Objective Function
Minimize the total weighted cost:
$$ \text{Minimize} \quad \sum_t (\text{GridUsage}_t \times \text{Price}_t) + \sum_i (\text{Delay}_i \times \text{Priority}_i \times \lambda) $$
Where:
- $\text{GridUsage}_t = \max(0, \text{TotalLoad}_t - \text{SolarAvailable}_t)$
- $\text{Delay}_i = S_i - \text{EarliestStart}_i$
- $\lambda$: Scaling factor for user satisfaction penalty.

## 2. Novel Features
- **Solar PV Integration**: Modeling time-varying renewable energy availability.
- **User Satisfaction (Soft Constraints)**: Penalizing delays for high-priority tasks (e.g., HVAC should start as soon as possible).
- **Hybrid Sourcing**: Dynamic switching between Grid and Solar based on instantaneous load.
- **Persistence**: SQLite-backed appliance management.

## 3. Dynamic Optimization
The system uses the **CP-SAT solver**, which is significantly more efficient than standard backtracking for large scheduling horizons. It handles 96 intervals (15-min resolution) per day, involving hundreds of boolean variables and linear constraints.
