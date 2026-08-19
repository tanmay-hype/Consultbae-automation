let mediaRecorder;
let audioChunks = [];
let timerInterval;
let seconds = 0;

const recordBtn = document.getElementById('recordBtn');
const stopBtn = document.getElementById('stopBtn');
const timerDisplay = document.getElementById('recordingTimer');
const audioForm = document.getElementById('audioForm');

function updateTimer() {
    seconds++;
    const mins = String(Math.floor(seconds / 60)).padStart(2, '0');
    const secs = String(seconds % 60).padStart(2, '0');
    timerDisplay.textContent = `${mins}:${secs}`;
}

recordBtn.addEventListener('click', async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) audioChunks.push(event.data);
        };
        
        mediaRecorder.start();
        
        recordBtn.disabled = true;
        stopBtn.disabled = false;
        seconds = 0;
        timerDisplay.textContent = "00:00";
        timerInterval = setInterval(updateTimer, 1000);
    } catch (err) {
        alert("Microphone access denied or unavailable.");
    }
});

stopBtn.addEventListener('click', () => {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
    clearInterval(timerInterval);
    
    recordBtn.disabled = false;
    stopBtn.disabled = true;
});

audioForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('applicant_name').value;
    const phone = document.getElementById('applicant_phone').value;
    const uploadInput = document.getElementById('audioUpload');
    
    let audioBlob;
    let fileName = `audio_${Date.now()}.webm`;
    
    if (uploadInput.files.length > 0) {
        audioBlob = uploadInput.files[0];
        fileName = audioBlob.name;
    } else if (audioChunks.length > 0) {
        audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    } else {
        alert("Please record audio or upload a file.");
        return;
    }
    
    const formData = new FormData();
    formData.append('applicant_name', name);
    formData.append('applicant_phone', phone);
    formData.append('audio_file', audioBlob, fileName);
    
    const submitBtn = audioForm.querySelector('button[type="submit"]');
    submitBtn.textContent = "Processing DSP Analytics...";
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/submit-audio', { method: 'POST', body: formData });
        if (response.ok) {
            window.location.reload(); 
        } else {
            const result = await response.json();
            alert(`Error: ${result.detail || 'Upload failed'}`);
        }
    } catch (err) {
        alert("Server error. Check terminal logs.");
    } finally {
        submitBtn.textContent = "Upload & Run DSP Extraction";
        submitBtn.disabled = false;
    }
});