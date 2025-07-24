
class CrossChainTrader {
    constructor() {
        this.supportedChains = {};
        this.currentQuote = null;
        this.init();
    }

    async init() {
        await this.loadSupportedChains();
        this.setupEventListeners();
        this.updateChainSelectors();
    }

    async loadSupportedChains() {
        try {
            const response = await fetch('/api/supported_chains');
            const result = await response.json();
            
            if (result.success) {
                this.supportedChains = result.chains;
                console.log('Loaded supported chains:', this.supportedChains);
            }
        } catch (error) {
            console.error('Error loading supported chains:', error);
        }
    }

    setupEventListeners() {
        // Cross-chain form submissions
        const crossChainForm = document.getElementById('crossChainForm');
        if (crossChainForm) {
            crossChainForm.addEventListener('submit', (e) => this.handleCrossChainSubmit(e));
        }

        // Chain and token selectors
        const fromChainSelect = document.getElementById('fromChain');
        const toChainSelect = document.getElementById('toChain');
        const fromTokenSelect = document.getElementById('fromToken');
        const amountInput = document.getElementById('crossChainAmount');

        if (fromChainSelect) {
            fromChainSelect.addEventListener('change', () => this.updateTokenOptions('from'));
        }
        
        if (toChainSelect) {
            toChainSelect.addEventListener('change', () => this.updateTokenOptions('to'));
        }

        if (fromTokenSelect || amountInput) {
            [fromTokenSelect, amountInput].forEach(element => {
                if (element) {
                    element.addEventListener('change', () => this.updateQuote());
                    element.addEventListener('input', () => this.debounceUpdateQuote());
                }
            });
        }

        // Quick chain buttons
        document.querySelectorAll('.quick-chain-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chain = e.target.dataset.chain;
                this.selectQuickChain(chain);
            });
        });
    }

    updateChainSelectors() {
        const fromChainSelect = document.getElementById('fromChain');
        const toChainSelect = document.getElementById('toChain');

        if (!fromChainSelect || !toChainSelect) return;

        // Clear existing options
        [fromChainSelect, toChainSelect].forEach(select => {
            select.innerHTML = '<option value="">Select Chain</option>';
        });

        // Add chain options
        Object.entries(this.supportedChains).forEach(([chainId, chainInfo]) => {
            const option = document.createElement('option');
            option.value = chainId;
            option.textContent = `${chainInfo.name} (${chainInfo.native_token})`;
            option.disabled = !chainInfo.rpc_connected;
            
            if (!chainInfo.rpc_connected) {
                option.textContent += ' - Offline';
            }

            fromChainSelect.appendChild(option.cloneNode(true));
            toChainSelect.appendChild(option);
        });

        // Set Flare as default from chain
        fromChainSelect.value = 'flare';
        this.updateTokenOptions('from');
    }

    updateTokenOptions(direction) {
        const chainSelect = document.getElementById(`${direction}Chain`);
        const tokenSelect = document.getElementById(`${direction}Token`);
        
        if (!chainSelect || !tokenSelect) return;

        const selectedChain = chainSelect.value;
        const chainInfo = this.supportedChains[selectedChain];
        
        tokenSelect.innerHTML = '<option value="">Select Token</option>';
        
        if (chainInfo && chainInfo.tokens) {
            chainInfo.tokens.forEach(token => {
                const option = document.createElement('option');
                option.value = token;
                option.textContent = token;
                tokenSelect.appendChild(option);
            });
        }
    }

    debounceUpdateQuote() {
        clearTimeout(this.quoteTimeout);
        this.quoteTimeout = setTimeout(() => this.updateQuote(), 500);
    }

    async updateQuote() {
        const fromChain = document.getElementById('fromChain')?.value;
        const toChain = document.getElementById('toChain')?.value;
        const fromToken = document.getElementById('fromToken')?.value;
        const toToken = document.getElementById('toToken')?.value;
        const amount = parseFloat(document.getElementById('crossChainAmount')?.value || 0);

        if (!fromChain || !toChain || !fromToken || !toToken || !amount || amount <= 0) {
            this.clearQuote();
            return;
        }

        try {
            this.showQuoteLoading();
            
            const response = await fetch('/api/cross_chain_quote', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    from_chain: fromChain,
                    to_chain: toChain,
                    from_token: fromToken,
                    to_token: toToken,
                    amount: amount
                })
            });

            const result = await response.json();

            if (result.success) {
                this.currentQuote = result.quote;
                this.displayQuote(result.quote);
            } else {
                this.displayQuoteError(result.message);
            }
        } catch (error) {
            console.error('Error getting quote:', error);
            this.displayQuoteError('Failed to get quote');
        }
    }

    showQuoteLoading() {
        const quoteDisplay = document.getElementById('quoteDisplay');
        if (quoteDisplay) {
            quoteDisplay.innerHTML = `
                <div class="d-flex justify-content-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Getting quote...</span>
                    </div>
                </div>
            `;
            quoteDisplay.style.display = 'block';
        }
    }

    displayQuote(quote) {
        const quoteDisplay = document.getElementById('quoteDisplay');
        if (!quoteDisplay) return;

        const priceImpactClass = quote.price_impact > 3 ? 'text-danger' : 
                                quote.price_impact > 1 ? 'text-warning' : 'text-success';

        quoteDisplay.innerHTML = `
            <div class="card bg-dark border-secondary">
                <div class="card-body">
                    <h6 class="card-title text-primary">
                        <i class="fas fa-route me-2"></i>Cross-Chain Quote
                    </h6>
                    
                    <div class="row mb-3">
                        <div class="col">
                            <small class="text-muted">You Send</small>
                            <div class="h5">${quote.amount_in} ${quote.from_token}</div>
                            <small class="text-muted">on ${quote.from_chain}</small>
                        </div>
                        <div class="col-auto align-self-center">
                            <i class="fas fa-arrow-right text-primary"></i>
                        </div>
                        <div class="col">
                            <small class="text-muted">You Receive</small>
                            <div class="h5 text-success">${quote.amount_out.toFixed(6)} ${quote.to_token}</div>
                            <small class="text-muted">on ${quote.to_chain}</small>
                        </div>
                    </div>

                    <div class="row mb-3">
                        <div class="col-6">
                            <small class="text-muted">Bridge Fee</small>
                            <div>$${quote.bridge_fee.toFixed(2)}</div>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Gas Estimate</small>
                            <div>$${quote.gas_estimate.toFixed(2)}</div>
                        </div>
                    </div>

                    <div class="row mb-3">
                        <div class="col-6">
                            <small class="text-muted">Total Fees</small>
                            <div class="fw-bold">$${quote.total_fee_usd.toFixed(2)}</div>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Price Impact</small>
                            <div class="${priceImpactClass}">${quote.price_impact.toFixed(2)}%</div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <small class="text-muted">Route: ${quote.route.name}</small><br>
                        <small class="text-muted">Est. Time: ${quote.estimated_time}</small>
                    </div>

                    <button type="button" class="btn btn-primary w-100" onclick="crossChainTrader.executeCrossChainSwap()">
                        <i class="fas fa-rocket me-2"></i>Execute Cross-Chain Swap
                    </button>
                </div>
            </div>
        `;
        quoteDisplay.style.display = 'block';
    }

    displayQuoteError(message) {
        const quoteDisplay = document.getElementById('quoteDisplay');
        if (quoteDisplay) {
            quoteDisplay.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>
            `;
            quoteDisplay.style.display = 'block';
        }
    }

    clearQuote() {
        const quoteDisplay = document.getElementById('quoteDisplay');
        if (quoteDisplay) {
            quoteDisplay.style.display = 'none';
            quoteDisplay.innerHTML = '';
        }
        this.currentQuote = null;
    }

    async executeCrossChainSwap() {
        if (!this.currentQuote) {
            showAlert('No quote available', 'danger');
            return;
        }

        try {
            const response = await fetch('/api/execute_cross_chain_swap', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    from_chain: this.currentQuote.from_chain,
                    to_chain: this.currentQuote.to_chain,
                    from_token: this.currentQuote.from_token,
                    to_token: this.currentQuote.to_token,
                    amount: this.currentQuote.amount_in
                })
            });

            const result = await response.json();

            if (result.success) {
                showAlert(result.message, 'success');
                this.clearQuote();
                document.getElementById('crossChainForm')?.reset();
                
                // Refresh portfolio after successful trade
                if (typeof refreshPortfolio === 'function') {
                    setTimeout(refreshPortfolio, 2000);
                }
            } else {
                showAlert(result.message, 'danger');
            }
        } catch (error) {
            console.error('Error executing cross-chain swap:', error);
            showAlert('Cross-chain swap failed', 'danger');
        }
    }

    selectQuickChain(chain) {
        const toChainSelect = document.getElementById('toChain');
        if (toChainSelect) {
            toChainSelect.value = chain;
            this.updateTokenOptions('to');
            this.updateQuote();
        }
    }

    handleCrossChainSubmit(e) {
        e.preventDefault();
        if (this.currentQuote) {
            this.executeCrossChainSwap();
        } else {
            this.updateQuote();
        }
    }
}

// Initialize cross-chain trader when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.crossChainTrader = new CrossChainTrader();
});

// Utility function for showing alerts (if not already defined)
function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer') || document.body;
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}
