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
    try {
        // Add a timestamp parameter to avoid caching issues
        const timestamp = new Date().getTime();
        
        fetch(`/api/dashboard/summary?_=${timestamp}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Dashboard data received:', data);
                
                // Validate response structure
                if (!data) {
                    throw new Error('Empty response received');
                }
                
                if (data.status !== 'success') {
                    throw new Error(`API returned error status: ${data.status}`);
                }
                
                if (!data.data) {
                    throw new Error('Response missing data property');
                }
                
                // Process data
                const dashboardData = data.data;
                
                // Update components with data
                updateStats(dashboardData);
                updateCharts(dashboardData.chart_data || { labels: [], datasets: [] });
                updateRecentData(dashboardData.latest_records || []);
                
                // Remove any error messages that might be displayed
                const errorElement = document.getElementById('dashboard-error');
                if (errorElement) {
                    errorElement.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error fetching dashboard data:', error);
                
                // Display error message to the user
                const mainContent = document.querySelector('.main-content');
                if (mainContent) {
                    // Check if error element already exists
                    let errorElement = document.getElementById('dashboard-error');
                    
                    if (!errorElement) {
                        // Create error element if it doesn't exist
                        errorElement = document.createElement('div');
                        errorElement.id = 'dashboard-error';
                        errorElement.className = 'alert alert-danger mt-3';
                        errorElement.role = 'alert';
                        mainContent.prepend(errorElement);
                    }
                    
                    // Update error message
                    errorElement.innerHTML = `
                        <h4 class="alert-heading">Dashboard Error</h4>
                        <p>There was a problem loading the dashboard data. The dashboard will automatically try again in a moment.</p>
                        <hr>
                        <p class="mb-0">Error details: ${error.message}</p>
                    `;
                    errorElement.style.display = 'block';
                }
                
                // Use default/empty data to avoid breaking the UI
                updateStats({
                    total_webhooks: 0,
                    source_counts: {}
                });
                updateCharts({ labels: [], datasets: [] });
                updateRecentData([]);
            });
    } catch (error) {
        console.error('Critical error in loadDashboardData:', error);
    }
}

/**
 * Update dashboard statistics
 */
function updateStats(data) {
    try {
        if (!data) {
            console.warn('No data provided to updateStats');
            return;
        }
        
        // Update total webhooks count
        const totalElement = document.getElementById('total-webhooks');
        if (totalElement) {
            // Ensure we always have a number, defaulting to 0
            const totalCount = typeof data.total_webhooks === 'number' ? data.total_webhooks : 0;
            totalElement.textContent = totalCount;
        } else {
            console.warn('Element with ID "total-webhooks" not found');
        }
        
        // Update source-specific counts if source_counts exists
        if (data.source_counts && typeof data.source_counts === 'object') {
            // First, initialize all source counts to 0
            const allSourceElements = document.querySelectorAll('[id^="source-count-"]');
            
            if (allSourceElements.length > 0) {
                allSourceElements.forEach(element => {
                    element.textContent = '0';
                });
                
                // Then update with actual values
                for (const source in data.source_counts) {
                    if (Object.prototype.hasOwnProperty.call(data.source_counts, source)) {
                        const countElement = document.getElementById(`source-count-${source}`);
                        if (countElement) {
                            const count = typeof data.source_counts[source] === 'number' ? 
                                data.source_counts[source] : 0;
                            countElement.textContent = count;
                        }
                    }
                }
            } else {
                console.warn('No source count elements found with ID pattern "source-count-*"');
            }
        } else {
            console.warn('No source_counts data provided or it is not an object', data);
        }
    } catch (error) {
        console.error('Error in updateStats:', error);
    }
}

/**
 * Update dashboard charts
 */
function updateCharts(chartData) {
    // Skip if no chart data
    if (!chartData) return;
    
    // Line chart for webhooks over time is updated in charts.js
    updateLineChart(chartData);
    
    // Update doughnut chart for source distribution
    updateDoughnutChart(chartData);
}

/**
 * Update recent data table
 */
function updateRecentData(records) {
    try {
        const tbody = document.getElementById('recent-webhooks-tbody');
        
        if (!tbody) {
            console.warn('No element found with ID "recent-webhooks-tbody"');
            return;
        }
        
        // Display message if no records or empty array
        if (!records || !Array.isArray(records) || records.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">No webhook data yet</td></tr>';
            return;
        }
        
        // Clear existing content
        tbody.innerHTML = '';
        
        // Keep track of errors for reporting
        let errorCount = 0;
        
        // Process each record
        records.forEach((record, index) => {
            try {
                if (!record) {
                    console.warn(`Skipping null or undefined record at index ${index}`);
                    return;
                }
                
                const row = document.createElement('tr');
                
                // Format timestamp safely
                let formattedTime = 'Invalid date';
                try {
                    if (record.timestamp) {
                        const timestamp = new Date(record.timestamp);
                        if (!isNaN(timestamp.getTime())) {
                            formattedTime = timestamp.toLocaleTimeString();
                        }
                    }
                } catch (e) {
                    console.warn(`Invalid timestamp for record ${index}:`, e);
                }
                
                // Get sample data from payload safely
                let dataSample = 'No data';
                try {
                    if (record.data && typeof record.data === 'object') {
                        const keys = Object.keys(record.data);
                        if (keys.length > 0) {
                            // Find first non-source key, or use the first key if none found
                            const firstKey = keys.find(key => key !== 'source') || keys[0];
                            
                            // Get value and convert to string safely
                            let value = record.data[firstKey];
                            let valueStr = '';
                            
                            if (value === null) {
                                valueStr = 'null';
                            } else if (value === undefined) {
                                valueStr = 'undefined';
                            } else if (typeof value === 'object') {
                                try {
                                    valueStr = JSON.stringify(value).substring(0, 30);
                                } catch (e) {
                                    valueStr = '[Object]';
                                }
                            } else {
                                valueStr = String(value).substring(0, 30);
                            }
                            
                            dataSample = `${firstKey}: ${valueStr}${valueStr.length >= 30 ? '...' : ''}`;
                        }
                    }
                } catch (e) {
                    console.warn(`Error processing payload for record ${index}:`, e);
                }
                
                // Get source safely
                const source = record.source || 'other';
                
                // Create row HTML
                row.innerHTML = `
                    <td>${formattedTime}</td>
                    <td><span class="badge" style="background-color: ${getSourceColor(source)}">${source}</span></td>
                    <td>${dataSample}</td>
                `;
                
                tbody.appendChild(row);
            } catch (rowError) {
                errorCount++;
                console.error(`Error processing record at index ${index}:`, rowError);
                
                // Only add error placeholder rows for first few errors to avoid filling the table
                if (errorCount <= 3) {
                    const errorRow = document.createElement('tr');
                    errorRow.innerHTML = `
                        <td colspan="3" class="text-danger">Error processing webhook data</td>
                    `;
                    tbody.appendChild(errorRow);
                }
            }
        });
        
        // If all records failed, ensure we display a message
        if (errorCount === records.length) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Error processing webhook data</td></tr>';
        }
    } catch (error) {
        console.error('Error in updateRecentData:', error);
    }
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
    try {
        // Show loading state
        showFilterLoading(true);
        
        // Get date range filter values
        let dateRange, dateFrom, dateTo;
        
        try {
            const dateRangeElement = document.getElementById('date-range');
            dateRange = dateRangeElement ? dateRangeElement.value : 'week';
            
            // Set date range based on selection
            if (dateRange === 'custom') {
                const dateFromElement = document.getElementById('date-from');
                const dateToElement = document.getElementById('date-to');
                
                dateFrom = dateFromElement && dateFromElement.value ? dateFromElement.value : '';
                dateTo = dateToElement && dateToElement.value ? dateToElement.value : '';
                
                // Validate date format
                if (dateFrom && !/^\d{4}-\d{2}-\d{2}$/.test(dateFrom)) {
                    console.warn('Invalid date format for dateFrom:', dateFrom);
                    dateFrom = '';
                }
                
                if (dateTo && !/^\d{4}-\d{2}-\d{2}$/.test(dateTo)) {
                    console.warn('Invalid date format for dateTo:', dateTo);
                    dateTo = '';
                }
            } else {
                // Use preset date range
                const dates = getDateRangeFromOption(dateRange);
                dateFrom = dates.from;
                dateTo = dates.to;
            }
        } catch (dateError) {
            console.error('Error processing date filters:', dateError);
            // Fall back to last week
            const dates = getDateRangeFromOption('week');
            dateFrom = dates.from;
            dateTo = dates.to;
        }
        
        // Get selected sources
        const selectedSources = [];
        try {
            const checkboxes = document.querySelectorAll('.source-filter-checkboxes input:checked');
            checkboxes.forEach(checkbox => {
                if (checkbox && checkbox.value) {
                    selectedSources.push(checkbox.value);
                }
            });
        } catch (sourceError) {
            console.error('Error getting selected sources:', sourceError);
        }
        
        // Build filter parameters
        const params = new URLSearchParams();
        
        if (dateFrom) params.append('from', dateFrom + 'T00:00:00');
        if (dateTo) params.append('to', dateTo + 'T23:59:59');
        
        // Fetch filtered data with a timeout
        const fetchTimeout = setTimeout(() => {
            showFilterError('Request timed out. Please try again.');
        }, 15000); // 15 second timeout
        
        fetch(`/api/webhook/data?${params.toString()}`)
            .then(response => {
                clearTimeout(fetchTimeout);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Hide loading state
                showFilterLoading(false);
                
                // Check for valid response structure
                if (!data || data.status !== 'success' || !Array.isArray(data.data)) {
                    throw new Error('Invalid data format received from API');
                }
                
                // Filter by selected sources client-side
                let filteredData = data.data;
                if (selectedSources.length > 0) {
                    filteredData = data.data.filter(item => 
                        item && item.source && selectedSources.includes(item.source)
                    );
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
                
                // Update filter success message
                const filterMessageEl = document.getElementById('filter-message');
                if (filterMessageEl) {
                    if (filteredData.length === 0) {
                        filterMessageEl.className = 'alert alert-info mt-3';
                        filterMessageEl.textContent = 'No data found for the selected filters';
                        filterMessageEl.style.display = 'block';
                    } else {
                        filterMessageEl.style.display = 'none';
                    }
                }
            })
            .catch(error => {
                // Clear timeout if there was an error
                clearTimeout(fetchTimeout);
                
                // Hide loading, show error
                showFilterLoading(false);
                showFilterError('Failed to apply filters: ' + error.message);
                
                console.error('Error applying filters:', error);
                
                // Reset UI to empty state
                updateStats({ total_webhooks: 0, source_counts: {} });
                updateCharts({ labels: [], datasets: [] });
                updateRecentData([]);
            });
    } catch (error) {
        showFilterLoading(false);
        showFilterError('An unexpected error occurred: ' + error.message);
        console.error('Critical error in applyFilters:', error);
    }
}

/**
 * Show or hide the filter loading state
 */
function showFilterLoading(isLoading) {
    // Get or create loading indicator
    let loadingEl = document.getElementById('filter-loading');
    
    if (!loadingEl) {
        loadingEl = document.createElement('div');
        loadingEl.id = 'filter-loading';
        loadingEl.className = 'alert alert-info mt-3';
        loadingEl.textContent = 'Loading data...';
        
        const filterForm = document.getElementById('filter-form');
        if (filterForm) {
            filterForm.parentNode.insertBefore(loadingEl, filterForm.nextSibling);
        }
    }
    
    loadingEl.style.display = isLoading ? 'block' : 'none';
    
    // Hide error message if showing loading
    if (isLoading) {
        const errorEl = document.getElementById('filter-error');
        if (errorEl) {
            errorEl.style.display = 'none';
        }
    }
}

/**
 * Show filter error message
 */
function showFilterError(message) {
    // Get or create error element
    let errorEl = document.getElementById('filter-error');
    
    if (!errorEl) {
        errorEl = document.createElement('div');
        errorEl.id = 'filter-error';
        errorEl.className = 'alert alert-danger mt-3';
        
        const filterForm = document.getElementById('filter-form');
        if (filterForm) {
            filterForm.parentNode.insertBefore(errorEl, filterForm.nextSibling);
        }
    }
    
    errorEl.textContent = message;
    errorEl.style.display = 'block';
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
        'stripe': '#6772E5', 
        'paypal': '#003087',
        'cart': '#FF9800',
        'google': '#EA4335',
        'whatsapp': '#25D366',
        'facebook': '#1877F2',
        'other': '#9C27B0'
    };
    
    return colors[source] || colors.other;
}
