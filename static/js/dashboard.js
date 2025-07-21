// Dashboard JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    initializePortfolioChart();
});

function initializePortfolioChart() {
    const ctx = document.getElementById('portfolioChart');
    if (!ctx) return;

    // Sample portfolio performance data
    const labels = [];
    const data = [];
    const now = new Date();
    
    // Generate 30 days of sample performance data
    for (let i = 29; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Simulate portfolio growth with some volatility
        const baseValue = 1000;
        const growth = (29 - i) * 10; // Gradual growth
        const volatility = Math.random() * 100 - 50; // ±50 volatility
        data.push(baseValue + growth + volatility);
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portfolio Value',
                data: data,
                borderColor: '#1f6feb',
                backgroundColor: 'rgba(31, 111, 235, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6
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
                            return '$' + value.toFixed(0);
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
}

// Auto-refresh dashboard data
setInterval(function() {
    refreshPrices();
}, 60000); // Refresh every minute
