# Smart Home Energy Management System (SHEMS) 🌿
*A Constraint Satisfaction Problem (CSP) Approach to Residential Energy Optimization*

## Overview
This project is a high-precision **Smart Home Energy Management System (SHEMS)** designed to optimize residential energy consumption. It frames appliance scheduling as a **Constraint Satisfaction Problem (CSP)**, solving for the most cost-effective and grid-efficient operational schedule while respecting user-defined temporal and power constraints.

The system harmonizes three distinct energy vectors:
1.  **Grid Intake**: Dynamic Time-of-Use (TOU) tariffs (Peak, Standard, Off-Peak).
2.  **Solar PV Generation**: Real-time "free energy" harvesting.
3.  **Battery Storage**: Peak-shaving and energy shifting via chemical storage.

---

## Key Features

### Advanced Optimization Engine
*   **Mathematical Modeling**: Leverages discrete optimization to find the global optimum for energy dispatch.
*   **Multi-Objective Minimization**:
    *   **Primary**: Minimize total monetary expenditure (₹).
    *   **Secondary**: Minimize peak grid demand (kW) to prevent transformer stress.
    *   **Tertiary**: Stability bias (prioritizing earlier starts for high-priority tasks).
*   **Interval Logic**: Uses 15-minute granularity (96 steps/day) for high-fidelity scheduling.

### Professional Analytics Dashboard
*   **Visual Dispatch Trajectory**: Real-time Chart.js interactive graphs showing Grid, Solar, Battery, and Load interaction.
*   **Gantt-Style Timetable**: A chronological "Time Table" of every appliance's active window.
*   **Printable Roadmap**: One-click generation of a physical operational schedule for home use.

### Constraint Framework
*   **Category-Based Prioritizing**:
    *   `Critical Mission`: Immovable loads (Server, Fridge).
    *   `Essential`: High-priority flexible loads (HVAC).
    *   `Standard`: Regular operative tasks (Washer).
    *   `Flexible/Deferrable`: Non-urgent loads suited for solar matching.

---

## Technical Architecture

### The Solver Logic (Backend)
The system treats energy management as a **hard-constraint problem**:
*   **Hard Constraints**: Total power must never exceed the `grid_limit`. Battery SOC must remain within physical bounds. Appliances must finish within their user-defined windows.
*   **Soft Constraints**: Penalties are applied to schedules that delay critical tasks or rely too heavily on peak-hour grid energy.

### Data Flow
1.  **Input**: User defines appliance properties (Power, Duration, Window, Category).
2.  **Processing**: The FastAPI backend transforms these into a mathematical model.
3.  **Optimization**: The CP-SAT engine iterates through millions of combinations to find the "Cheapest & Smoothest" schedule.
4.  **Output**: Returns a step-by-step history, summary metrics, and a visual dispatch plan.

---

## Project Structure
```bash
├── main.py                # FastAPI Application & Optimization Engine
├── energy_system.db       # Persistent SQLite Warehouse
├── requirements.txt       # System Dependency Manifest
├── static/
│   ├── index.html         # Main Mission Control Dashboard
│   ├── graph.html         # Deep Dispatch Visualizer
│   ├── script.js          # Reactive UI Logic
│   ├── graph.js           # Analytics & Charting Engine
│   └── style.css          # Premium Glassmorphic Design System
```

---

## Installation & Setup

### 1. Environment Preparation
Ensure you have Python 3.10+ installed.
```bash
pip install -r requirements.txt
```

### 2. Launching the System
```bash
python main.py
```
*The system will automatically initialize a fresh `energy_system.db` with a standard industrial reference dataset if none exists.*

### 3. Local Access
Open your browser and navigate to:
`http://localhost:8080`


### Git Workflow
```bash
git add .
git commit -m "feat: implement high-precision SHEMS with optimized scheduling"
git push origin main
```

---
*Developed with a focus on mathematical precision and sustainable energy engineering.*
