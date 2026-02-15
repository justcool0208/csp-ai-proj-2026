// --- NAVIGATION ---
function showSection(id) {
    document.querySelectorAll('.view-section').forEach(s => s.classList.add('hidden'));
    document.getElementById(`section-${id}`).classList.remove('hidden');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    const navBtn = document.getElementById(`nav-${id}`);
    if (navBtn) navBtn.classList.add('active');

    if (id === 'history') fetchHistory();
}

// --- DATA FETCHING ---
async function fetchApps() {
    const res = await fetch('/api/appliances');
    const apps = await res.json();
    const tbody = document.getElementById('app-list');
    tbody.innerHTML = '';

    apps.forEach(app => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-weight:900; color:var(--primary)">${app.name}</td>
            <td style="font-weight:700;">${app.power} kW</td>
            <td style="font-weight:700;">${app.duration} mins</td>
            <td><span class="priority-pill prio-${app.priority}">${getPrioLabel(app.priority)}</span></td>
            <td style="font-weight:600; color:var(--moss);">${formatTime(app.earliest_start)} - ${formatTime(app.latest_end)}</td>
            <td><button onclick="deleteApp('${app.id}')" style="background:transparent; border:none; color:var(--danger); cursor:pointer;"><i data-lucide="trash-2" width="20"></i></button></td>
        `;
        tbody.appendChild(tr);
    });
    lucide.createIcons();
}

function getPrioLabel(p) {
    if (p >= 5) return 'Critical';
    if (p >= 4) return 'Essential';
    if (p >= 3) return 'Standard';
    if (p >= 2) return 'Flexible';
    return 'Deferrable';
}

async function addApp(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Syncing Logic...';
    lucide.createIcons();

    try {
        const app = {
            id: Date.now().toString(),
            name: document.getElementById('in_name').value,
            power: parseFloat(document.getElementById('in_pwr').value),
            duration: parseInt(document.getElementById('in_dur').value),
            earliest_start: timeToMins(document.getElementById('in_start').value),
            latest_end: timeToMins(document.getElementById('in_end').value),
            priority: parseInt(document.getElementById('in_prio').value)
        };
        const res = await fetch('/api/appliances', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(app)
        });

        if (res.ok) {
            document.getElementById('modal-overlay').classList.add('hidden');
            document.getElementById('app-form').reset();
            await fetchApps();
            runBatchTest();
        } else {
            const err = await res.json();
            alert("Feasibility Violation: " + err.detail);
        }
    } catch (e) {
        alert("Transmission failure.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

async function runBatchTest() {
    const btn = document.getElementById('optimize-btn');
    if (!btn) return;
    const original = btn.innerHTML;
    btn.innerHTML = '<i data-lucide="cog" class="spin"></i> Computing Optima...';
    lucide.createIcons();

    const gridLimit = parseFloat(document.getElementById('grid-limit').value) || 12.0;

    try {
        const res = await fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ max_power_limit: gridLimit })
        });
        const data = await res.json();

        if (data.status === "Success") {
            updateDashboard(data);
        } else {
            alert("Constraint Infeasibility: " + data.suggestions[0]);
        }
    } catch (e) {
        console.error(e);
    } finally {
        btn.innerHTML = original;
        lucide.createIcons();
    }
}

function updateDashboard(data) {
    const s = data.summary;

    // Core Metrics
    document.getElementById('res-cost').innerHTML = `<span style="font-size: 1.2rem; opacity: 0.6;">₹</span>${s.optimized_cost}`;
    document.getElementById('res-solar').textContent = s.solar_energy_kWh + ' kWh';
    document.getElementById('res-batt').textContent = s.battery_usage_kWh + ' kWh';

    // Impact Visuals
    const pctLabel = document.getElementById('percent-saved');
    pctLabel.textContent = `${s.savings_percentage}% Efficiency Gain`;
    document.getElementById('baseline-cost').textContent = '₹' + s.baseline_cost;
    document.getElementById('optimized-cost').textContent = '₹' + s.optimized_cost;
    document.getElementById('total-savings').textContent = '₹' + s.price_saved;
    document.getElementById('peak-load').textContent = s.peak_grid_kW + ' kW';
    // Sort schedule by start time for a proper "Time Table" feel
    data.schedule.sort((a, b) => a.start - b.start);

    // Timeline Visualization
    renderTimeline(data.schedule);

    // Detailed Table
    const tbody = document.getElementById('timetable-list');
    tbody.innerHTML = data.schedule.map((item, idx) => `
        <tr style="animation: fadeIn 0.4s ease forwards; animation-delay: ${idx * 0.05}s">
            <td style="font-weight:900; color:var(--leaf)">${item.name || 'Unknown Appliance'}</td>
            <td><span class="priority-pill prio-${item.pri}">${getPrioLabel(item.pri)}</span></td>
            <td style="font-weight: 800; color: var(--primary);">${formatTime(item.start)} - ${formatTime(item.end)}</td>
            <td style="font-size: 0.9rem; line-height: 1.2;">
                <div style="color:var(--moss); text-decoration:line-through; font-size:0.75rem;">₹${(item.baseline_cost || 0).toFixed(2)}</div>
                <div style="font-weight:900;">₹${(item.optimized_cost || 0).toFixed(2)}</div>
            </td>
            <td style="font-size: 0.9rem; line-height: 1.6; color: var(--moss); max-width: 350px;">${item.why || 'Constraint-based scheduling.'}</td>
            <td style="font-weight: 900; color: var(--leaf);">₹${(item.saving || 0).toFixed(2)}</td>
        </tr>
    `).join('');
}

function printTimetable() {
    window.print();
}

function renderTimeline(schedule) {
    const container = document.getElementById('dashboard-timeline');
    if (!container) return;
    container.innerHTML = '';

    // Time Header
    const labelHeader = document.createElement('div');
    labelHeader.style.padding = '15px';
    labelHeader.style.background = '#f1f5f9';
    labelHeader.style.borderBottom = '2px solid var(--border)';
    container.appendChild(labelHeader);

    const timeRow = document.createElement('div');
    timeRow.className = 'time-header';
    timeRow.style.display = 'flex';
    timeRow.style.justifyContent = 'space-between';
    timeRow.style.padding = '15px';
    timeRow.style.background = '#f1f5f9';
    timeRow.style.borderBottom = '2px solid var(--border)';

    for (let i = 0; i <= 24; i += 2) {
        const span = document.createElement('span');
        span.textContent = `${i.toString().padStart(2, '0')}:00`;
        span.style.fontSize = '0.7rem';
        span.style.fontWeight = '900';
        span.style.color = '#64748b';
        timeRow.appendChild(span);
    }
    container.appendChild(timeRow);

    // Vertical Time Grid Lines Overlay
    const gridOverlay = document.createElement('div');
    gridOverlay.style.position = 'absolute';
    gridOverlay.style.top = '0';
    gridOverlay.style.left = '180px';
    gridOverlay.style.right = '0';
    gridOverlay.style.bottom = '0';
    gridOverlay.style.pointerEvents = 'none';
    gridOverlay.style.display = 'flex';
    gridOverlay.style.justifyContent = 'space-between';
    for (let i = 0; i <= 24; i += 2) {
        const line = document.createElement('div');
        line.style.width = '1px';
        line.style.height = '100%';
        line.style.background = 'rgba(203, 213, 225, 0.3)';
        gridOverlay.appendChild(line);
    }
    // container.appendChild(gridOverlay); // Optional: can be messy on scrolling

    schedule.forEach((item, idx) => {
        const label = document.createElement('div');
        label.className = 'app-label';
        label.style.padding = '12px 15px';
        label.style.fontWeight = '800';
        label.style.fontSize = '0.85rem';
        label.style.borderBottom = '1px solid #f1f5f9';
        label.style.display = 'flex';
        label.style.alignItems = 'center';
        label.innerHTML = `<i data-lucide="cpu" width="14" style="margin-right:8px; color:var(--leaf)"></i> ${item.name}`;
        container.appendChild(label);

        const track = document.createElement('div');
        track.style.position = 'relative';
        track.style.height = '45px';
        track.style.background = idx % 2 === 0 ? '#ffffff' : '#f8fafc';
        track.style.borderBottom = '1px solid #f1f5f9';

        const startPct = (item.start / 1440) * 100;
        const widthPct = ((item.end - item.start) / 1440) * 100;

        const bar = document.createElement('div');
        bar.className = 'timeline-bar';
        bar.style.position = 'absolute';
        bar.style.left = `${startPct}%`;
        bar.style.width = `${widthPct}%`;
        bar.style.height = '28px';
        bar.style.top = '8px';
        bar.style.display = 'flex';
        bar.style.alignItems = 'center';
        bar.style.justifyContent = 'center';
        bar.style.color = 'white';
        bar.style.fontSize = '0.65rem';
        bar.style.fontWeight = '900';
        bar.style.borderRadius = '6px';
        bar.style.background = 'linear-gradient(90deg, #1b4332, #2d6a4f)';
        bar.style.boxShadow = '0 4px 12px rgba(27, 67, 50, 0.1)';
        bar.textContent = `${formatTime(item.start)}`;

        track.appendChild(bar);
        container.appendChild(track);
    });
    lucide.createIcons();
}

async function fetchHistory() {
    try {
        const res = await fetch('/api/history');
        const logs = await res.json();
        const container = document.getElementById('history-list');

        if (!logs.length) {
            container.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 4rem; background: white; border-radius: 30px; border: 2px dashed var(--border);">
                    <i data-lucide="archive" width="48" style="color: var(--mint); margin-bottom: 1rem;"></i>
                    <p style="color: var(--moss); font-weight: 700;">No archived system states found.</p>
                </div>`;
            return;
        }

        container.innerHTML = logs.map((log, idx) => {
            const appNames = log.schedule.slice(0, 3).map(a => a.name).join(', ');
            const moreCount = log.schedule.length > 3 ? ` +${log.schedule.length - 3} more` : '';

            return `
            <div class="card" style="padding: 1.8rem; animation: fadeIn 0.4s ease forwards; animation-delay: ${idx * 0.05}s">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.2rem;">
                    <div>
                        <h4 style="font-size: 1.1rem; color: var(--leaf); margin-bottom: 4px;">Archive #${log.id}</h4>
                        <div style="font-size: 0.8rem; font-weight: 700; color: var(--moss); opacity: 0.7;">
                            <i data-lucide="calendar" width="12" style="vertical-align: middle;"></i> ${log.timestamp}
                        </div>
                    </div>
                    <div style="background: var(--nature-white); padding: 8px 12px; border-radius: 12px; border: 1px solid var(--border);">
                        <span style="font-weight: 900; color: var(--leaf); font-size: 0.9rem;">${log.summary.savings_percentage}% Saved</span>
                    </div>
                </div>
                
                <div style="background: #f8fafc; padding: 1rem; border-radius: 15px; margin-bottom: 1.2rem; font-size: 0.85rem;">
                    <div style="display: flex; align-items: center; gap: 8px; color: var(--primary); font-weight: 800; margin-bottom: 4px;">
                        <i data-lucide="cpu" width="14"></i> ${log.schedule.length} Appliances Optimized
                    </div>
                    <div style="color: var(--moss); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; opacity: 0.8;">
                        ${appNames}${moreCount}
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 0.85rem;">
                    <div class="stat-mini">
                        <span style="display:block; opacity: 0.6; font-size: 0.7rem; font-weight: 800; text-transform: uppercase;">Cost Reduction</span>
                        <strong style="font-size: 1.1rem; color: var(--primary);">₹${log.summary.price_saved}</strong>
                    </div>
                    <div class="stat-mini">
                        <span style="display:block; opacity: 0.6; font-size: 0.7rem; font-weight: 800; text-transform: uppercase;">Solar Utilized</span>
                        <strong style="font-size: 1.1rem; color: var(--solar);">${log.summary.solar_energy_kWh} <small style="font-size: 0.6rem;">kWh</small></strong>
                    </div>
                    <div class="stat-mini">
                        <span style="display:block; opacity: 0.6; font-size: 0.7rem; font-weight: 800; text-transform: uppercase;">Peak Demand</span>
                        <strong style="font-size: 1.1rem; color: var(--grid);">${log.summary.peak_grid_kW} <small style="font-size: 0.6rem;">kW</small></strong>
                    </div>
                    <div class="stat-mini">
                        <span style="display:block; opacity: 0.6; font-size: 0.7rem; font-weight: 800; text-transform: uppercase;">Storage Depth</span>
                        <strong style="font-size: 1.1rem; color: var(--battery);">${log.summary.battery_usage_kWh} <small style="font-size: 0.6rem;">kWh</small></strong>
                    </div>
                </div>
            </div>
        `}).join('');
        lucide.createIcons();
    } catch (e) { console.error(e); }
}

async function clearHistory() {
    if (!confirm('Permanently purge all archived optimization logs?')) return;
    try {
        await fetch('/api/history', { method: 'DELETE' });
        fetchHistory();
    } catch (e) { alert('Purge failed.'); }
}

// --- UTILS ---
function formatTime(m) {
    return `${Math.floor(m / 60).toString().padStart(2, '0')}:${(m % 60).toString().padStart(2, '0')}`;
}
function timeToMins(t) {
    const [h, m] = t.split(':').map(Number);
    return h * 60 + m;
}
async function deleteApp(id) {
    if (confirm('Permanently de-register this system load?')) {
        await fetch(`/api/appliances/${id}`, { method: 'DELETE' });
        fetchApps();
        runBatchTest();
    }
}
async function resetDefaults() {
    if (confirm('Restore industrial reference simulation? This will over-write current configuration.')) {
        await fetch('/api/reset', { method: 'POST' });
        location.reload();
    }
}

// --- INITIALIZATION ---
const overlay = document.getElementById('modal-overlay');
if (overlay) {
    document.getElementById('close-btn').onclick = () => overlay.classList.add('hidden');
    document.getElementById('add-btn').onclick = () => overlay.classList.remove('hidden');
    overlay.onclick = (e) => { if (e.target === overlay) overlay.classList.add('hidden'); };
}

const appForm = document.getElementById('app-form');
if (appForm) appForm.onsubmit = addApp;

const optimizeBtn = document.getElementById('optimize-btn');
if (optimizeBtn) optimizeBtn.onclick = runBatchTest;

window.onload = async () => {
    await fetchApps();
    runBatchTest();
};
