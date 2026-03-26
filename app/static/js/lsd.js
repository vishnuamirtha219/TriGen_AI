// Tab Switching
function switchTab(tab) {
    const manualBtn = document.getElementById('tab-manual');
    const uploadBtn = document.getElementById('tab-upload');
    const manualSec = document.getElementById('manual-section');
    const uploadSec = document.getElementById('upload-section');

    if (tab === 'manual') {
        manualBtn.style.borderBottom = '2px solid #10b981';
        manualBtn.style.color = '#10b981';
        uploadBtn.style.borderBottom = 'none';
        uploadBtn.style.color = 'var(--text-muted)';
        manualSec.style.display = 'block';
        uploadSec.style.display = 'none';
    } else {
        uploadBtn.style.borderBottom = '2px solid #10b981';
        uploadBtn.style.color = '#10b981';
        manualBtn.style.borderBottom = 'none';
        manualBtn.style.color = 'var(--text-muted)';
        uploadSec.style.display = 'block';
        manualSec.style.display = 'none';
    }
}

// File Upload
async function handleFileUpload(input) {
    if (!input.files || !input.files[0]) return;

    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const statusEl = document.getElementById('upload-status');
    statusEl.innerHTML = '<span class="loader" style="width:16px;height:16px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:0.5rem;"></span> Parsing file with AI...';
    statusEl.style.color = 'var(--primary)';

    try {
        const response = await fetch('/api/parse_file', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.success && result.data) {
            // Broad mapping: support multiple key name variants
            const map = {
                'beta_glucosidase': 'b_glucosidase', 'b_glucosidase': 'b_glucosidase',
                'glucosidase': 'b_glucosidase', 'beta-glucosidase': 'b_glucosidase',
                'alpha_galactosidase': 'a_galactosidase', 'a_galactosidase': 'a_galactosidase',
                'galactosidase': 'a_galactosidase', 'alpha-galactosidase': 'a_galactosidase',
                'liver_size': 'liver_size', 'liver': 'liver_size', 'hepatic_size': 'liver_size',
                'spleen_size': 'spleen_size', 'spleen': 'spleen_size', 'splenic_size': 'spleen_size'
            };

            let filled = 0;
            let filledNames = [];
            for (const [key, val] of Object.entries(result.data)) {
                const targetId = map[key];
                if (targetId && document.getElementById(targetId)) {
                    document.getElementById(targetId).value = val;
                    filled++;
                    filledNames.push(targetId.replace('_', ' ').replace('b glucosidase', 'β-Glucosidase').replace('a galactosidase', 'α-Galactosidase').replace('liver size', 'Liver Size').replace('spleen size', 'Spleen Size'));
                }
            }

            if (filled > 0) {
                statusEl.innerHTML = `✅ Extracted ${filled} parameter(s): ${filledNames.join(', ')}. Switching to form...`;
                statusEl.style.color = 'var(--success)';
                setTimeout(() => switchTab('manual'), 1500);
            } else {
                statusEl.innerHTML = `
                    <div style="text-align: left; padding: 1rem; background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 8px; margin-top: 0.5rem;">
                        <p style="color: var(--warning); font-weight: 600; margin-bottom: 0.5rem;">⚠️ No LSD parameters found in this file</p>
                        <p style="color: var(--text-main); font-size: 0.85rem; margin-bottom: 0.5rem;">LSD analysis requires specialized lab results:</p>
                        <ul style="color: var(--text-muted); font-size: 0.8rem; margin: 0; padding-left: 1.25rem;">
                            <li>Enzyme assay report (β-Glucosidase, α-Galactosidase activity)</li>
                            <li>Abdominal ultrasound (liver/spleen measurements)</li>
                            <li>CSV file with columns: b_glucosidase, a_galactosidase, liver_size, spleen_size</li>
                        </ul>
                        <p style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.5rem;">You can also enter values manually using the <strong>Manual Entry</strong> tab.</p>
                    </div>`;
            }
        } else {
            statusEl.textContent = 'Could not parse file. Please try a different format.';
            statusEl.style.color = 'var(--danger)';
        }
    } catch (e) {
        console.error(e);
        statusEl.textContent = 'Error uploading file. Please try again.';
        statusEl.style.color = 'var(--danger)';
    }
}

// Chart Logic
let chartInstance = null;

// Animated gauge fill
function animateGauge(targetProbability, riskLevel) {
    const duration = 1200;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const currentValue = targetProbability * eased;

        renderChart(currentValue, riskLevel);
        document.getElementById('prob-val').textContent = Math.round(currentValue) + '%';

        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function renderChart(probability, riskLevel) {
    const ctx = document.getElementById('lsdChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    const remaining = 100 - probability;
    let color = '#10b981';
    if (riskLevel === 'High') color = '#ef4444';
    else if (riskLevel === 'Medium') color = '#f59e0b';

    chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Risk', 'Safe'],
            datasets: [{
                data: [probability, remaining],
                backgroundColor: [color, 'rgba(0, 0, 0, 0.06)'],
                borderWidth: 0,
                cutout: '85%',
                circumference: 180,
                rotation: 270,
            }]
        },
        options: {
            responsive: true,
            aspectRatio: 2,
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            animation: { duration: 0 }
        }
    });
}

document.getElementById('lsd-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerHTML = '<span class="loader" style="width:18px;height:18px;border-width:2px;border-top-color:white;"></span> Calculating...';

    if (window.showLoader) window.showLoader('Assessing risk factors...');

    try {
        const response = await fetch('/api/predict/lsd', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (window.hideLoader) window.hideLoader();

        const panel = document.getElementById('result-panel');
        panel.style.display = 'block';
        panel.classList.add('animate-fade-in-up');
        panel.scrollIntoView({ behavior: 'smooth' });

        document.getElementById('risk-val').innerText = result.risk_level;
        document.getElementById('rec-val').innerText = result.recommendation;

        window.currentAnalysisResult = result;

        // Color coding
        const riskColor = result.risk_level === 'High' ? '#ef4444' : (result.risk_level === 'Medium' ? '#f59e0b' : '#10b981');
        document.getElementById('risk-val').style.color = riskColor;
        document.getElementById('result-panel').style.borderColor = riskColor;

        // Animated gauge fill
        animateGauge(result.probability, result.risk_level);

        // Linked Immunity Display
        const immBadge = document.getElementById('immunity-linked-badge');
        if (result.linked_immunity) {
            immBadge.style.display = 'inline-flex';
            document.getElementById('imm-link-val').innerText = `${result.linked_immunity.class} (${result.linked_immunity.score})`;
            immBadge.classList.add('animate-fade-in');
        } else {
            immBadge.style.display = 'none';
        }

        addDownloadBtn('LSD Risk Analysis', data, result);

    } catch (error) {
        if (window.hideLoader) window.hideLoader();
        alert('Error analyzing data.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<ion-icon name="calculator-outline"></ion-icon> Calculate Risk';
    }
});

async function addDownloadBtn(module, inputs, results) {
    const container = document.getElementById('result-panel');
    let btn = document.getElementById('download-btn');
    if (!btn) {
        btn = document.createElement('button');
        btn.id = 'download-btn';
        btn.className = 'btn btn-outline';
        btn.style.marginTop = '1.5rem';
        btn.style.borderColor = '#10b981';
        btn.style.color = '#10b981';
        btn.innerHTML = '<ion-icon name="download-outline"></ion-icon> Download PDF Report';

        const div = document.createElement('div');
        div.style.textAlign = 'center';
        div.appendChild(btn);
        container.appendChild(div);
    }

    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);

    newBtn.addEventListener('click', async () => {
        newBtn.innerHTML = '<span class="loader" style="width:16px;height:16px;border-width:2px;"></span> Generating...';
        try {
            const response = await fetch('/api/report/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ module, inputs, results })
            });
            const data = await response.json();
            window.open(data.download_url, '_blank');
        } catch (e) { console.error(e); }
        newBtn.innerHTML = '<ion-icon name="download-outline"></ion-icon> Download PDF Report';
    });
}
