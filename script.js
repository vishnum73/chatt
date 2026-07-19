const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("message");
const sendButton = document.getElementById("send-button");

function formatTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function appendMessage(role, text) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role}`;
    messageElement.innerHTML = `
        <div class="content">${text}</div>
        <span class="time">${formatTime()}</span>
    `;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    appendMessage('user', message);
    messageInput.value = '';
    messageInput.focus();

    try {
        const response = await fetch('http://127.0.0.1:8000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt: message }),
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        appendMessage('bot', data.response || 'Sorry, I could not get a response.');
    } catch (error) {
        appendMessage('bot', 'Unable to connect to the chatbot service. Please make sure the backend is running.');
        console.error(error);
    }
}

function handleEnterKey(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
}

messageInput.addEventListener('keydown', handleEnterKey);
sendButton.addEventListener('click', sendMessage);

window.addEventListener('DOMContentLoaded', () => {
    appendMessage('bot', 'Hello! How can I help you today?');
});