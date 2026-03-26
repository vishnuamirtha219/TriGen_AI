// Tab Switching
function switchTab(tab) {
    const manualBtn = document.getElementById('tab-manual');
    const uploadBtn = document.getElementById('tab-upload');
    const manualSec = document.getElementById('manual-section');
    const uploadSec = document.getElementById('upload-section');

    if (tab === 'manual') {
        manualBtn.style.borderBottom = '2px solid var(--primary)';
        manualBtn.style.color = 'var(--primary)';
        uploadBtn.style.borderBottom = 'none';
        uploadBtn.style.color = 'var(--text-muted)';

        manualSec.style.display = 'block';
        uploadSec.style.display = 'none';
    } else {
        uploadBtn.style.borderBottom = '2px solid var(--primary)';
        uploadBtn.style.color = 'var(--primary)';
        manualBtn.style.borderBottom = 'none';
        manualBtn.style.color = 'var(--text-muted)';

        uploadSec.style.display = 'block';
        manualSec.style.display = 'none';
    }
}

// File Selection Handler
let selectedFile = null;

document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name-display');
    const selectedFileName = document.getElementById('selected-file-name');
    const analyzeFileBtn = document.getElementById('analyze-file-btn');
    const uploadStatus = document.getElementById('upload-status');

    if (fileInput) {
        fileInput.addEventListener('change', function (e) {
            if (e.target.files && e.target.files[0]) {
                selectedFile = e.target.files[0];
                selectedFileName.textContent = selectedFile.name;
                fileNameDisplay.style.display = 'block';
                analyzeFileBtn.style.display = 'block';
                uploadStatus.textContent = 'File selected. Click "Analyze File" to process.';
                uploadStatus.style.color = 'var(--primary)';
            }
        });
    }

    if (analyzeFileBtn) {
        analyzeFileBtn.addEventListener('click', async function () {
            if (!selectedFile) {
                uploadStatus.textContent = 'Please select a file first.';
                uploadStatus.style.color = 'var(--danger)';
                return;
            }

            await handleFileAnalysis(selectedFile);
        });
    }
});

async function handleFileAnalysis(file) {
    const formData = new FormData();
    formData.append('file', file);
    const uploadStatus = document.getElementById('upload-status');
    const analyzeFileBtn = document.getElementById('analyze-file-btn');

    uploadStatus.textContent = 'Parsing file with AI...';
    uploadStatus.style.color = 'var(--text-muted)';
    analyzeFileBtn.disabled = true;
    analyzeFileBtn.innerHTML = '<span class="loader" style="width:18px;height:18px;border-width:2px;"></span> Processing...';

    try {
        const response = await fetch('/api/parse_file', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();

        if (result.success && result.data) {
            const map = {
                'wbc': 'wbc', 'neutrophils': 'neutrophils', 'lymphocytes': 'lymphocytes',
                'monocytes': 'monocytes', 'platelets': 'platelets', 'hemoglobin': 'hemoglobin',
                'hba': 'hemoglobin', 'igg': 'igg', 'age': 'age', 'eosinophils': 'eosinophils'
            };

            for (const [key, val] of Object.entries(result.data)) {
                const inputName = map[key];
                if (inputName) {
                    const inputField = document.getElementById(inputName) || document.querySelector(`input[name="${inputName}"]`);
                    if (inputField) inputField.value = val;
                }
            }

            uploadStatus.textContent = '✅ File parsed successfully! Switching to form...';
            uploadStatus.style.color = 'var(--success)';

            setTimeout(() => {
                switchTab('manual');
                document.getElementById('immunity-form').dispatchEvent(new Event('submit'));
            }, 1500);
        } else {
            uploadStatus.textContent = 'Could not extract data from file. Please try manual entry.';
            uploadStatus.style.color = 'var(--danger)';
        }
    } catch (e) {
        console.error(e);
        uploadStatus.textContent = 'Error processing file. Please try again.';
        uploadStatus.style.color = 'var(--danger)';
    } finally {
        analyzeFileBtn.disabled = false;
        analyzeFileBtn.innerHTML = 'Analyze File <ion-icon name="pulse-outline"></ion-icon>';
    }
}

// Chart
let chartInstance = null;

function renderChart(score) {
    const ctx = document.getElementById('immunityChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();

    const remaining = 100 - score;
    const color = score > 80 ? '#10b981' : (score > 50 ? '#f59e0b' : '#ef4444');

    chartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Score', 'Remaining'],
            datasets: [{
                data: [score, remaining],
                backgroundColor: [color, 'rgba(0, 0, 0, 0.06)'],
                borderWidth: 0,
                cutout: '80%'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
}

// Animated score counter
function animateScore(element, target) {
    const duration = 1200;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        element.textContent = Math.round(target * eased);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// Submit Form
document.getElementById('immunity-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="loader" style="width:18px;height:18px;border-width:2px;border-top-color:white;"></span> Analyzing...';
    btn.disabled = true;

    // Show global loader
    if (window.showLoader) window.showLoader('Analyzing immune markers...');

    try {
        const response = await fetch('/api/predict/immunity', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (window.hideLoader) window.hideLoader();

        // Show Result Section with animation
        const panel = document.getElementById('result-panel');
        panel.style.display = 'block';
        panel.classList.add('animate-fade-in-up');
        panel.scrollIntoView({ behavior: 'smooth' });

        // Animate score counter
        animateScore(document.getElementById('score-val'), result.score);
        document.getElementById('class-val').innerText = result.class;
        document.getElementById('rec-val').innerText = result.recommendation;
        document.getElementById('explanation-val').innerText = result.explanation || 'Analysis complete.';

        // Key Findings
        const findingsList = document.getElementById('findings-list');
        if (result.key_findings && result.key_findings.length > 0) {
            findingsList.innerHTML = result.key_findings.map(f =>
                `<li style="margin-bottom: 0.5rem; padding-left: 1rem; border-left: 3px solid var(--secondary);">${f}</li>`
            ).join('');
        } else {
            findingsList.innerHTML = '<li style="color: var(--text-muted);">No specific findings</li>';
        }

        // Risk Indicators
        const risksList = document.getElementById('risks-list');
        if (result.risk_indicators && result.risk_indicators.length > 0) {
            risksList.innerHTML = result.risk_indicators.map(r =>
                `<li style="margin-bottom: 0.5rem; padding-left: 1rem; border-left: 3px solid var(--danger);">⚠ ${r}</li>`
            ).join('');
        } else {
            risksList.innerHTML = '<li style="color: var(--text-muted);">✓ None detected</li>';
        }

        // Derived Features
        if (result.derived_features) {
            document.getElementById('alc-val').innerText = result.derived_features.alc || '--';
            document.getElementById('nlr-val').innerText = result.derived_features.nlr || '--';
            document.getElementById('plr-val').innerText = result.derived_features.plr || '--';
            document.getElementById('balance-val').innerText = result.derived_features.immune_balance || '--';
        }

        // Store result for Chatbot Context
        window.currentAnalysisResult = result;

        // Render Chart
        renderChart(result.score);
        addDownloadBtn('Immunity Analysis', data, result);

    } catch (error) {
        if (window.hideLoader) window.hideLoader();
        console.error('Error:', error);
        alert('An error occurred during analysis.');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
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
        btn.style.borderColor = 'var(--primary)';
        btn.style.color = 'var(--primary)';
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
