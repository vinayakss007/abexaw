/**
 * Dashboard.js - Handles dashboard functionality
 * 
 * This script manages data loading, filtering, and display for the dashboard page.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Load dashboard data initially
    loadDashboardData();
    
    // Set up event listeners
    setupEventListeners();
    
    // Refresh data automatically every 60 seconds
    setInterval(loadDashboardData, 60000);
});

/**
 * Load dashboard data from API
 */
function loadDashboardData() {
    fetch('/api/dashboard/summary')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateStats(data.data);
                updateCharts(data.data.chart_data);
                updateRecentData(data.data.latest_records);
            } else {
                console.error('Error loading dashboard data:', data.message);
            }
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
        });
}

/**
 * Update dashboard statistics
 */
function updateStats(data) {
    // Update total webhooks count
    document.getElementById('total-webhooks').textContent = data.total_webhooks;
    
    // Update source-specific counts
    for (const source in data.source_counts) {
        const countElement = document.getElementById(`source-count-${source}`);
        if (countElement) {
            countElement.textContent = data.source_counts[source];
        }
    }
}

/**
 * Update dashboard charts
 */
function updateCharts(chartData) {
    // Line chart for webhooks over time is updated in charts.js
    updateLineChart(chartData);
    
    // Update doughnut chart for source distribution
    updateDoughnutChart(chartData);
}

/**
 * Update recent data table
 */
function updateRecentData(records) {
    const tbody = document.getElementById('recent-webhooks-tbody');
    
    if (!records || records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center">No webhook data yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    
    records.forEach(record => {
        const row = document.createElement('tr');
        
        // Format timestamp
        const timestamp = new Date(record.timestamp);
        const formattedTime = timestamp.toLocaleTimeString();
        
        // Get sample data from payload
        let dataSample = '';
        if (record.data) {
            const firstKey = Object.keys(record.data).find(key => key !== 'source');
            if (firstKey) {
                dataSample = `${firstKey}: ${record.data[firstKey].toString().substring(0, 30)}...`;
            }
        }
        
        // Create row HTML
        row.innerHTML = `
            <td>${formattedTime}</td>
            <td><span class="badge" style="background-color: ${getSourceColor(record.source)}">${record.source || 'other'}</span></td>
            <td>${dataSample || 'No data'}</td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Set up event listeners for dashboard controls
 */
function setupEventListeners() {
    // Date range selector
    const dateRangeSelect = document.getElementById('date-range');
    const customDateRange = document.getElementById('custom-date-range');
    
    if (dateRangeSelect) {
        dateRangeSelect.addEventListener('change', function() {
            if (this.value === 'custom') {
                customDateRange.style.display = 'block';
            } else {
                customDateRange.style.display = 'none';
            }
        });
    }
    
    // Filter form
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            applyFilters();
        });
    }
    
    // Reset filters button
    const resetFiltersBtn = document.getElementById('reset-filters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            resetFilters();
        });
    }
}

/**
 * Apply dashboard filters
 */
function applyFilters() {
    // Get filter values
    const dateRange = document.getElementById('date-range').value;
    let dateFrom, dateTo;
    
    // Set date range based on selection
    if (dateRange === 'custom') {
        dateFrom = document.getElementById('date-from').value;
        dateTo = document.getElementById('date-to').value;
    } else {
        const dates = getDateRangeFromOption(dateRange);
        dateFrom = dates.from;
        dateTo = dates.to;
    }
    
    // Get selected sources
    const selectedSources = [];
    document.querySelectorAll('.source-filter-checkboxes input:checked').forEach(checkbox => {
        selectedSources.push(checkbox.value);
    });
    
    // Build filter parameters
    const params = new URLSearchParams();
    
    if (dateFrom) params.append('from', dateFrom + 'T00:00:00');
    if (dateTo) params.append('to', dateTo + 'T23:59:59');
    
    // Fetch filtered data
    fetch(`/api/webhook/data?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Filter by selected sources client-side
                let filteredData = data.data;
                if (selectedSources.length > 0) {
                    filteredData = data.data.filter(item => selectedSources.includes(item.source));
                }
                
                // Create chart data
                const chartData = transformDataForCharts(filteredData);
                
                // Update UI with filtered data
                updateStats({
                    total_webhooks: filteredData.length,
                    source_counts: countBySource(filteredData)
                });
                updateCharts(chartData);
                updateRecentData(filteredData.slice(0, 5));
            }
        })
        .catch(error => {
            console.error('Error applying filters:', error);
        });
}

/**
 * Reset dashboard filters
 */
function resetFilters() {
    // Reset date range to default
    document.getElementById('date-range').value = 'week';
    document.getElementById('custom-date-range').style.display = 'none';
    
    // Check all source checkboxes
    document.querySelectorAll('.source-filter-checkboxes input').forEach(checkbox => {
        checkbox.checked = true;
    });
    
    // Reload dashboard with default data
    loadDashboardData();
}

/**
 * Get date range from option
 */
function getDateRangeFromOption(option) {
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    
    const from = new Date(today);
    
    switch (option) {
        case 'today':
            from.setHours(0, 0, 0, 0);
            break;
        case 'yesterday':
            from.setDate(from.getDate() - 1);
            from.setHours(0, 0, 0, 0);
            break;
        case 'week':
            from.setDate(from.getDate() - 6);
            from.setHours(0, 0, 0, 0);
            break;
        case 'month':
            from.setDate(from.getDate() - 29);
            from.setHours(0, 0, 0, 0);
            break;
    }
    
    return {
        from: from.toISOString().split('T')[0],
        to: today.toISOString().split('T')[0]
    };
}

/**
 * Transform data for charts
 */
function transformDataForCharts(data) {
    // Get the dates for the last 7 days
    const today = new Date();
    const dates = [];
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
    }
    
    // Initialize source data
    const sources = {};
    
    // Count data by date and source
    data.forEach(item => {
        // Extract timestamp and convert to date
        let timestamp;
        try {
            timestamp = new Date(item.timestamp).toISOString().split('T')[0];
        } catch (e) {
            return;
        }
        
        const source = item.source || 'other';
        
        // Initialize source if not exists
        if (!sources[source]) {
            sources[source] = {};
            dates.forEach(date => {
                sources[source][date] = 0;
            });
        }
        
        // Increment count if timestamp is in the last 7 days
        if (dates.includes(timestamp)) {
            sources[source][timestamp]++;
        }
    });
    
    // Format for Chart.js
    const chartData = {
        labels: dates,
        datasets: []
    };
    
    // Create datasets for each source
    for (const source in sources) {
        chartData.datasets.push({
            label: source.charAt(0).toUpperCase() + source.slice(1),
            data: dates.map(date => sources[source][date]),
            backgroundColor: getSourceColor(source),
            borderColor: getSourceColor(source),
            fill: false
        });
    }
    
    return chartData;
}

/**
 * Count data by source
 */
function countBySource(data) {
    const counts = {};
    
    data.forEach(item => {
        const source = item.source || 'other';
        counts[source] = (counts[source] || 0) + 1;
    });
    
    return counts;
}

/**
 * Get color for a specific source
 */
function getSourceColor(source) {
    const colors = {
        'crm': '#4CAF50',
        'form': '#2196F3',
        'email': '#F44336',
        'other': '#9C27B0'
    };
    
    return colors[source] || colors.other;
}
