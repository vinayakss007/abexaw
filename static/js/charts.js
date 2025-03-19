/**
 * Charts.js - Handles chart creation and updates
 * 
 * This script manages the creation and updating of dashboard charts
 * using Chart.js library.
 */

// Store chart instances to update them later
let lineChart = null;
let doughnutChart = null;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts with empty data
    initializeCharts();
});

/**
 * Initialize dashboard charts
 */
function initializeCharts() {
    initializeLineChart();
    initializeDoughnutChart();
}

/**
 * Initialize the line chart for webhooks over time
 */
function initializeLineChart() {
    const ctx = document.getElementById('webhook-time-chart');
    
    if (!ctx) return;
    
    const defaultData = {
        labels: getLast7Days(),
        datasets: []
    };
    
    // Line chart configuration
    const config = {
        type: 'line',
        data: defaultData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            // Format date for tooltip title
                            return formatDateString(context[0].label);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                },
                x: {
                    ticks: {
                        callback: function(value, index) {
                            // Only show some dates to avoid crowding
                            return index % 2 === 0 ? this.getLabelForValue(value).split('-').slice(1).join('/') : '';
                        }
                    }
                }
            }
        }
    };
    
    // Create the chart
    lineChart = new Chart(ctx, config);
}

/**
 * Initialize the doughnut chart for source distribution
 */
function initializeDoughnutChart() {
    const ctx = document.getElementById('source-distribution-chart');
    
    if (!ctx) return;
    
    const defaultData = {
        labels: ['No Data'],
        datasets: [{
            data: [1],
            backgroundColor: ['#e0e0e0'],
            hoverOffset: 4
        }]
    };
    
    // Doughnut chart configuration
    const config = {
        type: 'doughnut',
        data: defaultData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    };
    
    // Create the chart
    doughnutChart = new Chart(ctx, config);
}

/**
 * Update line chart with new data
 */
function updateLineChart(chartData) {
    if (!lineChart || !chartData) return;
    
    lineChart.data.labels = chartData.labels;
    lineChart.data.datasets = chartData.datasets;
    lineChart.update();
}

/**
 * Update doughnut chart with new data
 */
function updateDoughnutChart(chartData) {
    if (!doughnutChart || !chartData || !chartData.datasets || chartData.datasets.length === 0) return;
    
    // Calculate source totals from the line chart data
    const sourceTotals = {};
    const sourceColors = {};
    
    chartData.datasets.forEach(dataset => {
        const sourceTotal = dataset.data.reduce((sum, value) => sum + value, 0);
        const sourceName = dataset.label;
        
        sourceTotals[sourceName] = sourceTotal;
        sourceColors[sourceName] = dataset.backgroundColor;
    });
    
    // Prepare data for doughnut chart
    const labels = Object.keys(sourceTotals);
    const data = Object.values(sourceTotals);
    const colors = labels.map(label => sourceColors[label]);
    
    // Check if we have actual data
    if (data.every(value => value === 0)) {
        // No data, show "No Data" placeholder
        doughnutChart.data.labels = ['No Data'];
        doughnutChart.data.datasets[0].data = [1];
        doughnutChart.data.datasets[0].backgroundColor = ['#e0e0e0'];
    } else {
        // Update with real data
        doughnutChart.data.labels = labels;
        doughnutChart.data.datasets[0].data = data;
        doughnutChart.data.datasets[0].backgroundColor = colors;
    }
    
    doughnutChart.update();
}

/**
 * Get formatted dates for the last 7 days
 */
function getLast7Days() {
    const dates = [];
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
    }
    return dates;
}

/**
 * Format a date string for display
 */
function formatDateString(dateStr) {
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return dateStr;
    }
}
