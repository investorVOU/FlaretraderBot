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
    
    // Check blockchain connection status
    checkBlockchainStatus();
    
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
    
    // Periodically refresh blockchain status
    setInterval(checkBlockchainStatus, 30000); // Check every 30 seconds
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
    messageDiv.className = 'chat-bubble max-w-4xl';
    
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
    });
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="flex items-start space-x-3 justify-end">
                <div class="bg-flare-500 rounded-2xl rounded-tr-none px-4 py-3 max-w-md">
                    <div class="text-white text-sm leading-relaxed">${escapeHtml(message)}</div>
                    <div class="text-flare-100 text-xs mt-1">${timeString}</div>
                </div>
                <div class="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-user text-white text-sm"></i>
                </div>
            </div>
        `;
    } else {
        let tradeInfoHtml = '';
        if (tradeInfo) {
            tradeInfoHtml = `
                <div class="bg-green-500/20 border border-green-500/30 rounded-lg px-3 py-2 mt-2">
                    <div class="flex items-center text-green-400 text-sm">
                        <i class="fas fa-check-circle mr-2"></i>
                        Trade executed: ${escapeHtml(tradeInfo)}
                    </div>
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="w-8 h-8 bg-flare-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-robot text-white text-sm"></i>
                </div>
                <div class="bg-gray-700/50 rounded-2xl rounded-tl-none px-4 py-3 max-w-2xl">
                    <div class="text-white text-sm leading-relaxed">${formatBotMessage(message)}</div>
                    <div class="text-gray-400 text-xs mt-1">${timeString}</div>
                    ${tradeInfoHtml}
                </div>
            </div>
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

// Blockchain status checking function
async function checkBlockchainStatus() {
    try {
        const response = await fetch('/api/refresh_prices');
        const data = await response.json();
        
        const statusElement = document.getElementById('blockchain-status');
        if (!statusElement) return;
        
        if (data.success) {
            statusElement.className = 'px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-sm font-medium';
            statusElement.innerHTML = '🔗 Blockchain Connected';
        } else {
            statusElement.className = 'px-3 py-1 rounded-full bg-yellow-500/20 text-yellow-400 text-sm font-medium';
            statusElement.innerHTML = '⚠️ Using Fallback Data';
        }
    } catch (error) {
        const statusElement = document.getElementById('blockchain-status');
        if (statusElement) {
            statusElement.className = 'px-3 py-1 rounded-full bg-red-500/20 text-red-400 text-sm font-medium';
            statusElement.innerHTML = '❌ Connection Error';
        }
    }
}

// Check blockchain status periodically
setInterval(checkBlockchainStatus, 30000); // Check every 30 seconds
