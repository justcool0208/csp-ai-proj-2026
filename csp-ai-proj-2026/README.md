# CSP SHEMS: Smart Home Energy Management System 🌿

A state-of-the-art energy optimization dashboard designed to balance home appliance loads, solar energy yields, and battery storage to minimize costs and maximize environmental impact.

## 🚀 How It Works

The system utilizes **Constraint Satisfaction Programming (CSP)** via Google's OR-Tools to solve the complex puzzle of energy management.

### 1. The Decision Engine (Backend)
- **Mathematical Optimization**: The system models your home's energy flow as a mathematical problem over 96 time-slots (15-minute intervals).
- **Multi-Objective Solver**: 
    - **Primary Goal**: Minimize total electricity cost using Time-of-Use (ToU) pricing.
    - **Secondary Goal**: "Peak Shaving" — reducing the maximum demand on the grid to avoid surcharges.
    - **Tertiary Goal**: Maximize Solar-Self-Consumption by shifting flexible loads to peak sun hours.
- **Battery Sync**: The solver decides when to store excess solar energy in your 8kWh battery and when to discharge it (usually during expensive evening peaks).

### 2. The Nature-Pro Interface (Frontend)
- **Eco-Pulse Dashboard**: Real-time visualization of the energy mix (Grid vs. Solar vs. Battery).
- **Eco-Flow Timetable**: A transparent "Explainability" layer that shows every device schedule alongside the specific logic (e.g., "Shifted to night-rate") and projected savings in ₹.
- **Inventory Control**: Allows you to dynamically bind new devices or restore a professional simulation set.

## 🛠️ Key Components
- **Framework**: FastAPI (Python) for high-precision backend performance.
- **Optimizer**: Google OR-Tools (CP-SAT Solver).
- **Database**: SQLite3 for persistent appliance Pulse data.
- **Visualization**: Chart.js with nature-mode custom skin.

## 💰 Economic Impact
By shifting heavy loads (EV Charging, Washing Machines) to off-peak hours and utilizing battery storage during the 4 PM - 9 PM window, the system typically reduces grid dependence by **30-50%** and cuts bills by up to **₹2500/month** in optimized scenarios.

---
*Healing the planet, one kilowatt at a time.* 🌿
