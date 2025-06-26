const BASE_URL = 'http://localhost:5000';

// Navigation buttons
document.querySelectorAll('nav a').forEach(link => {
    link.addEventListener('click', function (e) {
        e.preventDefault();
        const sectionId = this.getAttribute('href').substring(1);
        document.querySelectorAll('section').forEach(s => s.classList.add('hidden'));
        document.getElementById(sectionId).classList.remove('hidden');
    });
});

document.getElementById('uploadBtn').addEventListener('click', () => {
    document.querySelectorAll('section').forEach(s => s.classList.add('hidden'));
    document.getElementById('upload').classList.remove('hidden');
});

// ✅ Helper: Show cloud save message
function showCloudSaveMessage() {
    const msg = document.createElement('div');
    msg.textContent = '✅ Your insights have been saved to cloud.';
    msg.style.backgroundColor = '#ffe5e5';
    msg.style.color = '#c60000';
    msg.style.border = '1px solid #ffaaaa';
    msg.style.borderRadius = '8px';
    msg.style.padding = '10px';
    msg.style.marginBottom = '10px';
    msg.style.fontWeight = 'bold';
    msg.style.textAlign = 'center';
    msg.style.transition = 'opacity 0.5s ease';
    msg.style.opacity = '0';

    const insightsSection = document.getElementById('insights');
    insightsSection.prepend(msg);

    // Animate: fade in after 1s, stay 2s, then fade out
    setTimeout(() => {
        msg.style.opacity = '1';
        setTimeout(() => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500); // Remove after fade out
        }, 2000); // Show for 2s
    }, 1000); // Delay 1s after insights appear
}

// ✅ Main processing logic
async function processData(formData) {
    try {
        console.log("🚀 Sending request to /process...");
        const response = await fetch(`${BASE_URL}/process`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        console.log("✅ Received data:", data);

        if (!response.ok || data.success === false) {
            alert("❌ Error: " + (data.error || "Unknown"));
            return;
        }

        document.querySelectorAll('section').forEach(s => s.classList.add('hidden'));
        document.getElementById('insights').classList.remove('hidden');

        showCloudSaveMessage();
        renderCharts(data.insights || data);
        renderInsights((data.insights || data).recommendations);

    } catch (error) {
        console.error("🚨 Network or JS error:", error);
        alert('An error occurred while processing.');
    }
}

document.getElementById('useDefaultBtn').addEventListener('click', () => {
    console.log("📩 Use Sample Data button clicked");
    const formData = new FormData();
    processData(formData);
});

document.getElementById('processBtn').addEventListener('click', async () => {
    const transactionFile = document.getElementById('transactionsFile').files[0];
    const productFile = document.getElementById('productsFile').files[0];
    let formData = new FormData();

    if (transactionFile && productFile) {
        formData.append('transactions', transactionFile);
        formData.append('products', productFile);
    } else {
        alert('Please select both transaction and product CSV files.');
        return;
    }

    try {
        const response = await fetch(`${BASE_URL}/process`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok || data.success === false) {
            const rawError = data.error || "An unknown error occurred.";
            alert(
                "⚠️ Something went wrong while processing your data.\n\n" +
                "🔎 Error: " + rawError + "\n\n" +
                "👉 Tips:\n" +
                "- Make sure you uploaded the correct CSV files in the correct fields.\n" +
                "- Transactions CSV should contain: transaction_id, customer_id, product_id, quantity, date, channel.\n" +
                "- Products CSV should contain: product_id, product_name, price, category.\n" +
                "- Check for missing or misspelled columns."
            );
            return;
        }

        document.querySelectorAll('section').forEach(s => s.classList.add('hidden'));
        document.getElementById('insights').classList.remove('hidden');

        showCloudSaveMessage();
        renderCharts(data.insights || data);
        renderInsights((data.insights || data).recommendations);

    } catch (error) {
        console.error(error);
        alert('An error occurred while processing.');
    }
});

document.getElementById('contactForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const name = this.name.value;
    const email = this.email.value;
    const message = this.message.value;

    try {
        const res = await fetch(`${BASE_URL}/contact`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, message })
        });

        const result = await res.json();
        if (result.success) {
            alert('Message sent successfully!');
            this.reset();
        } else {
            alert('Error submitting message.');
        }
    } catch (err) {
        console.error(err);
        alert('Submission failed.');
    }
});

document.getElementById('openChatBtn').addEventListener('click', () => {
    document.getElementById('chatContainer').classList.toggle('hidden');
});

document.getElementById('sendChatBtn').addEventListener('click', async () => {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    const chatBox = document.getElementById('chatMessages');
    chatBox.innerHTML += `<p><strong>You:</strong> ${message}</p>`;
    input.value = 'Thinking...';
    input.disabled = true;

    try {
        const res = await fetch(`${BASE_URL}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await res.json();
        chatBox.innerHTML += `<p><strong>Bot:</strong> ${data.reply || '⚠️ Error processing request.'}</p>`;
    } catch (err) {
        chatBox.innerHTML += `<p><strong>Bot:</strong> ❌ Unable to connect.</p>`;
    }

    input.value = '';
    input.disabled = false;
});
