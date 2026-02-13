from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import sqlite3
import math
import random
from ortools.sat.python import cp_model

app = FastAPI(title="CSP SHEMS | Pro Eco Edition")

# --- DATABASE ENGINE ---
DB_PATH = "energy_system.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS appliances (
        id TEXT PRIMARY KEY, name TEXT, power REAL, duration INTEGER,
        earliest_start INTEGER, latest_end INTEGER, priority INTEGER, mandatory INTEGER
    )''')
    cursor.execute("SELECT COUNT(*) FROM appliances")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ('1', 'Eco Washer', 1.8, 90, 600, 960, 3, 1),      # Optimum for Solar
            ('2', 'Home Dishwasher', 1.2, 60, 1140, 1380, 2, 1), # Tail-end of solar
            ('3', 'Rapid EV Charge', 3.5, 240, 0, 420, 5, 1),    # Night (Cheap)
            ('4', 'Pro HVAC System', 1.2, 180, 0, 1439, 4, 1),   # All-day balance
            ('5', 'Pool Heat Pump', 2.0, 120, 720, 1080, 1, 1)   # Peak Solar Sink
        ]
        cursor.executemany("INSERT INTO appliances VALUES (?,?,?,?,?,?,?,?)", defaults)
    conn.commit()
    conn.close()

init_db()

# --- DATA MODELS ---
class Appliance(BaseModel):
    id: str
    name: str
    power: float
    duration: int
    earliest_start: int
    latest_end: int
    priority: int
    mandatory: bool = True

class OptimizationRequest(BaseModel):
    max_power_limit: float = 12.0 # Buffer for overlap
    include_solar: bool = True
    battery_capacity: float = 8.0 # Larger default battery
    weather_condition: str = "Sunny"

class TimeStepData(BaseModel):
    time: str
    grid: float
    solar: float
    battery: float
    load: float
    cost: float

class OptimizationResponse(BaseModel):
    status: str
    schedule: List[dict]
    summary: dict
    time_series: List[TimeStepData]
    suggestions: List[str]

# --- UTILITIES ---

def get_solar_profile(condition="Sunny"):
    peak = 5.0 if condition == "Sunny" else (2.5 if condition == "Cloudy" else 0.8)
    return [max(0, peak * math.sin(math.pi * (t - 24) / 48)) if 24 <= t <= 72 else 0.0 for t in range(96)]

def get_tou_prices():
    return [0.35 if 64 <= t <= 84 else (0.09 if t <= 24 else 0.18) for t in range(96)]

# --- API ENDPOINTS ---

@app.get("/api/appliances")
async def get_apps():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appliances")
    rows = cursor.fetchall()
    conn.close()
    return [{"id":r[0],"name":r[1],"power":r[2],"duration":r[3],"earliest_start":r[4],"latest_end":r[5],"priority":r[6]} for r in rows]

@app.post("/api/appliances")
async def add_app(app: Appliance):
    if app.latest_end <= app.earliest_start:
        raise HTTPException(status_code=400, detail="End time must be after start!")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO appliances VALUES (?,?,?,?,?,?,?,?)", 
                   (app.id, app.name, app.power, app.duration, app.earliest_start, app.latest_end, app.priority, 1))
    conn.commit()
    conn.close()
    return {"status":"ok"}

@app.delete("/api/appliances/{aid}")
async def del_app(aid: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor() # FIXED: cursor was missing!
    cursor.execute("DELETE FROM appliances WHERE id=?", (aid,))
    conn.commit()
    # Check if delete actually worked
    cursor.execute("SELECT COUNT(*) FROM appliances WHERE id=?", (aid,))
    count = cursor.fetchone()[0]
    conn.close()
    if count > 0:
        raise HTTPException(status_code=500, detail="Failed to remove entry")
    return {"status":"ok"}

@app.post("/api/reset")
async def reset_simulation():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appliances")
    defaults = [
        ('1', 'Eco Washer', 1.8, 90, 600, 960, 3, 1),
        ('2', 'Home Dishwasher', 1.2, 60, 1140, 1380, 2, 1),
        ('3', 'Rapid EV Charge', 3.5, 240, 0, 420, 5, 1),
        ('4', 'Pro HVAC System', 1.2, 180, 0, 1439, 4, 1),
        ('5', 'Pool Heat Pump', 2.0, 120, 720, 1080, 1, 1)
    ]
    cursor.executemany("INSERT INTO appliances VALUES (?,?,?,?,?,?,?,?)", defaults)
    conn.commit()
    conn.close()
    return {"status": "reset to simulation"}

@app.post("/api/optimize")
async def optimize(req: OptimizationRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appliances ORDER BY id")
    apps = cursor.fetchall()
    conn.close()
    
    if not apps: return {"status":"No devices"}

    model = cp_model.CpModel()
    NUM_T = 96
    solar = get_solar_profile(req.weather_condition)
    prices = get_tou_prices()
    
    task_vars = {}
    for r in apps:
        aid, name, pwr, dur_min, s_min, e_max, pri, _ = r
        s_idx, e_idx = s_min // 15, e_max // 15
        dur_idx = (dur_min + 14) // 15
        
        # Auto-adjust for feasibility
        if s_idx + dur_idx > e_idx: e_idx = s_idx + dur_idx
        if e_idx > 96: 
            e_idx = 96
            if s_idx + dur_idx > 96: s_idx = 96 - dur_idx

        start = model.NewIntVar(s_idx, e_idx - dur_idx, f's_{aid}')
        end = model.NewIntVar(s_idx + dur_idx, e_idx, f'e_{aid}')
        interval = model.NewIntervalVar(start, dur_idx, end, f'i_{aid}')
        task_vars[aid] = {'start':start, 'end':end, 'pwr':pwr, 'name':name, 'pri':pri, 'dur_min':dur_min}

    # Battery System Logic
    max_batt_w = 2500 
    batt_cap_wh = int(req.battery_capacity * 1000)
    soc = [model.NewIntVar(0, batt_cap_wh, f'soc_{t}') for t in range(NUM_T + 1)]
    discharge = [model.NewIntVar(0, max_batt_w, f'd_{t}') for t in range(NUM_T)]
    charge = [model.NewIntVar(0, max_batt_w, f'c_{t}') for t in range(NUM_T)]
    
    model.Add(soc[0] == batt_cap_wh // 2) # Start 50%
    
    grid = [model.NewIntVar(0, int(req.max_power_limit * 1000), f'g_{t}') for t in range(NUM_T)]
    
    for t in range(NUM_T):
        active_loads = []
        for aid, v in task_vars.items():
            # Correct Boolean Logic for Interval Activity
            # is_active <=> (start <= t AND end > t)
            b1 = model.NewBoolVar(f'b1_{aid}_{t}')
            b2 = model.NewBoolVar(f'b2_{aid}_{t}')
            
            model.Add(v['start'] <= t).OnlyEnforceIf(b1)
            model.Add(v['start'] > t).OnlyEnforceIf(b1.Not())
            
            model.Add(v['end'] > t).OnlyEnforceIf(b2)
            model.Add(v['end'] <= t).OnlyEnforceIf(b2.Not())
            
            is_active = model.NewBoolVar(f'a_{aid}_{t}')
            model.AddMultiplicationEquality(is_active, [b1, b2])
            
            active_loads.append(is_active * int(v['pwr'] * 1000))
        
        load_t = model.NewIntVar(0, 25000, f'L_{t}')
        model.Add(load_t == sum(active_loads))
        
        # Power Balance: Grid + Solar + Discharge = Load + Charge
        model.Add(grid[t] + int(solar[t]*1000) + discharge[t] >= load_t + charge[t])
        
        # SOC: soc[t+1] = soc[t] + (charge * efficiency - discharge/efficiency)/4
        model.Add(4 * soc[t+1] == 4 * soc[t] + charge[t] - discharge[t])

    # Multi-Objective: Minimize Cost + Minimize Grid Peak + Maximize User Safety
    total_cost_decicents = sum(grid[t] * int(prices[t] * 100) for t in range(NUM_T))
    peak_grid = model.NewIntVar(0, int(req.max_power_limit * 1000), "peak_grid")
    for t in range(NUM_T): model.Add(peak_grid >= grid[t])
    
    # Custom CSP Model: Lexicographical Objective Hierarchy (High-Magnitude Weights)
    # Tier 1: Minimize Total Cost (Weight: 1,000,000)
    # Tier 2: Minimize Peak Demand (Weight: 100)
    # Tier 3: Deterministic UI Stability (Weight: 1)
    
    # We sort the task vars by ID before summing to ensure the objective definition is identical
    sorted_tasks = [task_vars[aid] for aid in sorted(task_vars.keys())]
    stability_bias = sum(v['start'] for v in sorted_tasks)
    
    model.Minimize(
        (total_cost_decicents * 1000000) + 
        (peak_grid * 100) + 
        stability_bias
    )

    solver = cp_model.CpSolver()
    solver.parameters.random_seed = 42
    solver.parameters.num_search_workers = 1 # Absolute lock
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        res_sched = []
        for aid, v in task_vars.items():
            start_m = solver.Value(v['start']) * 15
            end_m = solver.Value(v['end']) * 15
            
            # Logic for 'Why'
            why = "Scheduled for off-peak pricing."
            if 480 <= start_m <= 1080: why = "Utilizing peak solar availability to minimize grid reliance."
            if start_m >= 1320 or start_m <= 240: why = "Shifted to night-rate to avoid peak demand surcharges."

            # Savings Calculation: Compared to running at Peak (0.35)
            peak_price = 0.35
            actual_price = prices[int(start_m // 15)]
            energy_kWh = v.get('pwr', 0) * (v.get('dur_min', 0) / 60)
            proj_saving = (peak_price - actual_price) * energy_kWh
            if proj_saving < 0: proj_saving = 0 

            res_sched.append({
                "id": aid,
                "name": v['name'],
                "start": start_m,
                "end": end_m,
                "pri": v['pri'],
                "why": why,
                "saving": round(proj_saving, 2)
            })
        
        ts_data = []
        t_cost, t_solar, t_batt, t_load = 0, 0, 0, 0
        for t in range(NUM_T):
            g_kW = solver.Value(grid[t])/1000.0
            d_kW = solver.Value(discharge[t])/1000.0
            c_kW = solver.Value(charge[t])/1000.0
            s_kW = solar[t]
            l_kW = sum(v['pwr'] for aid,v in task_vars.items() if solver.Value(v['start']) <= t < solver.Value(v['end']))
            
            step_cost = g_kW * 0.25 * prices[t]
            t_cost += step_cost
            t_solar += s_kW * 0.25
            t_batt += d_kW * 0.25
            t_load += l_kW * 0.25
            
            ts_data.append(TimeStepData(
                time=f"{t//4:02d}:{(t%4)*15:02d}",
                grid=round(g_kW, 2),
                solar=round(s_kW, 2),
                battery=round(d_kW - c_kW, 2),
                load=round(l_kW, 2),
                cost=round(step_cost, 4)
            ))

        # Insights
        suggestions = []
        if t_solar > 0: 
            ratio = (t_solar/max(0.1, t_load)) * 100
            suggestions.append(f"Solar PV covered {round(ratio)}% of your daily demand.")
        if t_batt > 0: suggestions.append(f"Battery storage shifted {round(t_batt, 2)} kWh to avoid high peak prices.")
        suggestions.append(f"Forecast: {req.weather_condition}. System optimized for {req.weather_condition.lower()} conditions.")

        return OptimizationResponse(
            status="Success",
            schedule=res_sched,
            summary={
                "total_cost": round(t_cost, 2),
                "total_energy": round(t_load, 2),
                "solar_savings": round(t_solar, 2),
                "battery_impact": round(t_batt, 2)
            },
            time_series=ts_data,
            suggestions=suggestions
        )
    
    return {"status": "Infeasible", "suggestions": ["Try increasing the Max Power Limit in Settings or spreading device run-times."]}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
