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
    if (!lineChart) {
        console.warn('Line chart not initialized');
        return;
    }
    
    if (!chartData || !chartData.labels || !chartData.datasets) {
        console.warn('Invalid chart data for line chart', chartData);
        
        // Display empty data state
        try {
            lineChart.data.labels = ['No Data'];
            lineChart.data.datasets = [{
                label: 'No Data Available',
                data: [0],
                backgroundColor: '#e0e0e0',
                borderColor: '#e0e0e0'
            }];
            lineChart.update();
        } catch (e) {
            console.error('Failed to show empty state in line chart:', e);
        }
        return;
    }
    
    try {
        // Make sure datasets contain valid data
        const validatedDatasets = chartData.datasets.map(dataset => {
            // Ensure dataset has all required properties
            return {
                label: dataset.label || 'Unknown',
                data: Array.isArray(dataset.data) ? dataset.data.map(val => Number(val) || 0) : [0],
                backgroundColor: dataset.backgroundColor || '#cccccc',
                borderColor: dataset.borderColor || '#cccccc',
                fill: dataset.fill !== undefined ? dataset.fill : false
            };
        });
        
        lineChart.data.labels = chartData.labels;
        lineChart.data.datasets = validatedDatasets;
        lineChart.update();
    } catch (error) {
        console.error('Error updating line chart:', error);
        
        // On error, display simple placeholder
        try {
            lineChart.data.labels = ['Error'];
            lineChart.data.datasets = [{
                label: 'Error Loading Data',
                data: [0],
                backgroundColor: '#ffcccc',
                borderColor: '#ffcccc'
            }];
            lineChart.update();
        } catch (e) {
            console.error('Failed to show error state in line chart:', e);
        }
    }
}

/**
 * Update doughnut chart with new data
 */
function updateDoughnutChart(chartData) {
    if (!doughnutChart) {
        console.warn('Doughnut chart not initialized');
        return;
    }
    
    if (!chartData || !chartData.datasets) {
        console.warn('Invalid chart data for doughnut chart');
        
        // Display no data in chart
        doughnutChart.data.labels = ['No Data'];
        doughnutChart.data.datasets[0].data = [1];
        doughnutChart.data.datasets[0].backgroundColor = ['#e0e0e0'];
        doughnutChart.update();
        return;
    }
    
    try {
        // Calculate source totals from the line chart data
        const sourceTotals = {};
        const sourceColors = {};
        
        chartData.datasets.forEach(dataset => {
            if (!dataset || !dataset.data) return;
            
            const sourceTotal = dataset.data.reduce((sum, value) => sum + (Number(value) || 0), 0);
            const sourceName = dataset.label || 'Unknown';
            
            sourceTotals[sourceName] = sourceTotal;
            sourceColors[sourceName] = dataset.backgroundColor || '#cccccc';
        });
        
        // Prepare data for doughnut chart
        const labels = Object.keys(sourceTotals);
        const data = Object.values(sourceTotals);
        const colors = labels.map(label => sourceColors[label]);
        
        // Check if we have actual data
        if (data.length === 0 || data.every(value => value === 0)) {
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
    } catch (error) {
        console.error('Error updating doughnut chart:', error);
        
        // On error, display simple placeholder
        try {
            doughnutChart.data.labels = ['Error'];
            doughnutChart.data.datasets[0].data = [1];
            doughnutChart.data.datasets[0].backgroundColor = ['#ffcccc'];
            doughnutChart.update();
        } catch (e) {
            console.error('Failed to show error state in doughnut chart:', e);
        }
    }
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
