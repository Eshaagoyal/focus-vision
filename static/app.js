// --- Chart Setup ---
const ctx = document.getElementById('focusChart').getContext('2d');
const focusChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Attention Score',
            data: [],
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.2)',
            borderWidth: 2,
            fill: true,
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { min: 0, max: 105, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
            x: { grid: { display: false }, ticks: { display: false } }
        },
        plugins: {
            legend: { display: false }
        },
        animation: { duration: 0 }
    }
});

const stateColors = {
    'ATTENTIVE': '#10b981',
    'DISTRACTED': '#f59e0b',
    'NOT FOCUSED': '#f59e0b',
    'DROWSY': '#8b5cf6',
    'PHONE DETECTED': '#ef4444',
    'TOO CLOSE': '#3b82f6'
};

let scoreHistory = [];
let stateHistory = [];
let audioPlayed = false;

// --- API Calls ---

function updateDashboard() {
    fetch('/metrics')
        .then(response => response.json())
        .then(data => {
            const metrics = data.metrics;
            const state = data.app_state;

            // Update App State
            document.getElementById('app-state-badge').innerText = state;
            document.getElementById('session-time').innerText = metrics.session_time_str;

            // Update UI Colors
            const scoreVal = document.getElementById('score-val');
            const stateVal = document.getElementById('state-val');
            const progressCircle = document.querySelector('.progress-ring__circle');

            scoreVal.innerText = metrics.score;
            stateVal.innerText = metrics.state;

            let color = '#ef4444'; // Red
            if (metrics.score >= 70) color = '#10b981'; // Green
            else if (metrics.score >= 40) color = '#f59e0b'; // Orange

            progressCircle.style.stroke = color;
            stateVal.style.color = color;

            // Circle math (Circumference is ~326.72)
            const offset = 326.72 - (metrics.score / 100) * 326.72;
            progressCircle.style.strokeDashoffset = offset;

            // Update Stats
            document.getElementById('head-val').innerText = metrics.head_dir;
            document.getElementById('gaze-val').innerText = metrics.gaze_dir;
            document.getElementById('eyes-val').innerText = metrics.eye_state;
            document.getElementById('dist-val').innerText = metrics.distractions;
            document.getElementById('avg-val').innerText = metrics.avg_score;

            let streakText = "None";
            if (metrics.streak_stars > 0) streakText = "⭐".repeat(metrics.streak_stars);
            document.getElementById('streak-val').innerText = streakText;

            // Update Chart
            if (state === "ACTIVE") {
                scoreHistory.push(metrics.score);
                stateHistory.push(metrics.state);
                
                if (scoreHistory.length > 60) {
                    scoreHistory.shift();
                    stateHistory.shift();
                }

                focusChart.data.labels = scoreHistory.map((_, i) => i);
                focusChart.data.datasets[0].data = scoreHistory;
                focusChart.data.datasets[0].pointBackgroundColor = stateHistory.map(s => stateColors[s] || '#10b981');
                focusChart.data.datasets[0].pointBorderColor = stateHistory.map(s => stateColors[s] || '#10b981');
                focusChart.data.datasets[0].pointRadius = stateHistory.map(s => s === 'ATTENTIVE' ? 0 : 5);
                focusChart.data.datasets[0].borderColor = color;
                focusChart.update();

                // AI Voice Alert Logic
                if (metrics.alert_active) {
                    if (!audioPlayed) {
                        let alertText = "Attention! Please focus on your screen.";
                        if (metrics.state === "PHONE DETECTED") alertText = "Mobile phone detected. Please put it away.";
                        else if (metrics.state === "DROWSY") alertText = "You seem drowsy. Please take a short break.";
                        else if (metrics.state === "TOO CLOSE") alertText = "You are sitting too close. Please protect your eyes.";
                        
                        const msg = new SpeechSynthesisUtterance(alertText);
                        msg.rate = 1.1;
                        window.speechSynthesis.speak(msg);
                        audioPlayed = true;
                    }
                } else {
                    audioPlayed = false;
                }
            }
        })
        .catch(err => console.error("Error fetching metrics:", err));
}

// Poll every second
setInterval(updateDashboard, 1000);

// --- Controls ---

function controlSession(action) {
    fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
    });
}

function stopServer() {
    if (confirm("Are you sure you want to completely shut down the tracker?")) {
        fetch('/api/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'stop' })
        });
        document.body.innerHTML = "<h1 style='color:white; text-align:center; margin-top:20vh;'>Tracker Stopped. You can close this tab.</h1>";
    }
}

function setTimer() {
    const hrs = parseInt(document.getElementById('timer-hrs').value) || 0;
    const mins = parseInt(document.getElementById('timer-mins').value) || 0;
    const secs = parseInt(document.getElementById('timer-secs').value) || 0;
    
    const totalSecs = (hrs * 3600) + (mins * 60) + secs;
    
    if (totalSecs <= 0) {
        alert("Please enter a valid time greater than 0.");
        return;
    }
    
    fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'set_timer', seconds: totalSecs })
    });
}

// --- Tabs & Insights ---

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

    document.getElementById('tab-' + tabName).classList.add('active');
    event.target.classList.add('active');
}

function saveTag(sessionId, inputId) {
    const tag = document.getElementById(inputId).value;
    fetch('/api/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: sessionId, tag: tag })
    }).then(res => res.json()).then(data => {
        if (data.status === 'success') {
            alert('Tag saved successfully!');
        }
    });
}

let modalChartInstance = null;
let globalSessionsData = [];

function openModal(index) {
    const session = globalSessionsData[index];
    document.getElementById('modal-title').innerText = `Session Details: ${session.date} at ${session.time}`;
    document.getElementById('chart-modal').classList.add('active');

    if (modalChartInstance) {
        modalChartInstance.destroy();
    }

    modalChartInstance = new Chart(document.getElementById('modal-canvas').getContext('2d'), {
        type: 'line',
        data: {
            labels: session.history.map((_, i) => {
                let totalSecs = i * 5;
                let m = Math.floor(totalSecs / 60);
                let s = totalSecs % 60;
                return `${m}m ${s}s`;
            }),
            datasets: [{
                label: 'Focus Score',
                data: session.history,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                borderWidth: 2,
                pointBackgroundColor: session.history_states ? session.history_states.map(s => stateColors[s] || '#10b981') : '#10b981',
                pointBorderColor: session.history_states ? session.history_states.map(s => stateColors[s] || '#10b981') : '#10b981',
                pointRadius: session.history_states ? session.history_states.map(s => s === 'ATTENTIVE' ? 2 : 6) : 2,
                pointHoverRadius: 8,
                fill: true,
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: { display: true, min: 0, max: 105, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                x: { display: true, ticks: { color: '#94a3b8', maxTicksLimit: 20 }, grid: { color: 'rgba(255,255,255,0.05)' } }
            },
            plugins: {
                legend: { display: false },
                tooltip: { 
                    enabled: true, 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    titleColor: '#fff', 
                    bodyColor: '#fff', 
                    titleFont: { size: 14 }, 
                    bodyFont: { size: 16 },
                    callbacks: {
                        label: function(context) {
                            let score = context.raw;
                            let state = session.history_states ? session.history_states[context.dataIndex] : "UNKNOWN";
                            return `Score: ${score} ⚠ Reason: ${state}`;
                        }
                    }
                }
            }
        }
    });
}

function closeModal() {
    document.getElementById('chart-modal').classList.remove('active');
}

function fetchInsights() {
    Promise.all([
        fetch('/api/insights').then(res => res.json()),
        fetch('/api/tags').then(res => res.json())
    ]).then(([data, tagsData]) => {
        const grid = document.getElementById('insights-grid');
        const globalContainer = document.getElementById('insights-global');

        grid.innerHTML = '';
        globalContainer.innerHTML = '';

        if (!data.sessions || data.sessions.length === 0) {
            grid.innerHTML = '<p>No session logs found yet. Complete a session to see insights!</p>';
            return;
        }

        // 1. Render Global Stats
        const stats = data.global_stats;
        globalContainer.innerHTML = `
            <div class="global-stat-box"><h4>Total Focused</h4><span>${stats.total_hours} hr</span></div>
            <div class="global-stat-box"><h4>Global Average</h4><span>${stats.overall_avg}</span></div>
            <div class="global-stat-box"><h4>Peak Time</h4><span class="accent">${stats.best_time}</span></div>
        `;

        // 2. Render Session Cards
        globalSessionsData = data.sessions.reverse();
        globalSessionsData.forEach((session, index) => {
            const mins = Math.floor(session.duration_secs / 60);
            const secs = session.duration_secs % 60;
            const currentTag = tagsData[session.id] || "";

            const card = document.createElement('div');
            card.className = 'insight-card';
            card.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 0.5rem;">
                    <h3 style="margin:0; font-size:1.1rem;">📅 ${session.date} - ${session.time}</h3>
                    <button class="small-btn" onclick="openModal(${index})" style="background: transparent; border: 1px solid var(--accent); color: var(--accent);">🔍 Expand Graph</button>
                </div>
                
                <div class="tag-input-container">
                    <input type="text" id="tag-${index}" placeholder="Add session tag (e.g., Coding)" value="${currentTag}">
                    <button class="small-btn" onclick="saveTag('${session.id}', 'tag-${index}')">Save</button>
                </div>

                <div class="stat-badges">
                    <div class="stat-badge">Duration: <span>${mins}m ${secs}s</span></div>
                    <div class="stat-badge">Avg Score: <span>${session.avg_score}</span></div>
                    <div class="stat-badge">Distraction: <span style="color:var(--warning);">${session.primary_distraction}</span></div>
                </div>
                
                <div class="card-charts-row">
                    <div class="card-chart-wrapper">
                        <span class="chart-title" style="text-align:center;">State Distribution</span>
                        <canvas id="pie-chart-${index}"></canvas>
                    </div>
                </div>
            `;
            grid.appendChild(card);

            // Render Pie Chart
            const dist = session.state_distribution;
            new Chart(document.getElementById(`pie-chart-${index}`).getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Attentive', 'Distracted', 'Drowsy', 'Phone', 'Posture'],
                    datasets: [{
                        data: [dist.Attentive, dist.Distracted, dist.Drowsy, dist.Phone, dist.Posture],
                        backgroundColor: ['#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#3b82f6'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: true, backgroundColor: 'rgba(15, 23, 42, 0.9)' }
                    },
                    cutout: '70%',
                    animation: false
                }
            });
        });
    });
}
