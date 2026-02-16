let chartInstance = null;
let currentData = null;

async function fetchAndRender() {
    try {
        const res = await fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await res.json();

        if (data.status === "Success") {
            currentData = data;
            // Sort schedule by start time for a proper "Time Table" feel
            currentData.schedule.sort((a, b) => a.start - b.start);
            renderChart('line');
            renderTimeline(currentData.schedule);
            updateTable(currentData.schedule);
        } else {
            alert("No optimization data found. Please run the solver on the Dashboard first.");
        }
    } catch (e) {
        console.error("Load failed", e);
    }
}

function changeChartType(type, btn) {
    document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    renderChart(type);
}

// Function to toggle datasets from custom legend
function toggleDataset(index) {
    if (!chartInstance) return;
    const meta = chartInstance.getDatasetMeta(index);
    meta.hidden = meta.hidden === null ? !chartInstance.data.datasets[index].hidden : null;
    chartInstance.update();

    // UI Feedback for the custom legend can be added here if needed
}

function renderChart(type) {
    if (!currentData) return;
    const ts = currentData.time_series;
    const ctx = document.getElementById('detailedChart').getContext('2d');

    if (chartInstance) chartInstance.destroy();

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index',
            intersect: false
        },
        plugins: {
            legend: { display: false }, // Use custom HTML legend
            tooltip: {
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                titleColor: '#1b4332',
                bodyColor: '#1b4332',
                borderColor: '#d1fae5',
                borderWidth: 1,
                padding: 15,
                titleFont: { size: 14, weight: 'bold' },
                bodyFont: { size: 13 },
                callbacks: {
                    label: function (context) {
                        return ` ${context.dataset.label}: ${context.parsed.y} kW`;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: { display: true, text: 'Power (kW)', font: { weight: 'bold' } },
                grid: { color: 'rgba(0,0,0,0.03)' }
            },
            x: {
                grid: { display: false },
                ticks: { maxTicksLimit: 12 }
            }
        }
    };

    if (type === 'radar') {
        const labels = ['Night (00-06)', 'Morning (06-12)', 'Afternoon (12-18)', 'Evening (18-00)'];
        const getAvg = (arr, start, end) => arr.slice(start, end).reduce((a, b) => a + b, 0) / (end - start);

        const gridData = [getAvg(ts.map(s => s.grid), 0, 24), getAvg(ts.map(s => s.grid), 24, 48), getAvg(ts.map(s => s.grid), 48, 72), getAvg(ts.map(s => s.grid), 72, 96)];
        const solarData = [getAvg(ts.map(s => s.solar), 0, 24), getAvg(ts.map(s => s.solar), 24, 48), getAvg(ts.map(s => s.solar), 48, 72), getAvg(ts.map(s => s.solar), 72, 96)];
        const batteryData = [getAvg(ts.map(s => Math.abs(s.battery)), 0, 24), getAvg(ts.map(s => Math.abs(s.battery)), 24, 48), getAvg(ts.map(s => Math.abs(s.battery)), 48, 72), getAvg(ts.map(s => Math.abs(s.battery)), 72, 96)];

        chartInstance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [
                    { label: 'Grid Usage', data: gridData, borderColor: '#4338ca', backgroundColor: 'rgba(67, 56, 202, 0.2)', fill: true },
                    { label: 'Solar Gen', data: solarData, borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.2)', fill: true },
                    { label: 'Battery Activity', data: batteryData, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.2)', fill: true }
                ]
            },
            options: commonOptions
        });
        return;
    }

    const datasets = [
        {
            label: 'Grid Intake',
            data: ts.map(s => s.grid),
            borderColor: '#4338ca',
            backgroundColor: type === 'line' ? 'rgba(67, 56, 202, 0.08)' : '#4338ca',
            fill: type === 'line',
            tension: 0.4,
            pointRadius: 0
        },
        {
            label: 'Solar Output',
            data: ts.map(s => s.solar),
            borderColor: '#f59e0b',
            backgroundColor: type === 'line' ? 'rgba(245, 158, 11, 0.08)' : '#f59e0b',
            fill: type === 'line',
            tension: 0.4,
            pointRadius: 0
        },
        {
            label: 'Storage Flow',
            data: ts.map(s => s.battery),
            borderColor: '#10b981',
            backgroundColor: type === 'line' ? 'rgba(16, 185, 129, 0.08)' : '#10b981',
            fill: type === 'line',
            tension: 0.4,
            pointRadius: 0
        },
        {
            label: 'Home Load',
            data: ts.map(s => s.load),
            borderColor: '#1b4332',
            borderWidth: 2,
            borderDash: type === 'line' ? [6, 4] : [],
            fill: false,
            tension: 0.2,
            type: 'line',
            pointRadius: 0
        }
    ];

    chartInstance = new Chart(ctx, {
        type: type,
        data: {
            labels: ts.map(s => s.time),
            datasets: datasets
        },
        options: commonOptions
    });
}

function renderTimeline(schedule) {
    const container = document.getElementById('timeline-container');
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

    schedule.forEach((item, idx) => {
        const label = document.createElement('div');
        label.className = 'app-row app-label';
        label.style.fontWeight = '800';
        label.style.display = 'flex';
        label.style.alignItems = 'center';
        label.style.padding = '12px 15px';
        label.style.fontSize = '0.85rem';
        label.style.borderBottom = '1px solid #f1f5f9';
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

function updateTable(schedule) {
    const tbody = document.getElementById('timetable-list');
    if (!tbody) return;
    tbody.innerHTML = schedule.map((item, idx) => `
        <tr style="animation: fadeIn 0.4s ease forwards; animation-delay: ${idx * 0.05}s">
            <td style="font-weight:900; color:var(--leaf)">${item.name || 'Unknown Unit'}</td>
            <td><span class="priority-pill prio-${item.pri}">${getPrioLabel(item.pri)}</span></td>
            <td style="font-weight: 800; color: var(--primary);">${formatTime(item.start)} - ${formatTime(item.end)}</td>
            <td style="font-size: 0.9rem; line-height: 1.2;">
                <div style="color:var(--moss); text-decoration:line-through; font-size:0.75rem;">₹${(item.baseline_cost || 0).toFixed(2)}</div>
                <div style="font-weight:900;">₹${(item.optimized_cost || 0).toFixed(2)}</div>
            </td>
            <td style="font-size: 0.9rem; line-height: 1.6; color: var(--moss); max-width: 350px;">${item.why || 'Strategic schedule optimization.'}</td>
            <td style="font-weight: 900; color: var(--leaf);">₹${(item.saving || 0).toFixed(2)}</td>
        </tr>
    `).join('');
}

function getPrioLabel(p) {
    if (p >= 5) return 'Critical';
    if (p >= 4) return 'Essential';
    if (p >= 3) return 'Standard';
    if (p >= 2) return 'Flexible';
    return 'Deferrable';
}

function formatTime(m) {
    return `${Math.floor(m / 60).toString().padStart(2, '0')}:${(m % 60).toString().padStart(2, '0')}`;
}

window.onload = fetchAndRender;
