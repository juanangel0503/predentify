// Global variables
let procedures = [];
let providers = [];
let mitigatingFactors = [];
let procedureIndex = 0;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadInitialData();
    setupEventListeners();
});

// Load initial data from server
async function loadInitialData() {
    try {
        // Load procedures, providers, and mitigating factors
        const [proceduresResponse, providersResponse, factorsResponse] = await Promise.all([
            fetch('/api/procedures'),
            fetch('/api/providers'),
            fetch('/api/mitigating_factors')
        ]);

        procedures = await proceduresResponse.json();
        providers = await providersResponse.json();
        mitigatingFactors = await factorsResponse.json();

        // Populate initial dropdowns
        populateProviderDropdown();
        populateProcedureDropdown(0);
        populateMitigatingFactors();

    } catch (error) {
        console.error('Error loading initial data:', error);
        displayError('Failed to load data. Please refresh the page.');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Form submission
    document.getElementById('estimationForm').addEventListener('submit', handleFormSubmit);
    
    // Add procedure button
    document.getElementById('addProcedure').addEventListener('click', addProcedure);
    
    // Provider change - filter procedures
    document.getElementById('provider').addEventListener('change', function() {
        const selectedProvider = this.value;
        if (selectedProvider) {
            filterProceduresByProvider(selectedProvider);
        } else {
            // Reset all procedure dropdowns to show all procedures
            document.querySelectorAll('.procedure-select').forEach(select => {
                populateProcedureDropdown(select.closest('.procedure-item').dataset.procedureIndex);
            });
        }
    });
    
    // Procedure change - filter providers and show/hide fields
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('procedure-select')) {
            const procedureIndex = e.target.closest('.procedure-item').dataset.procedureIndex;
            const selectedProcedure = e.target.value;
            
            if (selectedProcedure) {
                filterProvidersByProcedure(selectedProcedure);
                showHideFields(procedureIndex, selectedProcedure);
            }
        }
    });
    
    // Teeth change - show/hide quadrants
    document.addEventListener('input', function(e) {
        if (e.target.name && e.target.name.includes('[num_teeth]')) {
            const procedureIndex = e.target.closest('.procedure-item').dataset.procedureIndex;
            const numTeeth = parseInt(e.target.value) || 1;
            showHideQuadrants(procedureIndex, numTeeth);
        }
    });
    
    // Remove procedure buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.remove-procedure')) {
            const procedureItem = e.target.closest('.procedure-item');
            removeProcedure(procedureItem);
        }
    });
}

// Populate provider dropdown
function populateProviderDropdown() {
    const providerSelect = document.getElementById('provider');
    providerSelect.innerHTML = '<option value="">Select a provider...</option>';
    
    providers.forEach(provider => {
        const option = document.createElement('option');
        option.value = provider;
        option.textContent = provider;
        providerSelect.appendChild(option);
    });
}

// Populate procedure dropdown for a specific procedure index
async function populateProcedureDropdown(procedureIndex, filteredProcedures = null) {
    const procedureSelect = document.querySelector(`[data-procedure-index="${procedureIndex}"] .procedure-select`);
    if (!procedureSelect) return;
    
    procedureSelect.innerHTML = '<option value="">Select a procedure...</option>';
    
    const proceduresToShow = filteredProcedures || procedures;
    
    proceduresToShow.forEach(procedure => {
        const option = document.createElement('option');
        option.value = procedure;
        option.textContent = procedure;
        procedureSelect.appendChild(option);
    });
}

// Filter procedures by provider
async function filterProceduresByProvider(provider) {
    try {
        const response = await fetch(`/api/procedures/${encodeURIComponent(provider)}`);
        const filteredProcedures = await response.json();
        
        // Update all procedure dropdowns
        document.querySelectorAll('.procedure-select').forEach(select => {
            const procedureIndex = select.closest('.procedure-item').dataset.procedureIndex;
            populateProcedureDropdown(procedureIndex, filteredProcedures);
        });
        
        // Clear any invalid procedure selections
        document.querySelectorAll('.procedure-select').forEach(select => {
            if (select.value && !filteredProcedures.includes(select.value)) {
                select.value = '';
                const procedureIndex = select.closest('.procedure-item').dataset.procedureIndex;
                showHideFields(procedureIndex, '');
            }
        });
        
    } catch (error) {
        console.error('Error filtering procedures:', error);
    }
}

// Filter providers by procedure
async function filterProvidersByProcedure(procedure) {
    try {
        const response = await fetch(`/api/providers/${encodeURIComponent(procedure)}`);
        const filteredProviders = await response.json();
        
        const providerSelect = document.getElementById('provider');
        const currentProvider = providerSelect.value;
        
        // Update provider dropdown
        providerSelect.innerHTML = '<option value="">Select a provider...</option>';
        
        filteredProviders.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider;
            option.textContent = provider;
            providerSelect.appendChild(option);
        });
        
        // Clear provider if it's not valid for this procedure
        if (currentProvider && !filteredProviders.includes(currentProvider)) {
            providerSelect.value = '';
        }
        
    } catch (error) {
        console.error('Error filtering providers:', error);
    }
}

// Show/hide fields based on procedure type
function showHideFields(procedureIndex, procedure) {
    const surfacesDiv = document.getElementById(`surfaces-${procedureIndex}`);
    const canalsDiv = document.getElementById(`canals-${procedureIndex}`);
    
    // Hide both initially
    if (surfacesDiv) surfacesDiv.style.display = 'none';
    if (canalsDiv) canalsDiv.style.display = 'none';
    
    // Show appropriate field based on procedure type
    if (procedure) {
        const procedureLower = procedure.toLowerCase();
        
        if (procedureLower.includes('filling')) {
            if (surfacesDiv) surfacesDiv.style.display = 'block';
        } else if (procedureLower.includes('root canal')) {
            if (canalsDiv) canalsDiv.style.display = 'block';
        }
    }
}

// Show/hide quadrants based on number of teeth
function showHideQuadrants(procedureIndex, numTeeth) {
    const quadrantsDiv = document.getElementById(`quadrants-${procedureIndex}`);
    if (quadrantsDiv) {
        quadrantsDiv.style.display = numTeeth > 1 ? 'block' : 'none';
    }
}

// Populate mitigating factors
function populateMitigatingFactors() {
    const container = document.getElementById('mitigatingFactors');
    container.innerHTML = '';
    
    mitigatingFactors.forEach(factor => {
        const div = document.createElement('div');
        div.className = 'form-check';
        
        div.innerHTML = `
            <input class="form-check-input" type="checkbox" name="mitigating_factors" 
                   value="${factor.name}" id="factor_${factor.name.replace(/\s+/g, '_')}">
            <label class="form-check-label" for="factor_${factor.name.replace(/\s+/g, '_')}">
                ${factor.name}
                ${factor.is_multiplier ? 
                    `<small class="text-muted"> (×${factor.multiplier})</small>` : 
                    `<small class="text-muted"> (+${factor.additional_time} min)</small>`
                }
            </label>
        `;
        
        container.appendChild(div);
    });
}

// Add new procedure
function addProcedure() {
    procedureIndex++;
    
    const container = document.getElementById('proceduresContainer');
    const newProcedure = document.createElement('div');
    newProcedure.className = 'procedure-item border rounded p-3 mb-3';
    newProcedure.setAttribute('data-procedure-index', procedureIndex);
    
    newProcedure.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <h6 class="mb-0">Procedure ${procedureIndex + 1}</h6>
            <button type="button" class="btn btn-sm btn-outline-danger remove-procedure">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        
        <!-- Procedure Selection -->
        <div class="mb-3">
            <label class="form-label">Procedure</label>
            <select class="form-select procedure-select" name="procedures[${procedureIndex}][procedure]" required>
                <option value="">Select a procedure...</option>
            </select>
        </div>

        <!-- Number of Teeth -->
        <div class="mb-3">
            <label class="form-label">Number of Teeth</label>
            <input type="number" class="form-control" name="procedures[${procedureIndex}][num_teeth]" 
                   value="1" min="1" max="32" required>
        </div>

        <!-- Quadrants (only show if more than 1 tooth) -->
        <div class="mb-3" id="quadrants-${procedureIndex}" style="display: none;">
            <label class="form-label">Number of Quadrants</label>
            <input type="number" class="form-control" name="procedures[${procedureIndex}][num_quadrants]" 
                   value="1" min="1" max="4">
        </div>

        <!-- Surfaces (only show for fillings) -->
        <div class="mb-3" id="surfaces-${procedureIndex}" style="display: none;">
            <label class="form-label">Number of Surfaces</label>
            <input type="number" class="form-control" name="procedures[${procedureIndex}][num_surfaces]" 
                   value="1" min="1" max="5">
        </div>

        <!-- Canals (only show for root canals) -->
        <div class="mb-3" id="canals-${procedureIndex}" style="display: none;">
            <label class="form-label">Number of Canals</label>
            <input type="number" class="form-control" name="procedures[${procedureIndex}][num_surfaces]" 
                   value="1" min="1" max="4">
        </div>
    `;
    
    container.appendChild(newProcedure);
    
    // Populate the new procedure dropdown
    const selectedProvider = document.getElementById('provider').value;
    if (selectedProvider) {
        filterProceduresByProvider(selectedProvider);
    } else {
        populateProcedureDropdown(procedureIndex);
    }
    
    // Show remove buttons for all procedures if more than one
    updateRemoveButtons();
}

// Remove procedure
function removeProcedure(procedureItem) {
    procedureItem.remove();
    updateRemoveButtons();
    updateProcedureNumbers();
}

// Update remove buttons visibility
function updateRemoveButtons() {
    const procedureItems = document.querySelectorAll('.procedure-item');
    const removeButtons = document.querySelectorAll('.remove-procedure');
    
    removeButtons.forEach(button => {
        button.style.display = procedureItems.length > 1 ? 'block' : 'none';
    });
}

// Update procedure numbers
function updateProcedureNumbers() {
    const procedureItems = document.querySelectorAll('.procedure-item');
    procedureItems.forEach((item, index) => {
        const title = item.querySelector('h6');
        if (title) {
            title.textContent = `Procedure ${index + 1}`;
        }
    });
}

// Handle form submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const provider = formData.get('provider');
    const mitigatingFactors = formData.getAll('mitigating_factors');
    
    // Collect procedure data
    const proceduresData = [];
    const procedureItems = document.querySelectorAll('.procedure-item');
    
    procedureItems.forEach(item => {
        const procedure = item.querySelector('.procedure-select').value;
        const numTeeth = parseInt(item.querySelector('input[name*="[num_teeth]"]').value) || 1;
        const numSurfaces = parseInt(item.querySelector('input[name*="[num_surfaces]"]').value) || 1;
        const numQuadrants = parseInt(item.querySelector('input[name*="[num_quadrants]"]').value) || 1;
        
        if (procedure) {
            proceduresData.push({
                procedure: procedure,
                num_teeth: numTeeth,
                num_surfaces: numSurfaces,
                num_quadrants: numQuadrants
            });
        }
    });
    
    if (proceduresData.length === 0) {
        displayError('Please select at least one procedure.');
        return;
    }
    
    if (!provider) {
        displayError('Please select a provider.');
        return;
    }
    
    await calculateAppointmentTime(proceduresData, provider, mitigatingFactors);
}

// Calculate appointment time
async function calculateAppointmentTime(proceduresData, provider, mitigatingFactors) {
    try {
        showLoading();
        
        const response = await fetch('/estimate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                provider: provider,
                procedures_data: proceduresData,
                mitigating_factors: mitigatingFactors
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayResults(result);
        } else {
            displayError(result.error || 'Calculation failed');
        }
        
    } catch (error) {
        console.error('Error calculating appointment time:', error);
        displayError('Failed to calculate appointment time. Please try again.');
    }
}

// Display results
function displayResults(result) {
    const resultsDiv = document.getElementById('results');
    
    let html = `
        <div class="alert alert-success">
            <h5><i class="fas fa-check-circle me-2"></i>Calculation Complete</h5>
        </div>
        
        <div class="row mb-4">
            <div class="col-4">
                <div class="text-center">
                    <div class="h3 text-primary">${result.final_times.total_time}</div>
                    <small class="text-muted">Total Time (min)</small>
                </div>
            </div>
            <div class="col-4">
                <div class="text-center">
                    <div class="h4 text-info">${result.final_times.doctor_time}</div>
                    <small class="text-muted">Doctor Time (min)</small>
                </div>
            </div>
            <div class="col-4">
                <div class="text-center">
                    <div class="h4 text-success">${result.final_times.assistant_time}</div>
                    <small class="text-muted">Assistant Time (min)</small>
                </div>
            </div>
        </div>
    `;
    
    // Show procedure breakdown
    if (result.procedures && result.procedures.length > 0) {
        html += '<h6>Procedure Breakdown:</h6>';
        html += '<div class="table-responsive">';
        html += '<table class="table table-sm">';
        html += '<thead><tr><th>Procedure</th><th>Teeth</th><th>Time</th><th>Notes</th></tr></thead>';
        html += '<tbody>';
        
        result.procedures.forEach((proc, index) => {
            const isReduced = proc.is_reduced;
            const notes = isReduced ? '<span class="badge bg-warning">30% reduced</span>' : '';
            
            html += `
                <tr>
                    <td>${proc.procedure}</td>
                    <td>${proc.num_teeth}</td>
                    <td>${proc.individual_times.total_time} min</td>
                    <td>${notes}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
    }
    
    // Show mitigating factors if any
    if (result.mitigating_factors && (result.mitigating_factors.multiplier !== 1 || result.mitigating_factors.additional_time > 0)) {
        html += '<h6 class="mt-3">Applied Factors:</h6>';
        html += '<ul class="list-unstyled">';
        
        if (result.mitigating_factors.multiplier !== 1) {
            html += `<li><i class="fas fa-times me-1"></i>Multiplier: ×${result.mitigating_factors.multiplier}</li>`;
        }
        
        if (result.mitigating_factors.additional_time > 0) {
            html += `<li><i class="fas fa-plus me-1"></i>Additional time: +${result.mitigating_factors.additional_time} min</li>`;
        }
        
        html += '</ul>';
    }
    
    resultsDiv.innerHTML = html;
}

// Display error
function displayError(message) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="alert alert-danger">
            <h5><i class="fas fa-exclamation-triangle me-2"></i>Error</h5>
            <p class="mb-0">${message}</p>
        </div>
    `;
}

// Show loading state
function showLoading() {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p>Calculating appointment time...</p>
        </div>
    `;
}
