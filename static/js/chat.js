// Chat interface JavaScript

let isProcessing = false;

document.addEventListener('DOMContentLoaded', function() {
    initializeChatInterface();
    scrollToBottom();
});

function initializeChatInterface() {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    
    // Handle form submission
    chatForm.addEventListener('submit', handleChatSubmit);
    
    // Handle quick command buttons
    document.querySelectorAll('.quick-command').forEach(button => {
        button.addEventListener('click', function() {
            const command = this.getAttribute('data-command');
            chatInput.value = command;
            chatInput.focus();
        });
    });
    
    // Handle Enter key
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!isProcessing) {
                handleChatSubmit(e);
            }
        }
    });
    
    // Auto-focus on chat input
    chatInput.focus();
}

async function handleChatSubmit(e) {
    e.preventDefault();
    
    if (isProcessing) return;
    
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // Update UI
    isProcessing = true;
    sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    sendButton.disabled = true;
    chatInput.disabled = true;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Clear input
    chatInput.value = '';
    
    try {
        // Send message to backend
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        });
        
        const result = await response.json();
        
        // Add bot response to chat
        addMessageToChat(result.response, 'bot', result.trade_info);
        
    } catch (error) {
        addMessageToChat('Sorry, I encountered an error processing your request. Please try again.', 'bot');
        console.error('Chat error:', error);
    } finally {
        // Reset UI
        isProcessing = false;
        sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        sendButton.disabled = false;
        chatInput.disabled = false;
        chatInput.focus();
    }
}

function addMessageToChat(message, type, tradeInfo = null) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}-message fade-in`;
    
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
    });
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-user me-2"></i>${escapeHtml(message)}
            </div>
            <div class="message-time">${timeString}</div>
        `;
    } else {
        let tradeInfoHtml = '';
        if (tradeInfo) {
            tradeInfoHtml = `
                <div class="trade-info">
                    <i class="fas fa-check-circle text-success me-2"></i>Trade executed: ${escapeHtml(tradeInfo)}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-robot me-2"></i>${formatBotMessage(message)}
            </div>
            ${tradeInfoHtml}
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function formatBotMessage(message) {
    // Convert markdown-style formatting to HTML
    let formatted = escapeHtml(message);
    
    // Bold text
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Bullet points
    formatted = formatted.replace(/^• (.+)$/gm, '&nbsp;&nbsp;• $1');
    
    // Line breaks
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Auto-scroll to bottom when new messages are added
const chatMessages = document.getElementById('chatMessages');
if (chatMessages) {
    const observer = new MutationObserver(scrollToBottom);
    observer.observe(chatMessages, { childList: true });
}
