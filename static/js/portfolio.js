// Portfolio page JavaScript

let allocationChart;
let performanceChart;

document.addEventListener('DOMContentLoaded', function() {
    initializePortfolioCharts();
});

function initializePortfolioCharts() {
    initializeAllocationChart();
    initializePerformanceChart();
}

function initializeAllocationChart() {
    const ctx = document.getElementById('allocationChart');
    if (!ctx || typeof portfolioData === 'undefined' || portfolioData.length === 0) {
        // Show empty state
        ctx.getContext('2d').fillStyle = '#8b949e';
        ctx.getContext('2d').font = '16px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.getContext('2d').textAlign = 'center';
        ctx.getContext('2d').fillText('No portfolio data available', ctx.width / 2, ctx.height / 2);
        return;
    }

    const labels = portfolioData.map(item => item.token.symbol);
    const data = portfolioData.map(item => item.current_value);
    const backgroundColors = [
        '#1f6feb', '#238636', '#da3633', '#f85149', 
        '#ffa657', '#a5a5a5', '#8b949e'
    ];

    allocationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors.slice(0, data.length),
                borderWidth: 2,
                borderColor: '#21262d'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#f0f6fc',
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const percentage = ((context.parsed / totalValue) * 100).toFixed(1);
                            return `${context.label}: $${context.parsed.toFixed(2)} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

function initializePerformanceChart() {
    const ctx = document.getElementById('performanceChart');
    if (!ctx || typeof portfolioData === 'undefined' || portfolioData.length === 0) {
        return;
    }

    const labels = portfolioData.map(item => item.token.symbol);
    const pnlData = portfolioData.map(item => item.pnl_percent);
    
    // Color bars based on performance
    const backgroundColors = pnlData.map(value => 
        value >= 0 ? '#2ea043' : '#da3633'
    );

    performanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Return %',
                data: pnlData,
                backgroundColor: backgroundColors,
                borderWidth: 1,
                borderColor: '#21262d'
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
                    beginAtZero: true,
                    grid: {
                        color: '#30363d'
                    },
                    ticks: {
                        color: '#8b949e',
                        callback: function(value) {
                            return value.toFixed(1) + '%';
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

// Update portfolio data when prices refresh
function updatePortfolioCharts() {
    if (allocationChart) {
        allocationChart.update();
    }
    if (performanceChart) {
        performanceChart.update();
    }
}

// Listen for price updates
document.addEventListener('pricesUpdated', function() {
    updatePortfolioCharts();
});
