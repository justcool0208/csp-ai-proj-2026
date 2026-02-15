# Smart Home Energy Management System (SHEMS) 🌿

A technical implementation of a system designed to optimize household energy consumption through mathematical modeling and discrete optimization. The system harmonizes grid tariffs, solar PV generation, and battery storage to minimize procurement costs and peak demand.

## 🛠 Core Capabilities

- **Mathematical Optimization Engine**: Models energy scheduling as a complex set of constraints to be solved for optimal efficiency.
- **Dynamic Tariff Awareness**: Integrates Time-of-Use (TOU) pricing structures (Peak, Standard, and Off-Peak) to drive cost-effective scheduling.
- **Solar & Storage Integration**: Intelligently prioritizes "Free Energy" from solar PV and manages battery state-of-charge for maximum utilization.
- **Constraint Enforcement**: Strictly adheres to global power limits and user-defined operational windows for individual appliances.

## 🧠 System Architecture

The scheduling engine operates on a 96-step temporal domain (15-minute granularity):
- **Decision Variables**: Allotment intervals for system loads.
- **Hard Constraints**: Grid power ceilings, battery energy balance, and mandatory run windows.
- **Objective Function**: A multi-objective minimization of total cost (₹), peak grid load, and prioritization delays.

## 📂 Project Structure

- `main.py`: Primary application containing the API endpoints and the core optimization solver.
- `energy_system.db`: Persistent storage for appliance registry and historical system performance.
- `problem_statement.md`: Technical documentation of the mathematical framework used for scheduling.
- `static/`:
    - `index.html`: Main dashboard for constraint configuration and solver execution.
    - `graph.html`: Visualizer for power dispatch trajectories and energy flow.

## 🚀 Getting Started

1. **Install Prerequisites**:
   ```bash
   pip install fastapi uvicorn ortools pydantic
   ```
2. **Execute System**:
   ```bash
   python main.py
   ```
3. **Access Dashboard**:
   Navigate to `http://localhost:8080` in your browser.

## 🛰 Deployment & Version Control

### GitHub Synchronization
1. **Initialize & Stage**:
   ```bash
   git init
   git add .
   ```
2. **Commit Changes**:
   ```bash
   git commit -m "feat: implement high-precision energy scheduling & printable timetable"
   ```
3. **Push to Remote**:
   ```bash
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

### Deployment (Railway/Render/etc.)
- **Entry Point**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Dependencies**: The system automatically reads `requirements.txt`.
- **Environment**: Ensure the environment is Linux/Mac/Windows (compatible across all).

---
*Built with precision for smart energy management.*
