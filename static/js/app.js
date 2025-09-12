// PreDentify - Appointment Time Estimator JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('estimationForm');
    const resultsDiv = document.getElementById('results');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const providerAlert = document.getElementById('providerAlert');
    const proceduresContainer = document.getElementById('proceduresContainer');
    const addProcedureBtn = document.getElementById('addProcedure');
    
    let procedureCount = 1;
    let allProcedures = [];
    let allProviders = [];

    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        calculateAppointmentTime();
    });

    // Add procedure functionality
    addProcedureBtn.addEventListener('click', function() {
        addProcedureRow();
    });

    function addProcedureRow() {
        const procedureHtml = `
            <div class="procedure-item border rounded p-3 mb-3">
                <div class="row align-items-end">
                    <div class="col-md-4">
                        <label class="form-label small">Procedure</label>
                        <select class="form-select procedure-select" name="procedures[${procedureCount}][procedure]" required>
                            <option value="">Select procedure...</option>
                            ${getProcedureOptions()}
                        </select>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small">Teeth</label>
                        <input type="number" class="form-control teeth-input" name="procedures[${procedureCount}][num_teeth]" 
                               value="1" min="1" max="32" placeholder="1">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small">Quadrants</label>
                        <input type="number" class="form-control quadrants-input" name="procedures[${procedureCount}][num_quadrants]" 
                               value="1" min="1" max="4" placeholder="1" style="display: none;">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small surfaces-label" style="display: none;">Surfaces</label>
                        <label class="form-label small canals-label" style="display: none;">Canals</label>
                        <input type="number" class="form-control surfaces-input" name="procedures[${procedureCount}][num_surfaces]" 
                               value="1" min="1" max="10" placeholder="1" style="display: none;">
                    </div>
                    <div class="col-md-2">
                        <button type="button" class="btn btn-outline-danger btn-sm remove-procedure">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        proceduresContainer.insertAdjacentHTML('beforeend', procedureHtml);
        procedureCount++;
        
        // Show remove buttons for all procedures if more than one
        updateRemoveButtons();
        
        // Add event listeners to new inputs
        addProcedureEventListeners();
        
        // Update field visibility for new row
        updateFieldVisibility();
    }

    function getProcedureOptions() {
        const firstSelect = document.querySelector('.procedure-select');
        if (firstSelect) {
            return firstSelect.innerHTML;
        }
        return '';
    }

    function updateRemoveButtons() {
        const procedureItems = document.querySelectorAll('.procedure-item');
        const removeButtons = document.querySelectorAll('.remove-procedure');
        
        removeButtons.forEach((btn, index) => {
            btn.style.display = procedureItems.length > 1 ? 'block' : 'none';
        });
    }

    // Remove procedure functionality
    function removeProcedureRow(button) {
        button.closest('.procedure-item').remove();
        updateRemoveButtons();
        updateFieldVisibility();
    }

    function addProcedureEventListeners() {
        // Remove procedure buttons
        document.querySelectorAll('.remove-procedure').forEach(btn => {
            btn.addEventListener('click', function() {
                removeProcedureRow(this);
            });
        });

        // Teeth input changes
        document.querySelectorAll('.teeth-input').forEach(input => {
            input.addEventListener('input', function() {
                updateFieldVisibility();
            });
        });

        // Procedure selection changes
        document.querySelectorAll('.procedure-select').forEach(select => {
            select.addEventListener('change', function() {
                updateFieldVisibility();
                updateProviderOptions();
            });
        });
    }

    // Update field visibility based on procedure type and teeth count
    function updateFieldVisibility() {
        document.querySelectorAll('.procedure-item').forEach(item => {
            const procedureSelect = item.querySelector('.procedure-select');
            const teethInput = item.querySelector('.teeth-input');
            const quadrantsInput = item.querySelector('.quadrants-input');
            const surfacesInput = item.querySelector('.surfaces-input');
            const surfacesLabel = item.querySelector('.surfaces-label');
            const canalsLabel = item.querySelector('.canals-label');
            
            // Check if elements exist before accessing their properties
            if (!procedureSelect || !teethInput || !quadrantsInput || !surfacesInput) {
                return; // Skip this item if elements don't exist
            }
            
            const procedure = procedureSelect.value;
            const teeth = parseInt(teethInput.value) || 1;
            
            // Reset all field visibility
            quadrantsInput.style.display = 'none';
            surfacesInput.style.display = 'none';
            if (surfacesLabel) surfacesLabel.style.display = 'none';
            if (canalsLabel) canalsLabel.style.display = 'none';
            
            // Show quadrants only if more than one tooth
            if (teeth > 1) {
                quadrantsInput.style.display = 'block';
            }
            
            // Show surfaces only for fillings
            if (procedure === 'Filling') {
                surfacesInput.style.display = 'block';
                if (surfacesLabel) surfacesLabel.style.display = 'block';
            }
            
            // Show canals only for root canals
            if (procedure === 'Root Canal') {
                surfacesInput.style.display = 'block';
                if (canalsLabel) canalsLabel.style.display = 'block';
            }
        });
    }

    // Bidirectional filtering functions
    function updateProcedureOptions(provider) {
        if (!provider) {
            // If no provider selected, show all procedures
            populateProcedureDropdowns(allProcedures);
        } else {
            // Fetch procedures for the specific provider
            fetch('/api/procedures/' + encodeURIComponent(provider))
                .then(response => response.json())
                .then(procedures => {
                    populateProcedureDropdowns(procedures);
                })
                .catch(error => console.error('Error fetching provider procedures:', error));
        }
    }

    function updateProviderOptions(procedure) {
        if (!procedure) {
            // If no procedure selected, show all providers
            populateProviderDropdown(allProviders);
        } else {
            // Fetch providers for the specific procedure
            fetch('/api/providers/' + encodeURIComponent(procedure))
                .then(response => response.json())
                .then(providers => {
                    populateProviderDropdown(providers);
                })
                .catch(error => console.error('Error fetching procedure providers:', error));
        }
    }

    function populateProcedureDropdowns(procedures) {
        const procedureSelects = document.querySelectorAll('.procedure-select');
        
        procedureSelects.forEach(select => {
            const currentValue = select.value;
            
            // Clear and repopulate options
            select.innerHTML = '<option value="">Select procedure...</option>';
            
            procedures.forEach(procedure => {
                const option = document.createElement('option');
                option.value = procedure;
                option.textContent = procedure;
                select.appendChild(option);
            });
            
            // Restore previous selection if it's still available
            if (currentValue && procedures.includes(currentValue)) {
                select.value = currentValue;
            } else if (currentValue && !procedures.includes(currentValue)) {
                // Clear invalid selection
                select.value = '';
                updateProviderOptions(''); // Reset provider options
            }
        });
        
        // Only update field visibility if we have procedure items
        if (document.querySelectorAll('.procedure-item').length > 0) {
            updateFieldVisibility();
        }
    }

    function populateProviderDropdown(providers) {
        const providerSelect = document.getElementById('provider');
        if (!providerSelect) return; // Exit if provider select doesn't exist
        
        const currentValue = providerSelect.value;
        
        // Clear and repopulate options
        providerSelect.innerHTML = '<option value="">Select provider...</option>';
        
        providers.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider;
            option.textContent = provider;
            providerSelect.appendChild(option);
        });
        
        // Restore previous selection if it's still available
        if (currentValue && providers.includes(currentValue)) {
            providerSelect.value = currentValue;
        } else if (currentValue && !providers.includes(currentValue)) {
            // Clear invalid selection
            providerSelect.value = '';
            updateProcedureOptions(''); // Reset procedure options
        }
    }

    function calculateAppointmentTime() {
        const provider = document.getElementById('provider');
        if (!provider) {
            displayError('Provider selection not found.');
            return;
        }
        
        const providerValue = provider.value;
        const procedures = [];
        
        // Collect all procedure data with null checks
        document.querySelectorAll('.procedure-item').forEach((item, index) => {
            const procedureSelect = item.querySelector('.procedure-select');
            const teethInput = item.querySelector('.teeth-input');
            const quadrantsInput = item.querySelector('.quadrants-input');
            const surfacesInput = item.querySelector('.surfaces-input');
            
            // Check if all required elements exist
            if (!procedureSelect || !teethInput || !quadrantsInput || !surfacesInput) {
                console.warn('Missing form elements in procedure item', index);
                return; // Skip this item
            }
            
            const procedure = procedureSelect.value;
            const numTeeth = parseInt(teethInput.value) || 1;
            const numQuadrants = parseInt(quadrantsInput.value) || 1;
            const numSurfaces = parseInt(surfacesInput.value) || 1;
            
            if (procedure) {
                procedures.push({
                    procedure: procedure,
                    num_teeth: numTeeth,
                    num_quadrants: numQuadrants,
                    num_surfaces: numSurfaces
                });
            }
        });
        
        // Collect mitigating factors
        const mitigatingFactors = [];
        document.querySelectorAll('input[name="mitigating_factors"]:checked').forEach(checkbox => {
            mitigatingFactors.push(checkbox.value);
        });
        
        if (!providerValue || procedures.length === 0) {
            displayError('Please select a provider and at least one procedure.');
            return;
        }
        
        showLoading(true);
        
        fetch('/estimate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                provider: providerValue,
                procedures: procedures,
                mitigating_factors: mitigatingFactors
            })
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            displayResults(data);
        })
        .catch(error => {
            showLoading(false);
            displayError('Error calculating appointment time: ' + error.message);
        });
    }

    function displayResults(data) {
        if (!data.success) {
            if (data.warning) {
                showProviderAlert();
            }
            displayError(data.error);
            return;
        }

        const { procedures, provider, base_times, final_times, applied_factors } = data;

        let html = `
            <div class="fade-in">
                <h6 class="text-primary mb-3">
                    <i class="fas fa-check-circle me-2"></i>
                    ${procedures.length} Procedure${procedures.length > 1 ? 's' : ''} - ${provider}
                </h6>
        `;

        // Show procedure details
        if (procedures.length > 1) {
            html += '<div class="mb-3">';
            procedures.forEach((proc, index) => {
                const isFirst = index === 0;
                const adjustment = isFirst ? '' : ' (30% reduction applied)';
                html += `
                    <div class="mb-2">
                        <small class="text-muted">
                            <strong>${proc.procedure}${adjustment}:</strong> ${proc.num_teeth} tooth${proc.num_teeth > 1 ? 's' : ''}, 
                            ${proc.num_quadrants} quadrant${proc.num_quadrants > 1 ? 's' : ''}, 
                            ${proc.num_surfaces} surface${proc.num_surfaces > 1 ? 's' : ''}/canal${proc.num_surfaces > 1 ? 's' : ''}
                        </small>
                    </div>
                `;
            });
            html += '</div>';
        } else {
            const proc = procedures[0];
            html += `
                <div class="mb-2">
                    <small class="text-muted">
                        <strong>Details:</strong> ${proc.num_teeth} tooth${proc.num_teeth > 1 ? 's' : ''}, 
                        ${proc.num_quadrants} quadrant${proc.num_quadrants > 1 ? 's' : ''}, 
                        ${proc.num_surfaces} surface${proc.num_surfaces > 1 ? 's' : ''}/canal${proc.num_surfaces > 1 ? 's' : ''}
                    </small>
                </div>
            `;
        }
        
        html += `
                <div class="time-breakdown success-state">
                    <div class="time-item">
                        <div class="time-label">
                            <i class="fas fa-user-nurse text-info"></i>
                            Assistant Time
                        </div>
                        <div class="time-value">${final_times.assistant_time} min</div>
                    </div>
                    
                    <div class="time-item">
                        <div class="time-label">
                            <i class="fas fa-user-md text-success"></i>
                            Doctor Time
                        </div>
                        <div class="time-value">${final_times.doctor_time} min</div>
                    </div>
                    
                    <div class="time-item">
                        <div class="time-label">
                            <i class="fas fa-clock text-primary"></i>
                            Total Time
                        </div>
                        <div class="time-value">${final_times.total_time} min</div>
                    </div>
                </div>
        `;

        // Show base times if different from final times
        if (hasAppliedFactors(base_times, final_times) || hasTeethAdjustments(procedures)) {
            html += `
                <div class="mt-3">
                    <small class="text-muted">
                        <strong>Base Times:</strong> Assistant: ${base_times.assistant_time} min, 
                        Doctor: ${base_times.doctor_time} min, Total: ${base_times.total_time} min
                    </small>
                </div>
            `;
        }

        // Show applied factors
        if (applied_factors && applied_factors.length > 0) {
            html += `
                <div class="mt-3">
                    <small class="text-success">
                        <i class="fas fa-info-circle me-1"></i>
                        Applied: ${applied_factors.map(f => f.name).join(', ')}
                    </small>
                </div>
            `;
        }

        html += '</div>';
        resultsDiv.innerHTML = html;
    }

    function displayError(message) {
        const html = `
            <div class="fade-in">
                <div class="text-center text-danger">
                    <i class="fas fa-exclamation-circle fa-3x mb-3"></i>
                    <h6>Error</h6>
                    <p>${message}</p>
                </div>
            </div>
        `;
        resultsDiv.innerHTML = html;
    }

    function hasAppliedFactors(baseTimes, finalTimes) {
        return baseTimes.assistant_time !== finalTimes.assistant_time ||
               baseTimes.doctor_time !== finalTimes.doctor_time ||
               baseTimes.total_time !== finalTimes.total_time;
    }

    function hasTeethAdjustments(procedures) {
        return procedures.some(proc => 
            proc.adjusted_times && (
                proc.adjusted_times.assistant_time > 0 || 
                proc.adjusted_times.doctor_time > 0 || 
                proc.adjusted_times.total_time > 0
            )
        );
    }

    function showLoading(show) {
        loadingSpinner.style.display = show ? 'block' : 'none';
    }

    function showProviderAlert() {
        providerAlert.style.display = 'block';
    }

    function hideProviderAlert() {
        providerAlert.style.display = 'none';
    }

    // Auto-calculate when form changes
    const providerSelect = document.getElementById('provider');
    
    let autoCalculateTimeout;
    
    function scheduleAutoCalculate() {
        clearTimeout(autoCalculateTimeout);
        autoCalculateTimeout = setTimeout(() => {
            if (providerSelect && providerSelect.value && document.querySelector('.procedure-select') && document.querySelector('.procedure-select').value) {
                calculateAppointmentTime();
            }
        }, 500);
    }

    // Add event listeners for auto-calculation and bidirectional filtering
    if (providerSelect) {
        providerSelect.addEventListener('change', function() {
            updateProcedureOptions(this.value);
            scheduleAutoCalculate();
        });
    }

    // Add event listeners for checkboxes
    document.querySelectorAll('input[name="mitigating_factors"]').forEach(checkbox => {
        checkbox.addEventListener('change', scheduleAutoCalculate);
    });

    // Initialize procedure event listeners
    addProcedureEventListeners();

    // Load initial data
    Promise.all([
        fetch('/api/procedures').then(r => r.json()),
        fetch('/api/providers').then(r => r.json())
    ]).then(([procedures, providers]) => {
        allProcedures = procedures;
        allProviders = providers;
        
        // Initialize procedure options (load all procedures initially)
        updateProcedureOptions('');
        
        // Initialize field visibility only if we have procedure items
        if (document.querySelectorAll('.procedure-item').length > 0) {
            updateFieldVisibility();
        }
    }).catch(error => {
        console.error('Error loading initial data:', error);
    });

    // Initialize tooltips (if using Bootstrap tooltips)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
