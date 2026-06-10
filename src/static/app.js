const state = {
    refFile: null,
    poseFile: null,
    currentResultUrl: null,
};

async function checkHealth() {
    try {
        const res = await fetch('/health');
        const data = await res.json();
        const dot = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        if (data.runpod && !data.runpod.error) {
            dot.className = 'status-dot online';
            text.textContent = 'Online';
        } else {
            dot.className = 'status-dot online';
            text.textContent = 'Backend OK (GPU sleeping)';
        }
    } catch {
        document.getElementById('status-indicator').className = 'status-dot offline';
        document.getElementById('status-text').textContent = 'Offline';
    }
}

async function loadModels() {
    try {
        const res = await fetch('/api/models');
        const data = await res.json();
        const modelSelect = document.getElementById('model-select');
        const loraSelect = document.getElementById('lora-select');
        modelSelect.innerHTML = '';
        loraSelect.innerHTML = '<option value="">None</option>';
        for (const ckpt of data.checkpoints) {
            const opt = document.createElement('option');
            opt.value = ckpt.name;
            opt.textContent = ckpt.name;
            modelSelect.appendChild(opt);
        }
        for (const lora of data.loras) {
            const opt = document.createElement('option');
            opt.value = lora.name;
            opt.textContent = lora.name + (lora.nsfw ? ' (NSFW)' : '');
            loraSelect.appendChild(opt);
        }
    } catch (err) {
        console.error('Failed to load models:', err);
    }
}

async function loadJobs() {
    try {
        const res = await fetch('/api/jobs?limit=20');
        const data = await res.json();
        const list = document.getElementById('job-list');
        list.innerHTML = '';
        for (const job of data.jobs) {
            const div = document.createElement('div');
            div.className = 'job-item';
            const type = document.createElement('span');
            type.className = 'job-type';
            type.textContent = job.workflow_type;
            const status = document.createElement('span');
            status.className = `job-status ${job.status}`;
            status.textContent = job.status === 'completed' ? 'Done' :
                job.status === 'failed' ? 'Failed' :
                job.status === 'running' ? 'Running' : 'Pending';
            const sim = document.createElement('span');
            sim.className = 'job-similarity';
            sim.textContent = job.similarity_score
                ? `${(job.similarity_score * 100).toFixed(1)}%`
                : '';
            const time = document.createElement('span');
            time.className = 'job-time';
            const created = new Date(job.created_at);
            time.textContent = created.toLocaleTimeString();
            div.appendChild(type);
            div.appendChild(status);
            div.appendChild(sim);
            div.appendChild(time);
            list.appendChild(div);
        }
    } catch (err) {
        console.error('Failed to load jobs:', err);
    }
}

function setupImageUpload(zoneId, inputId, previewId, onFile) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    const placeholder = zone.querySelector('.upload-placeholder');

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.style.borderColor = '#4ade80';
    });

    zone.addEventListener('dragleave', () => {
        zone.style.borderColor = '#333';
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.style.borderColor = '#333';
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            input.files = e.dataTransfer.files;
            handleFile(file, zone, preview, placeholder, onFile);
        }
    });

    input.addEventListener('change', () => {
        if (input.files[0]) {
            handleFile(input.files[0], zone, preview, placeholder, onFile);
        }
    });
}

function handleFile(file, zone, preview, placeholder, onFile) {
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.style.display = 'block';
        placeholder.style.display = 'none';
        zone.classList.add('has-image');
    };
    reader.readAsDataURL(file);
    onFile(file);
}

function setupRangeDisplay(rangeId, valId) {
    const range = document.getElementById(rangeId);
    const val = document.getElementById(valId);
    range.addEventListener('input', () => {
        val.textContent = range.value;
    });
    val.textContent = range.value;
}

document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadModels();
    loadJobs();

    setInterval(checkHealth, 30000);
    setInterval(loadJobs, 15000);

    setupImageUpload('ref-upload', 'ref-input', 'ref-preview', (file) => {
        state.refFile = file;
    });

    setupImageUpload('pose-upload', 'pose-input', 'pose-preview', (file) => {
        state.poseFile = file;
        document.getElementById('remove-pose').style.display = 'inline-block';
    });

    document.getElementById('remove-pose').addEventListener('click', () => {
        state.poseFile = null;
        document.getElementById('pose-input').value = '';
        document.getElementById('pose-preview').style.display = 'none';
        document.getElementById('pose-upload').querySelector('.upload-placeholder').style.display = '';
        document.getElementById('pose-upload').classList.remove('has-image');
        document.getElementById('remove-pose').style.display = 'none';
    });

    setupRangeDisplay('lora-strength', 'lora-strength-val');
    setupRangeDisplay('pulid-weight', 'pulid-weight-val');

    document.getElementById('generate-btn').addEventListener('click', async () => {
        if (!state.refFile) {
            alert('Please upload a reference image.');
            return;
        }
        const prompt = document.getElementById('prompt-input').value.trim();
        if (!prompt) {
            alert('Please describe the result you want.');
            return;
        }

        const btn = document.getElementById('generate-btn');
        const loading = document.getElementById('loading');
        const results = document.getElementById('results-section');
        btn.disabled = true;
        loading.style.display = 'flex';
        results.style.display = 'none';

        const formData = new FormData();
        formData.append('ref_image', state.refFile);
        formData.append('prompt', prompt);
        if (state.poseFile) {
            formData.append('pose_image', state.poseFile);
        }
        const modelName = document.getElementById('model-select').value;
        if (modelName) formData.append('model_name', modelName);
        const loraName = document.getElementById('lora-select').value;
        if (loraName) formData.append('lora_name', loraName);
        const loraStrength = parseFloat(document.getElementById('lora-strength').value);
        if (loraName) formData.append('lora_strength', loraStrength);
        formData.append('seed', parseInt(document.getElementById('seed-input').value));
        formData.append('steps', parseInt(document.getElementById('steps-input').value));
        formData.append('guidance', parseFloat(document.getElementById('guidance-input').value));
        formData.append('pulid_weight', parseFloat(document.getElementById('pulid-weight').value));

        try {
            const res = await fetch('/api/generate', { method: 'POST', body: formData });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Generation failed');
            }
            const data = await res.json();

            const simBadge = document.getElementById('similarity-badge');
            const simScore = data.similarity && data.similarity.score !== null
                ? data.similarity.score
                : null;
            const simLabel = data.similarity ? data.similarity.label : 'unknown';

            if (simScore !== null) {
                simBadge.textContent = `Face Similarity: ${(simScore * 100).toFixed(1)}%`;
            } else {
                simBadge.textContent = 'Face Similarity: N/A';
            }
            simBadge.className = `badge ${simLabel}`;

            const imgContainer = document.getElementById('result-image');
            const images = data.output && data.output.images ? data.output.images : [];
            let imageUrl = null;

            if (images.length > 0) {
                const img = images[0];
                if (img.type === 's3_url' && img.data) {
                    imageUrl = img.data;
                    state.currentResultUrl = img.data;
                } else if (img.type === 'base64' && img.data) {
                    let b64 = img.data;
                    if (b64.startsWith('data:')) {
                        imageUrl = b64;
                    } else {
                        imageUrl = `data:image/png;base64,${b64}`;
                    }
                }
            }

            if (imageUrl) {
                imgContainer.src = imageUrl;
            } else {
                imgContainer.src = '';
                imgContainer.alt = 'No image in response';
            }

            results.style.display = 'block';
            loadJobs();
        } catch (err) {
            alert(`Error: ${err.message}`);
            console.error(err);
        } finally {
            btn.disabled = false;
            loading.style.display = 'none';
        }
    });

    document.getElementById('download-btn').addEventListener('click', () => {
        if (state.currentResultUrl) {
            const a = document.createElement('a');
            a.href = state.currentResultUrl;
            a.download = 'project-o-result.png';
            a.click();
        }
    });

    document.getElementById('regenerate-btn').addEventListener('click', () => {
        document.getElementById('seed-input').value = 0;
        document.getElementById('generate-btn').click();
    });

    document.getElementById('prompt-input').addEventListener('input', () => {
        const prompt = document.getElementById('prompt-input').value.toLowerCase();
        const needsPose = prompt.includes('pose') || prompt.includes('posture')
            || prompt.includes('standing') || prompt.includes('sitting')
            || prompt.includes('walking') || prompt.includes('body position');
        const group = document.getElementById('second-image-group');
        if (needsPose) {
            group.style.display = '';
        } else if (!state.poseFile) {
            group.style.display = 'none';
        }
    });
});
