document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('fileInput');
    const modeInput = document.getElementById('mode');
    const statusDiv = document.getElementById('status');
    const formData = new FormData();
    
    if(fileInput.files.length === 0) {
        alert("Please select a file first!");
        return;
    }

    formData.append('file', fileInput.files[0]);
    formData.append('mode', modeInput.value);

    statusDiv.innerHTML = "<b>Step 1:</b> Uploading... <br><b>Step 2:</b> AI is structuring the MAK Paper... (Please wait)";
    statusDiv.style.color = "blue";

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if(result.status === 'success') {
            statusDiv.innerHTML = "<h3>✅ Analysis Success!</h3>";
            statusDiv.style.color = "green";
            
            // Create Download Button
            const downloadBtn = document.createElement('a');
            downloadBtn.href = "/download/" + result.download_url;
            downloadBtn.innerText = "📄 Download MAK Question Paper (.docx)";
            downloadBtn.className = "download-btn";
            downloadBtn.style.display = "block";
            downloadBtn.style.marginTop = "20px";
            downloadBtn.style.padding = "15px";
            downloadBtn.style.backgroundColor = "#d9534f"; // Red color for attention
            downloadBtn.style.color = "white";
            downloadBtn.style.textDecoration = "none";
            downloadBtn.style.borderRadius = "5px";
            downloadBtn.style.fontWeight = "bold";
            
            statusDiv.appendChild(downloadBtn);

            // Optional: Show JSON for debugging
            const details = document.createElement('details');
            details.innerHTML = "<summary>View Extracted Data (Debug)</summary>";
            const pre = document.createElement('pre');
            pre.innerText = JSON.stringify(result.data, null, 2);
            details.appendChild(pre);
            statusDiv.appendChild(details);

        } else {
            statusDiv.innerHTML = "❌ Error: " + (result.message || "Unknown error");
            statusDiv.style.color = "red";
        }
    } catch (error) {
        console.error(error);
        statusDiv.innerHTML = "❌ Error connecting to server.";
        statusDiv.style.color = "red";
    }
});