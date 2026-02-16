from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import sqlite3
import math
import json
from datetime import datetime
from ortools.sat.python import cp_model

app = FastAPI(title="CSP Smart Home Energy Management System")

# --- DATABASE ENGINE ---
DB_PATH = "energy_system.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS appliances (
        id TEXT PRIMARY KEY, name TEXT, power REAL, duration INTEGER,
        earliest_start INTEGER, latest_end INTEGER, priority INTEGER, mandatory INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        summary TEXT,
        schedule TEXT
    )''')
    
    cursor.execute("SELECT COUNT(*) FROM appliances")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ('1', 'Eco Washer', 1.8, 90, 600, 1080, 3, 1),             # 10:00 - 18:00
            ('2', 'Home Dishwasher', 1.2, 60, 1140, 1380, 2, 1),       # 19:00 - 23:00
            ('3', 'Rapid EV Charge', 3.5, 240, 0, 480, 5, 1),          # 00:00 - 08:00
            ('4', 'Central HVAC', 2.2, 180, 0, 1439, 4, 1),            # 24hr flexibility
            ('5', 'Pool Heat Pump', 2.0, 120, 720, 1080, 1, 1),        # 12:00 - 18:00
            ('6', 'Smart Oven', 2.5, 45, 1020, 1200, 3, 1),            # 17:00 - 20:00
            ('7', 'Home Office Cluster', 0.8, 480, 480, 1020, 5, 1)    # 08:00 - 17:00
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
    max_power_limit: float = 12.0
    include_solar: bool = True
    battery_capacity: float = 8.0
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
    # Rupees per kWh: Peak=₹12, Std=₹6, Off-Peak=₹3
    return [12.0 if 64 <= t <= 84 else (3.0 if t <= 24 else 6.0) for t in range(96)]

def calculate_baseline(apps, prices):
    """Calculates cost if all appliances started at their earliest possible time (Baseline)."""
    ts_load = [0.0] * 96
    total_cost = 0.0
    for r in apps:
        aid, name, pwr, dur_min, s_min, e_max, pri, _ = r
        s_idx = s_min // 15
        dur_idx = (dur_min + 14) // 15
        for t in range(s_idx, min(s_idx + dur_idx, 96)):
            ts_load[t] += pwr
    
    for t in range(96):
        total_cost += ts_load[t] * 0.25 * prices[t]
    return round(total_cost, 2), round(sum(ts_load) * 0.25, 2)

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
    if (app.latest_end - app.earliest_start) < app.duration:
        raise HTTPException(status_code=400, detail=f"Feasibility Error: Duration ({app.duration}m) is longer than the available window ({app.latest_end - app.earliest_start}m).")
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
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appliances WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    return {"status":"ok"}

@app.get("/api/history")
async def get_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY id DESC LIMIT 15")
    rows = cursor.fetchall()
    conn.close()
    return [{"id":r[0], "timestamp":r[1], "summary":json.loads(r[2]), "schedule":json.loads(r[3])} for r in rows]

@app.delete("/api/history")
async def clear_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history")
    conn.commit()
    conn.close()
    return {"status":"ok"}

@app.post("/api/optimize")
async def optimize(req: OptimizationRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appliances ORDER BY id")
    apps = cursor.fetchall()
    conn.close()
    
    if not apps: return {"status":"No devices"}

    prices = get_tou_prices()
    baseline_cost, baseline_energy = calculate_baseline(apps, prices)

    model = cp_model.CpModel()
    NUM_T = 96
    solar = get_solar_profile(req.weather_condition)
    
    task_vars = {}
    for r in apps:
        aid, name, pwr, dur_min, s_min, e_max, pri, _ = r
        s_idx, e_idx = s_min // 15, e_max // 15
        dur_idx = (dur_min + 14) // 15
        
        # Security constraints
        if s_idx + dur_idx > e_idx: e_idx = s_idx + dur_idx
        if e_idx > 96: 
            e_idx = 96
            if s_idx + dur_idx > 96: s_idx = 96 - dur_idx

        start = model.NewIntVar(s_idx, e_idx - dur_idx, f's_{aid}')
        end = model.NewIntVar(s_idx + dur_idx, e_idx, f'e_{aid}')
        interval = model.NewIntervalVar(start, dur_idx, end, f'i_{aid}')
        task_vars[aid] = {'start':start, 'end':end, 'pwr':pwr, 'name':name, 'pri':pri, 'dur_min':dur_min, 'start_min': s_min}

    # Battery
    max_batt_w = 2500 
    batt_cap_wh = int(req.battery_capacity * 1000)
    soc = [model.NewIntVar(0, batt_cap_wh, f'soc_{t}') for t in range(NUM_T + 1)]
    discharge = [model.NewIntVar(0, max_batt_w, f'd_{t}') for t in range(NUM_T)]
    charge = [model.NewIntVar(0, max_batt_w, f'c_{t}') for t in range(NUM_T)]
    model.Add(soc[0] == batt_cap_wh // 2)
    
    grid = [model.NewIntVar(0, int(req.max_power_limit * 1000), f'g_{t}') for t in range(NUM_T)]
    
    for t in range(NUM_T):
        active_loads = []
        for aid, v in task_vars.items():
            b1, b2 = model.NewBoolVar(f'b1_{aid}_{t}'), model.NewBoolVar(f'b2_{aid}_{t}')
            model.Add(v['start'] <= t).OnlyEnforceIf(b1)
            model.Add(v['start'] > t).OnlyEnforceIf(b1.Not())
            model.Add(v['end'] > t).OnlyEnforceIf(b2)
            model.Add(v['end'] <= t).OnlyEnforceIf(b2.Not())
            is_active = model.NewBoolVar(f'a_{aid}_{t}')
            model.AddMultiplicationEquality(is_active, [b1, b2])
            active_loads.append(is_active * int(v['pwr'] * 1000))
        
        load_t = model.NewIntVar(0, 25000, f'L_{t}')
        model.Add(load_t == sum(active_loads))
        model.Add(grid[t] + int(solar[t]*1000) + discharge[t] >= load_t + charge[t])
        model.Add(4 * soc[t+1] == 4 * soc[t] + charge[t] - discharge[t])

    total_cost_paise = sum(grid[t] * int(prices[t] * 100) for t in range(NUM_T))
    peak_grid = model.NewIntVar(0, int(req.max_power_limit * 1000), "peak_grid")
    for t in range(NUM_T): model.Add(peak_grid >= grid[t])
    
    # Soft constraints: Prioritize earlier start times for high-priority units
    sorted_tasks = [task_vars[aid] for aid in sorted(task_vars.keys())]
    stability_bias = sum(v['start'] * (6 - v['pri']) for v in sorted_tasks)
    
    # Multi-Objective: Cost reduction (primary) + Peak load balancing (secondary)
    model.Minimize(total_cost_paise + (peak_grid * 500) + stability_bias)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        res_sched = []
        for aid, v in task_vars.items():
            start_m = solver.Value(v['start']) * 15
            end_m = solver.Value(v['end']) * 15
            
            # Technical Optimization Reasoning
            actual_price = prices[int(start_m // 15)]
            s_idx = solver.Value(v['start'])
            dur_idx = (v['dur_min'] + 14) // 15
            
            # Step-by-step cost in optimized schedule
            o_cost = 0
            for t in range(s_idx, s_idx + dur_idx):
                t_clamped = min(t, 95)
                # Calculate what load at this step costs AFTER solar/battery
                # We share the grid-intake cost proportionally among active loads
                step_grid_kW = solver.Value(grid[t_clamped]) / 1000.0
                total_step_load = sum(v2['pwr'] for v2 in task_vars.values() if solver.Value(v2['start']) <= t_clamped < solver.Value(v2['end']))
                share = (v['pwr'] / max(0.1, total_step_load))
                o_cost += (step_grid_kW * share) * 0.25 * prices[t_clamped]

            # Baseline (Earliest Start)
            # Baseline assumes no battery/solar shift - strictly grid
            b_start_idx = v['start_min'] // 15
            b_dur_idx = (v['dur_min'] + 14) // 15
            b_cost = sum(v['pwr'] * 0.25 * prices[min(t, 95)] for t in range(b_start_idx, b_start_idx + b_dur_idx))
            
            # Reasoning
            why = "Strategic load-balancing."
            if 480 <= start_m <= 1080: 
                why = "Shifted to Solar-Peak window to utilize zero-cost generation."
            elif actual_price <= 3.0:
                why = "Scheduled in night slot to capture ₹3/kWh economy tariff."
            elif b_cost > o_cost:
                why = "Shifted away from baseline peak to reduce grid demand impact."
            
            if actual_price >= 12.0: 
                why = "Mandatory constraint: Locked in peak window due to strict duration limits."

            res_sched.append({
                "id": aid, "name": v['name'], "power": v['pwr'], "start": start_m, "end": end_m,
                "pri": v['pri'], "baseline_cost": round(b_cost, 2), "optimized_cost": round(o_cost, 2),
                "saving": round(max(0, b_cost - o_cost), 2), "why": why
            })
        
        ts_data = []
        t_cost, t_solar, t_batt_dis, t_batt_chg = 0, 0, 0, 0

        # --- NEW PEAK GRID LOAD LOGIC ---
        hourly_grid_load = [0.0] * 24
        for hour in range(24):
            # For each hour, sum power of appliances that are ON
            for aid, v in task_vars.items():
                start_min = solver.Value(v['start']) * 15
                end_min = solver.Value(v['end']) * 15
                # If appliance is ON during this hour
                if start_min <= hour * 60 < end_min:
                    hourly_grid_load[hour] += v['pwr']
        peak_grid_hourly = max(hourly_grid_load)

        # --- Time series and other stats (unchanged) ---
        peak_load = 0
        for t in range(NUM_T):
            g_kW = solver.Value(grid[t]) / 1000.0
            d_kW = solver.Value(discharge[t]) / 1000.0
            c_kW = solver.Value(charge[t]) / 1000.0
            s_kW = solar[t]

            l_kW = sum(v['pwr'] for v in task_vars.values() if solver.Value(v['start']) <= t < solver.Value(v['end']))

            if g_kW > peak_load: peak_load = g_kW

            step_cost = g_kW * 0.25 * prices[t]
            t_cost += step_cost
            t_solar += min(l_kW, s_kW) * 0.25
            t_batt_dis += d_kW * 0.25
            t_batt_chg += c_kW * 0.25

            ts_data.append(TimeStepData(
                time=f"{t//4:02d}:{(t%4)*15:02d}",
                grid=round(g_kW, 2),
                solar=round(s_kW, 2),
                battery=round(d_kW - c_kW, 2),
                load=round(l_kW, 2),
                cost=round(step_cost, 4)
            ))

        total_demand_kWh = sum(v['pwr'] * (v['dur_min'] / 60) for v in task_vars.values())
        # ...existing code...
        total_baseline_cost = sum(item['baseline_cost'] for item in res_sched)

        summary = {
            "baseline_cost": round(total_baseline_cost, 2),
            "optimized_cost": round(t_cost, 2),
            "price_saved": round(max(0, total_baseline_cost - t_cost), 2),
            "total_energy_kWh": round(total_demand_kWh, 2),
            "solar_energy_kWh": round(t_solar, 2),
            "battery_usage_kWh": round(t_batt_dis, 2),
            "peak_grid_kW": round(peak_grid_hourly, 2),
            "savings_percentage": round(((total_baseline_cost - t_cost)/max(1, total_baseline_cost) * 100), 1) if total_baseline_cost > 0 else 0
        }

        # ...existing code...

        # SAVE TO HISTORY
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO history (timestamp, summary, schedule) VALUES (?,?,?)",
                       (datetime.now().strftime("%Y-%m-%d %H:%M"), json.dumps(summary), json.dumps(res_sched)))
        conn.commit()
        conn.close()

        return OptimizationResponse(status="Success", schedule=res_sched, summary=summary, time_series=ts_data,
                                    suggestions=[f"Solar PV handled {round((t_solar/max(0.1, total_demand_kWh))*100)}% of your load.", f"Battery storage deferred {round(t_batt_dis, 2)} kWh to avoid high rates."])
    
    return {"status": "Infeasible", "suggestions": ["Constraint violation. Try relaxing priority or window limits."]}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
