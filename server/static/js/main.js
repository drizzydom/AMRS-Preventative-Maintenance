// Main JavaScript for AMRS Maintenance Tracker

// Global variables
let authToken = localStorage.getItem('auth_token');
let partsList = [];
let sitesList = [];
let machinesList = [];

// Helper function for API calls
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const options = {
            method,
            headers,
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Load parts data with filters
async function loadParts() {
    try {
        const siteId = document.getElementById('site-filter').value;
        const machineId = document.getElementById('machine-filter').value;
        
        // Get status filters
        const showOverdue = document.querySelector('.status-checkbox[data-status="overdue"]').checked;
        const showDueSoon = document.querySelector('.status-checkbox[data-status="due_soon"]').checked;
        const showOk = document.querySelector('.status-checkbox[data-status="ok"]').checked;
        
        // Build query string
        let queryParams = [];
        if (siteId != -1) queryParams.push(`site_id=${siteId}`);
        if (machineId != -1) queryParams.push(`machine_id=${machineId}`);
        if (!showOverdue || !showDueSoon || !showOk) {
            const statuses = [];
            if (showOverdue) statuses.push('overdue');
            if (showDueSoon) statuses.push('due_soon');
            if (showOk) statuses.push('ok');
            queryParams.push(`status=${statuses.join(',')}`);
        }
        
        const queryString = queryParams.length ? `?${queryParams.join('&')}` : '';
        
        // Fetch parts data
        const data = await apiCall(`/api/parts${queryString}`);
        partsList = data.parts || [];
        
        // Populate table
        const table = document.getElementById('parts-table').getElementsByTagName('tbody')[0];
        table.innerHTML = '';
        
        if (partsList.length === 0) {
            const row = table.insertRow();
            const cell = row.insertCell(0);
            cell.colSpan = 7;
            cell.textContent = 'No parts match your filter criteria.';
            cell.className = 'no-data';
            return;
        }
        
        partsList.forEach(part => {
            const row = table.insertRow();
            
            const nameCell = row.insertCell(0);
            nameCell.textContent = part.name;
            
            const machineCell = row.insertCell(1);
            machineCell.textContent = part.machine_name;
            
            const siteCell = row.insertCell(2);
            siteCell.textContent = part.site_name;
            
            const lastMaintenanceCell = row.insertCell(3);
            lastMaintenanceCell.textContent = part.last_maintenance || 'Never';
            
            const nextDueCell = row.insertCell(4);
            nextDueCell.textContent = part.next_due || 'Unknown';
            
            const statusCell = row.insertCell(5);
            const statusSpan = document.createElement('span');
            statusSpan.className = `status status-${part.status}`;
            statusSpan.textContent = part.status.replace('_', ' ');
            statusCell.appendChild(statusSpan);
            
            const actionsCell = row.insertCell(6);
            const recordButton = document.createElement('button');
            recordButton.className = 'btn-primary';
            recordButton.textContent = 'Record';
            recordButton.addEventListener('click', () => showMaintenanceModal(part));
            actionsCell.appendChild(recordButton);
            
            // Store part id as data attribute for easy access
            row.dataset.partId = part.id;
            
            // Double-click on row to open maintenance dialog
            row.addEventListener('dblclick', () => showMaintenanceModal(part));
        });
    } catch (error) {
        console.error('Error loading parts:', error);
        alert('Failed to load parts data. Please try again later.');
    }
}

// Load machines for specific site
async function loadMachinesForSite(siteId) {
    try {
        const machineFilter = document.getElementById('machine-filter');
        machineFilter.innerHTML = '<option value="-1">All Machines</option>';
        
        if (siteId == -1) {
            return; // No need to fetch machines for "All Sites"
        }
        
        const data = await apiCall(`/api/machines?site_id=${siteId}`);
        machinesList = data.machines || [];
        
        machinesList.forEach(machine => {
            const option = document.createElement('option');
            option.value = machine.id;
            option.textContent = machine.name;
            machineFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading machines:', error);
    }
}

// Show maintenance modal for a part
function showMaintenanceModal(part) {
    const modal = document.getElementById('maintenance-modal');
    document.getElementById('part-id').value = part.id;
    document.getElementById('part-name').textContent = part.name;
    document.getElementById('maintenance-notes').value = '';
    
    modal.style.display = 'block';
}

// Record maintenance
async function recordMaintenance(event) {
    event.preventDefault();
    
    const partId = document.getElementById('part-id').value;
    const notes = document.getElementById('maintenance-notes').value;
    
    try {
        const response = await apiCall('/api/maintenance/record', 'POST', {
            part_id: partId,
            notes: notes
        });
        
        if (response.status === 'success') {
            document.getElementById('maintenance-modal').style.display = 'none';
            alert('Maintenance recorded successfully!');
            loadParts(); // Refresh the parts list
        } else {
            throw new Error(response.message || 'Unknown error');
        }
    } catch (error) {
        console.error('Error recording maintenance:', error);
        alert('Failed to record maintenance. Please try again.');
    }
}

// Load sites data
async function loadSites() {
    try {
        const data = await apiCall('/api/sites');
        sitesList = data.sites || [];
        
        const siteFilter = document.getElementById('site-filter');
        siteFilter.innerHTML = '<option value="-1">All Sites</option>';
        
        sitesList.forEach(site => {
            const option = document.createElement('option');
            option.value = site.id;
            option.textContent = site.name;
            siteFilter.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading sites:', error);
    }
}

// Initialize the page when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the maintenance page
    const maintenancePage = document.querySelector('.maintenance-page');
    if (maintenancePage) {
        // Load initial data
        loadSites();
        loadParts();
        
        // Set up event listeners for filters
        document.getElementById('site-filter').addEventListener('change', function() {
            loadMachinesForSite(this.value);
            loadParts();
        });
        
        document.getElementById('machine-filter').addEventListener('change', loadParts);
        
        document.querySelectorAll('.status-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', loadParts);
        });
        
        // Close modal when clicking the X button
        document.querySelector('.close-button').addEventListener('click', () => {
            document.getElementById('maintenance-modal').style.display = 'none';
        });
        
        // Close modal when clicking outside
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('maintenance-modal');
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
        
        // Handle form submission
        document.getElementById('maintenance-form').addEventListener('submit', recordMaintenance);
    }
});
