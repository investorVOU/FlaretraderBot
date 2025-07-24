// Trading interface JavaScript

let priceChart;
let tokenPrices = {};

document.addEventListener('DOMContentLoaded', function() {
    initializeTradingInterface();
    initializePriceChart();
    loadTokenPrices();
});

function initializeTradingInterface() {
    // Form submissions
    document.getElementById('buyForm').addEventListener('submit', handleBuySubmit);
    document.getElementById('sellForm').addEventListener('submit', handleSellSubmit);
    document.getElementById('swapForm').addEventListener('submit', handleSwapSubmit);
    document.getElementById('wrapForm').addEventListener('submit', handleWrapSubmit);
    document.getElementById('dexForm').addEventListener('submit', handleDexSubmit);
    document.getElementById('bridgeForm').addEventListener('submit', handleBridgeSubmit);
    
    // Token selection changes
    document.getElementById('buyToken').addEventListener('change', updateBuyPriceInfo);
    document.getElementById('sellToken').addEventListener('change', updateSellPriceInfo);
    document.getElementById('swapFromToken').addEventListener('change', updateSwapPriceInfo);
    document.getElementById('swapToToken').addEventListener('change', updateSwapPriceInfo);
    document.getElementById('wrapFromToken').addEventListener('change', updateWrapPriceInfo);
    document.getElementById('wrapToToken').addEventListener('change', updateWrapPriceInfo);
    
    // Amount input changes
    document.getElementById('buyAmount').addEventListener('input', updateBuyPriceInfo);
    document.getElementById('sellAmount').addEventListener('input', updateSellPriceInfo);
    document.getElementById('swapAmount').addEventListener('input', updateSwapPriceInfo);
    document.getElementById('wrapAmount').addEventListener('input', updateWrapPriceInfo);
    
    // Chart token selection
    document.getElementById('chartTokenSelect').addEventListener('change', updatePriceChart);
    
    // DEX form changes
    document.getElementById('dexFromToken').addEventListener('change', updateDexPriceInfo);
    document.getElementById('dexToToken').addEventListener('change', updateDexPriceInfo);
    document.getElementById('dexAmount').addEventListener('input', updateDexPriceInfo);
    document.getElementById('useOneInch').addEventListener('change', updateDexPriceInfo);
    
    // Bridge form changes  
    document.getElementById('bridgeToken').addEventListener('change', updateBridgePriceInfo);
    document.getElementById('bridgeAmount').addEventListener('input', updateBridgePriceInfo);
    document.getElementById('destinationChain').addEventListener('change', updateBridgePriceInfo);
    
    // Handle wrap token selection logic
    document.getElementById('wrapFromToken').addEventListener('change', function() {
        const fromToken = this.value;
        const toTokenSelect = document.getElementById('wrapToToken');
        
        if (fromToken === 'FLR') {
            toTokenSelect.value = 'WFLR';
        } else if (fromToken === 'WFLR') {
            toTokenSelect.value = 'FLR';
        }
        updateWrapPriceInfo();
    });
}

async function handleBuySubmit(e) {
    e.preventDefault();
    const token = document.getElementById('buyToken').value;
    const amount = parseFloat(document.getElementById('buyAmount').value);
    
    await executeTrade('buy', token, amount);
}

async function handleSellSubmit(e) {
    e.preventDefault();
    const token = document.getElementById('sellToken').value;
    const amount = parseFloat(document.getElementById('sellAmount').value);
    
    await executeTrade('sell', token, amount);
}

async function handleSwapSubmit(e) {
    e.preventDefault();
    const fromToken = document.getElementById('swapFromToken').value;
    const toToken = document.getElementById('swapToToken').value;
    const amount = parseFloat(document.getElementById('swapAmount').value);
    
    await executeTrade('swap', toToken, amount, fromToken);
}

async function handleWrapSubmit(e) {
    e.preventDefault();
    const fromToken = document.getElementById('wrapFromToken').value;
    const toToken = document.getElementById('wrapToToken').value;
    const amount = parseFloat(document.getElementById('wrapAmount').value);
    
    await executeTrade('swap', toToken, amount, fromToken);
}

async function handleDexSubmit(e) {
    e.preventDefault();
    const fromToken = document.getElementById('dexFromToken').value;
    const toToken = document.getElementById('dexToToken').value;
    const amount = parseFloat(document.getElementById('dexAmount').value);
    const useOneInch = document.getElementById('useOneInch').checked;
    
    await executeDexSwap(fromToken, toToken, amount, useOneInch);
}

async function handleBridgeSubmit(e) {
    e.preventDefault();
    const token = document.getElementById('bridgeToken').value;
    const amount = parseFloat(document.getElementById('bridgeAmount').value);
    const destinationChain = document.getElementById('destinationChain').value;
    const toToken = document.getElementById('bridgeToToken').value || token;
    const recipient = document.getElementById('bridgeRecipient').value;
    
    await executeBridge(token, amount, destinationChain, toToken, recipient);
}

async function executeTrade(type, token, amount, fromToken = null) {
    const button = event.target.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
    button.disabled = true;
    
    try {
        const response = await fetch('/api/execute_trade', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: type,
                token: token,
                amount: amount,
                from_token: fromToken
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(result.message, 'success');
            // Reset form
            event.target.reset();
            // Clear price info
            document.querySelectorAll('.price-info').forEach(el => el.innerHTML = '');
        } else {
            showAlert(result.message, 'danger');
        }
    } catch (error) {
        showAlert('Network error occurred', 'danger');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

function updateBuyPriceInfo() {
    const token = document.getElementById('buyToken').value;
    const amount = parseFloat(document.getElementById('buyAmount').value) || 0;
    updatePriceInfo('buyPriceInfo', token, amount);
}

function updateSellPriceInfo() {
    const token = document.getElementById('sellToken').value;
    const amount = parseFloat(document.getElementById('sellAmount').value) || 0;
    updatePriceInfo('sellPriceInfo', token, amount);
}

function updateSwapPriceInfo() {
    const fromToken = document.getElementById('swapFromToken').value;
    const toToken = document.getElementById('swapToToken').value;
    const amount = parseFloat(document.getElementById('swapAmount').value) || 0;
    
    if (fromToken && toToken && amount > 0 && tokenPrices[fromToken] && tokenPrices[toToken]) {
        const fromPrice = tokenPrices[fromToken];
        const toPrice = tokenPrices[toToken];
        const totalValue = amount * fromPrice;
        const receiveAmount = totalValue / toPrice;
        
        document.getElementById('swapPriceInfo').innerHTML = `
            <div class="d-flex justify-content-between">
                <span>You pay:</span>
                <span class="price-display">${amount} ${fromToken}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>You receive:</span>
                <span class="price-display">${receiveAmount.toFixed(6)} ${toToken}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>Exchange rate:</span>
                <span class="total-cost">1 ${fromToken} = ${(fromPrice / toPrice).toFixed(6)} ${toToken}</span>
            </div>
        `;
    } else {
        document.getElementById('swapPriceInfo').innerHTML = '';
    }
}

function updatePriceInfo(elementId, token, amount) {
    if (token && amount > 0 && tokenPrices[token]) {
        const price = tokenPrices[token];
        const total = amount * price;
        
        document.getElementById(elementId).innerHTML = `
            <div class="d-flex justify-content-between">
                <span>Price:</span>
                <span class="price-display">$${price.toFixed(6)}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>Total:</span>
                <span class="total-cost">$${total.toFixed(2)}</span>
            </div>
        `;
    } else {
        document.getElementById(elementId).innerHTML = '';
    }
}

function updateWrapPriceInfo() {
    const fromToken = document.getElementById('wrapFromToken').value;
    const toToken = document.getElementById('wrapToToken').value;
    const amount = parseFloat(document.getElementById('wrapAmount').value) || 0;
    
    if (fromToken && toToken && amount > 0 && tokenPrices[fromToken] && tokenPrices[toToken]) {
        const fromPrice = tokenPrices[fromToken];
        const toPrice = tokenPrices[toToken];
        const totalValue = amount * fromPrice;
        const receiveAmount = totalValue / toPrice;
        
        // For wrapping, it's usually 1:1 but we'll use the price calculation
        const wrapAction = fromToken === 'FLR' ? 'Wrap' : 'Unwrap';
        
        document.getElementById('wrapPriceInfo').innerHTML = `
            <div class="d-flex justify-content-between">
                <span>You ${wrapAction.toLowerCase()}:</span>
                <span class="price-display">${amount} ${fromToken}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>You receive:</span>
                <span class="price-display">${receiveAmount.toFixed(6)} ${toToken}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>${wrapAction} rate:</span>
                <span class="total-cost">1:${(receiveAmount / amount).toFixed(6)}</span>
            </div>
        `;
    } else {
        document.getElementById('wrapPriceInfo').innerHTML = '';
    }
}

async function loadTokenPrices() {
    // Extract prices from the page
    document.querySelectorAll('[data-token]').forEach(element => {
        if (element.classList.contains('price')) {
            const token = element.getAttribute('data-token');
            const priceText = element.textContent.replace('$', '');
            tokenPrices[token] = parseFloat(priceText);
        }
    });
}

async function initializePriceChart() {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;
    
    const selectedToken = document.getElementById('chartTokenSelect').value;
    await updatePriceChart();
}

async function updatePriceChart() {
    const selectedToken = document.getElementById('chartTokenSelect').value;
    
    try {
        const response = await fetch(`/api/price_data/${selectedToken}`);
        const data = await response.json();
        
        if (data.error) {
            console.error('Error loading price data:', data.error);
            return;
        }
        
        const ctx = document.getElementById('priceChart');
        
        // Destroy existing chart
        if (priceChart) {
            priceChart.destroy();
        }
        
        priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: `${selectedToken} Price`,
                    data: data.data,
                    borderColor: '#1f6feb',
                    backgroundColor: 'rgba(31, 111, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: '#30363d'
                        },
                        ticks: {
                            color: '#8b949e',
                            callback: function(value) {
                                return '$' + value.toFixed(6);
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: '#30363d'
                        },
                        ticks: {
                            color: '#8b949e'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    } catch (error) {
        console.error('Error updating price chart:', error);
    }
}

function quickBuy(token) {
    document.getElementById('buyToken').value = token;
    document.getElementById('buyAmount').focus();
    
    // Switch to buy tab
    const buyTab = new bootstrap.Tab(document.getElementById('buy-tab'));
    buyTab.show();
}

function quickSell(token) {
    document.getElementById('sellToken').value = token;
    document.getElementById('sellAmount').focus();
    
    // Switch to sell tab
    const sellTab = new bootstrap.Tab(document.getElementById('sell-tab'));
    sellTab.show();
}

async function executeDexSwap(fromToken, toToken, amount, useOneInch) {
    const button = event.target.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing DEX Swap...';
    button.disabled = true;
    
    try {
        const response = await fetch('/api/execute_dex_swap', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                from_token: fromToken,
                to_token: toToken,
                amount: amount,
                use_oneinch: useOneInch
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const aggregator = useOneInch ? ' via 1inch' : ' via internal DEX';
            showAlert(result.message + aggregator, 'success');
            // Reset form
            event.target.reset();
            document.getElementById('dexPriceInfo').innerHTML = '';
        } else {
            showAlert(result.message, 'danger');
        }
    } catch (error) {
        showAlert('DEX swap network error occurred', 'danger');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

async function executeBridge(token, amount, destinationChain, toToken, recipient) {
    const button = event.target.querySelector('button[type="submit"]');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing Bridge...';
    button.disabled = true;
    
    try {
        const response = await fetch('/api/execute_cross_chain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                from_token: token,
                amount: amount,
                destination_chain: destinationChain,
                to_token: toToken,
                recipient: recipient
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(`Bridge to ${destinationChain}: ${result.message}`, 'success');
            // Reset form
            event.target.reset();
            document.getElementById('bridgePriceInfo').innerHTML = '';
        } else {
            showAlert(result.message, 'danger');
        }
    } catch (error) {
        showAlert('Bridge network error occurred', 'danger');
    } finally {
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

function updateDexPriceInfo() {
    const fromToken = document.getElementById('dexFromToken').value;
    const toToken = document.getElementById('dexToToken').value;
    const amount = parseFloat(document.getElementById('dexAmount').value) || 0;
    const useOneInch = document.getElementById('useOneInch').checked;
    
    if (fromToken && toToken && amount > 0 && tokenPrices[fromToken] && tokenPrices[toToken]) {
        const fromPrice = tokenPrices[fromToken];
        const toPrice = tokenPrices[toToken];
        const totalValue = amount * fromPrice;
        const receiveAmount = totalValue / toPrice;
        const fee = useOneInch ? 0.1 : 0.3; // 1inch: 0.1%, Internal: 0.3%
        const feeAmount = receiveAmount * (fee / 100);
        const finalAmount = receiveAmount - feeAmount;
        
        document.getElementById('dexPriceInfo').innerHTML = `
            <div class="d-flex justify-content-between">
                <span>You pay:</span>
                <span class="price-display">${amount} ${fromToken}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>You receive:</span>
                <span class="price-display">${finalAmount.toFixed(6)} ${toToken}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>Exchange rate:</span>
                <span class="total-cost">1 ${fromToken} = ${(fromPrice / toPrice).toFixed(6)} ${toToken}</span>
            </div>
            <div class="d-flex justify-content-between text-muted">
                <span>Fee (${fee}%):</span>
                <span>${feeAmount.toFixed(6)} ${toToken}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span><strong>Route:</strong></span>
                <span class="text-${useOneInch ? 'warning' : 'info'}">${useOneInch ? '1inch Aggregator' : 'Internal DEX'}</span>
            </div>
        `;
    } else {
        document.getElementById('dexPriceInfo').innerHTML = '';
    }
}

function updateBridgePriceInfo() {
    const token = document.getElementById('bridgeToken').value;
    const amount = parseFloat(document.getElementById('bridgeAmount').value) || 0;
    const destinationChain = document.getElementById('destinationChain').value;
    
    if (token && amount > 0 && destinationChain && tokenPrices[token]) {
        const price = tokenPrices[token];
        const totalValue = amount * price;
        const bridgeFee = totalValue * 0.005; // 0.5% bridge fee
        const estimatedGas = 50; // USD
        const totalCost = bridgeFee + estimatedGas;
        
        document.getElementById('bridgePriceInfo').innerHTML = `
            <div class="d-flex justify-content-between">
                <span>Amount to bridge:</span>
                <span class="price-display">${amount} ${token}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span>Total value:</span>
                <span class="total-cost">$${totalValue.toFixed(2)}</span>
            </div>
            <div class="d-flex justify-content-between text-muted">
                <span>Bridge fee (0.5%):</span>
                <span>$${bridgeFee.toFixed(2)}</span>
            </div>
            <div class="d-flex justify-content-between text-muted">
                <span>Est. gas fee:</span>
                <span>~$${estimatedGas}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span><strong>Total cost:</strong></span>
                <span class="text-warning">$${totalCost.toFixed(2)}</span>
            </div>
            <div class="d-flex justify-content-between">
                <span><strong>Destination:</strong></span>
                <span class="text-info">${destinationChain.charAt(0).toUpperCase() + destinationChain.slice(1)}</span>
            </div>
        `;
    } else {
        document.getElementById('bridgePriceInfo').innerHTML = '';
    }
}

// Refresh prices and update chart
setInterval(async function() {
    await loadTokenPrices();
    if (priceChart) {
        await updatePriceChart();
    }
}, 30000); // Every 30 seconds
