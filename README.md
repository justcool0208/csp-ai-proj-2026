# CSP SHEMS: Smart Home Energy Management System 🌿

A state-of-the-art energy optimization system designed to balance home appliance loads, solar energy yields, and battery storage. This project leverages **Constraint Satisfaction Programming (CSP)** to minimize electricity costs while maximizing the use of renewable energy.

---

## 🚀 Key Features

- **Mathematical Optimization**: Uses Google OR-Tools (CP-SAT Solver) to solve scheduling over 96 time-slots (15-minute intervals).
- **Solar PV Integration**: Modeling time-varying renewable energy availability based on weather conditions (Sunny, Cloudy, Rainy).
- **Battery Management**: Intelligent charging and discharging logic for an 8kWh battery system.
- **Dynamic Pricing**: Optimizes against Time-of-Use (ToU) electricity rates.
- **User Satisfaction**: Soft constraints that prioritize high-priority tasks and minimize delays.
- **Eco-Pulse Dashboard**: Real-time visualization of energy mix (Grid vs. Solar vs. Battery).

---

## 🛠️ Project Structure

- `csp-ai-proj-2026/`
  - `main.py`: FastAPI backend and CP-SAT optimization engine.
  - `static/`: Modern dashboard built with Chart.js.
  - `energy_system.db`: Persistent storage for appliance data.
  - `batch_test.py`: Comprehensive test suite for CRUD and Optimization.
  - `problem_statement.md`: Detailed mathematical formulation of the CSOP.

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.8 or higher
- Git

### Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd energy-management-system
   ```

2. **Navigate to the source directory**:
   ```bash
   cd csp-ai-proj-2026
   ```

3. **Create and activate a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```
   The dashboard will be available at `http://localhost:8080`.

---

## 🧪 Testing

To ensure the system is functioning correctly, follow these steps:

1. **Start the server** (as described in the Setup section).
2. **Run the comprehensive test suite**:
   ```bash
   python batch_test.py
   ```
   This script verifies:
   - ✨ **CRUD Operations**: Adding, retrieving, and deleting appliances.
   - 🧠 **Optimization Engine**: Running the CSP solver on a set of loads.
   - ✅ **End-to-End Lifecycle**: Verifying the database state after operations.

3. **Run basic optimization test**:
   ```bash
   python test_optim.py
   ```

---

## 📊 Mathematical Formulation

The problem is modeled as a **Constraint Satisfaction and Optimization Problem (CSOP)**:

- **Variables**: $S_i$ (Start time), $E_i$ (End time), $X_{i,t}$ (Active state).
- **Constraints**: Time windows, power limits, task continuity, and battery SOC limits.
- **Objective**: 
  1. Minimize Total Cost (Grid usage × ToU Price).
  2. Minimize Peak Grid Demand.
  3. Maximize User Satisfaction (Priority-weighted delay penalty).

For a deep dive, see [problem_statement.md](./csp-ai-proj-2026/problem_statement.md).

---

## 💰 Economic & Environmental Impact

By shifting heavy loads like EV charging and washing machines to off-peak hours and utilizing battery storage during the evening (4 PM - 9 PM), SHEMS typically reduces grid dependence by **30-50%** and cuts electricity bills by up to **₹2500/month**.

---
*Healing the planet, one kilowatt at a time.* 🌿


## Video 

https://github.com/user-attachments/assets/54541cfa-8ea3-41bc-afa3-1684925c5b3f


