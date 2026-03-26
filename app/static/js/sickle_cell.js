function switchTab(tab) {
    const dataSec = document.getElementById('data-section');
    const uploadSec = document.getElementById('upload-section');
    const dataBtn = document.getElementById('tab-data');
    const uploadBtn = document.getElementById('tab-upload');

    if (tab === 'data') {
        dataSec.style.display = 'block';
        uploadSec.style.display = 'none';
        dataBtn.style.borderBottom = '2px solid var(--accent)';
        dataBtn.style.color = 'var(--accent)';
        uploadBtn.style.borderBottom = 'none';
        uploadBtn.style.color = 'var(--text-muted)';
    } else {
        uploadSec.style.display = 'block';
        dataSec.style.display = 'none';
        uploadBtn.style.borderBottom = '2px solid var(--accent)';
        uploadBtn.style.color = 'var(--accent)';
        dataBtn.style.borderBottom = 'none';
        dataBtn.style.color = 'var(--text-muted)';
    }
}

async function handleFileUpload(input) {
    if (!input.files || !input.files[0]) return;

    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const statusEl = document.getElementById('upload-status');
    statusEl.innerHTML = '<span class="loader" style="width:16px;height:16px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:0.5rem;"></span> Processing genetic sequence...';
    statusEl.style.color = 'var(--primary)';

    try {
        const response = await fetch('/api/parse_file', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.success && result.data) {
            // Auto-fill gene sequence
            if (result.data.sequence) {
                document.getElementById('sequence').value = result.data.sequence;
            }

            // Auto-fill hemoglobin values
            if (result.data.hba !== undefined) document.getElementById('hba').value = result.data.hba;
            if (result.data.hbs !== undefined) document.getElementById('hbs').value = result.data.hbs;
            if (result.data.hbf !== undefined) document.getElementById('hbf').value = result.data.hbf;

            // Show AI estimation warning
            if (result.data.is_ai_estimated) {
                const mutationType = result.data.mutation_type || 'Unknown';
                statusEl.innerHTML = `
                    <div style="text-align: left; padding: 1rem; background: rgba(79, 70, 229, 0.04); border: 1px solid rgba(79, 70, 229, 0.15); border-radius: 8px; margin-top: 1rem;">
                        <p style="color: var(--success); font-weight: 600; margin-bottom: 0.5rem;">
                            ✅ Genetic Analysis Complete!
                        </p>
                        <p style="color: var(--text-main); margin-bottom: 0.5rem;">
                            <strong>Mutation Status:</strong> ${mutationType}
                        </p>
                        <p style="color: var(--text-main); margin-bottom: 0.5rem;">
                            <strong>Estimated Values:</strong> HbA: ${result.data.hba}% | HbS: ${result.data.hbs}% | HbF: ${result.data.hbf}%
                        </p>
                        <p style="color: var(--warning); font-size: 0.85rem; margin-top: 0.75rem;">
                            ⚠️ ${result.data.ai_note}
                        </p>
                    </div>
                `;
            } else {
                statusEl.textContent = '✅ Data extracted successfully!';
                statusEl.style.color = 'var(--success)';
            }

            setTimeout(() => switchTab('data'), 2000);
        } else {
            statusEl.textContent = 'Could not extract markers from this file.';
            statusEl.style.color = 'var(--danger)';
        }
    } catch (e) {
        console.error(e);
        statusEl.textContent = 'Analysis error. Please fill manually.';
        statusEl.style.color = 'var(--danger)';
    }
}

// Chart Logic
let chartInstance = null;
function renderChart(hba, hbs, hbf) {
    const ctx = document.getElementById('sickleChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['HbA', 'HbS', 'HbF'],
            datasets: [{
                label: 'Hemoglobin Levels (%)',
                data: [hba, hbs, hbf],
                backgroundColor: ['#10b981', '#ef4444', '#6366f1'],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true, max: 100,
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: { color: 'var(--text-muted)' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: 'var(--text-muted)' }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

document.getElementById('sickle-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerHTML = '<span class="loader" style="width:18px;height:18px;border-width:2px;border-top-color:white;"></span> Analyzing Genetics...';

    if (window.showLoader) window.showLoader('Analyzing genetic markers...');

    try {
        const response = await fetch('/api/predict/sickle_cell', {
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

        document.getElementById('pred-val').innerText = result.prediction;
        document.getElementById('note-val').innerText = result.note;
        document.getElementById('rec-val').innerText = result.recommendation || "Maintain routine health checks.";

        window.currentAnalysisResult = result;

        const hba = parseFloat(data.hba || 0);
        const hbs = parseFloat(data.hbs || 0);
        const hbf = parseFloat(data.hbf || 0);
        renderChart(hba, hbs, hbf);

        if (result.mutation_detected) {
            const badge = document.getElementById('mutation-badge');
            badge.style.display = 'inline-flex';
            badge.classList.add('animate-pulse');
        } else {
            document.getElementById('mutation-badge').style.display = 'none';
        }

        // Linked Immunity Display
        const immBadge = document.getElementById('immunity-linked-badge');
        if (result.linked_immunity) {
            immBadge.style.display = 'inline-flex';
            document.getElementById('imm-link-val').innerText = `${result.linked_immunity.class} (${result.linked_immunity.score})`;
            immBadge.classList.add('animate-fade-in');
        } else {
            immBadge.style.display = 'none';
        }

        addDownloadBtn('Sickle Cell Prediction', data, result);

    } catch (error) {
        if (window.hideLoader) window.hideLoader();
        alert('Error analyzing data.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<ion-icon name="analytics-outline"></ion-icon> Predict Risk';
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
        btn.style.borderColor = 'var(--accent)';
        btn.style.color = 'var(--accent)';
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
