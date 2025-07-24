
let isConnected = false;
let walletAddress = '';

// Initialize chat functionality
document.addEventListener('DOMContentLoaded', function() {
    setupChatHandlers();
    setupWalletHandlers();
    checkWalletStatus();
});

function setupChatHandlers() {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');

    if (chatForm) {
        chatForm.addEventListener('submit', handleChatSubmit);
    }

    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleChatSubmit(e);
            }
        });
    }

    // Quick command buttons
    document.querySelectorAll('.quick-command').forEach(button => {
        button.addEventListener('click', function() {
            const command = this.dataset.command;
            if (command) {
                chatInput.value = command;
                handleChatSubmit();
            }
        });
    });
}

function setupWalletHandlers() {
    const connectBtn = document.getElementById('connectWallet');
    const disconnectBtn = document.getElementById('disconnectWallet');

    if (connectBtn) {
        connectBtn.addEventListener('click', connectWallet);
    }

    if (disconnectBtn) {
        disconnectBtn.addEventListener('click', disconnectWallet);
    }
}

async function handleChatSubmit(e) {
    if (e) e.preventDefault();
    
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const message = chatInput.value.trim();

    if (!message) return;

    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Clear input and show loading
    chatInput.value = '';
    sendButton.disabled = true;
    sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Sending</span>';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        
        if (data.response) {
            addMessageToChat(data.response, 'bot');
            
            // Show trade notification if applicable
            if (data.trade_executed && data.trade_info) {
                showTradeNotification(data.trade_info);
            }
        } else {
            addMessageToChat('Sorry, I encountered an error processing your request.', 'bot');
        }
    } catch (error) {
        console.error('Chat error:', error);
        addMessageToChat('Sorry, I\'m having trouble connecting. Please try again.', 'bot');
    } finally {
        sendButton.disabled = false;
        sendButton.innerHTML = '<i class="fas fa-paper-plane"></i><span>Send</span>';
        chatInput.focus();
    }
}

function addMessageToChat(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-bubble max-w-4xl';

    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="flex items-start space-x-3 justify-end">
                <div class="bg-flare-500 rounded-2xl rounded-tr-none px-4 py-3 max-w-md">
                    <div class="text-white text-sm leading-relaxed">${escapeHtml(message)}</div>
                </div>
                <div class="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-user text-white text-sm"></i>
                </div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="flex items-start space-x-3">
                <div class="w-8 h-8 bg-flare-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-robot text-white text-sm"></i>
                </div>
                <div class="bg-gray-700/50 rounded-2xl rounded-tl-none px-4 py-3 max-w-md">
                    <div class="text-white text-sm leading-relaxed">${formatBotMessage(message)}</div>
                </div>
            </div>
        `;
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatBotMessage(message) {
    // Convert markdown-style formatting to HTML
    return message
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code class="bg-gray-600 px-1 py-0.5 rounded text-xs">$1</code>')
        .replace(/\n/g, '<br>')
        .replace(/• /g, '• ');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showTradeNotification(tradeInfo) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
    notification.innerHTML = `
        <div class="flex items-center space-x-2">
            <i class="fas fa-check-circle"></i>
            <span>Trade executed: ${tradeInfo}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Wallet connection functions
async function connectWallet() {
    try {
        if (typeof window.ethereum !== 'undefined') {
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            const chainId = await window.ethereum.request({ method: 'eth_chainId' });
            
            if (accounts.length > 0) {
                const address = accounts[0];
                
                // Send wallet connection to backend
                const response = await fetch('/api/wallet/connect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        address: address,
                        chainId: parseInt(chainId, 16)
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    updateWalletUI(address, true);
                    showNotification('Wallet connected successfully!', 'success');
                } else {
                    showNotification('Failed to connect wallet: ' + result.message, 'error');
                }
            }
        } else {
            showNotification('Please install MetaMask or another Web3 wallet', 'error');
        }
    } catch (error) {
        console.error('Wallet connection error:', error);
        showNotification('Failed to connect wallet', 'error');
    }
}

async function disconnectWallet() {
    try {
        const response = await fetch('/api/wallet/disconnect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateWalletUI('', false);
            showNotification('Wallet disconnected', 'info');
        }
    } catch (error) {
        console.error('Wallet disconnection error:', error);
        showNotification('Failed to disconnect wallet', 'error');
    }
}

async function checkWalletStatus() {
    try {
        const response = await fetch('/api/wallet/status');
        const status = await response.json();
        
        if (status.connected && status.address) {
            updateWalletUI(status.address, true);
        }
    } catch (error) {
        console.error('Error checking wallet status:', error);
    }
}

function updateWalletUI(address, connected) {
    const connectBtn = document.getElementById('connectWallet');
    const connectedDiv = document.getElementById('walletConnected');
    const addressSpan = document.getElementById('walletAddress');
    
    isConnected = connected;
    walletAddress = address;
    
    if (connected && address) {
        connectBtn.classList.add('hidden');
        connectedDiv.classList.remove('hidden');
        addressSpan.textContent = address.substring(0, 6) + '...' + address.substring(address.length - 4);
    } else {
        connectBtn.classList.remove('hidden');
        connectedDiv.classList.add('hidden');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    const bgColor = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'info': 'bg-blue-500'
    }[type] || 'bg-gray-500';
    
    notification.className = `fixed top-4 right-4 ${bgColor} text-white px-4 py-2 rounded-lg shadow-lg z-50`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 4000);
}

// Handle wallet account changes
if (typeof window.ethereum !== 'undefined') {
    window.ethereum.on('accountsChanged', function (accounts) {
        if (accounts.length === 0) {
            updateWalletUI('', false);
        } else if (accounts[0] !== walletAddress) {
            connectWallet();
        }
    });

    window.ethereum.on('chainChanged', function (chainId) {
        // Reload the page on chain change
        window.location.reload();
    });
}
