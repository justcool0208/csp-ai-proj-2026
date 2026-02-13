# CSP SHEMS: Decision Engine & Solver 🌿

This directory contains the core logic for the Smart Home Energy Management System. It handles the API requests, database interactions, and the CSP optimization solver.

## 📁 Key Files

- **`main.py`**: The FastAPI application. Contains the REST endpoints and the **CP-SAT solver** implementation using Google OR-Tools.
- **`energy_system.db`**: SQLite database storing the appliance registry and historical settings.
- **`batch_test.py`**: Automated test suite that covers the full API lifecycle.
- **`test_optim.py`**: A lightweight script to verify the solver's output.
- **`problem_statement.md`**: The mathematical documentation for the energy scheduling problem.

## 🚀 Quick Start (Local Development)

1. **Activate Environment**:
   ```bash
   .\venv\Scripts\activate
   ```
2. **Launch Server**:
   ```bash
   python main.py
   ```
3. **Run Tests**:
   ```bash
   python batch_test.py
   ```

Refer to the [Root README](../README.md) for full project documentation and setup instructions.
