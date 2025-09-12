// PreDentify - Appointment Time Estimator JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('estimationForm');
    const resultsDiv = document.getElementById('results');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const providerAlert = document.getElementById('providerAlert');
    const proceduresContainer = document.getElementById('proceduresContainer');
    const addProcedureBtn = document.getElementById('addProcedure');
    
    let procedureCount = 1;

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
                        <input type="number" class="form-control" name="procedures[${procedureCount}][num_teeth]" 
                               value="1" min="1" max="32" placeholder="1">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small">Quadrants</label>
                        <input type="number" class="form-control" name="procedures[${procedureCount}][num_quadrants]" 
                               value="1" min="1" max="4" placeholder="1">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label small">Surfaces/Canals</label>
                        <input type="number" class="form-control" name="procedures[${procedureCount}][num_surfaces]" 
                               value="1" min="1" max="10" placeholder="1">
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

    function addProcedureEventListeners() {
        // Add event listeners to all procedure inputs
        document.querySelectorAll('.procedure-select, .procedure-item input[type="number"]').forEach(input => {
            input.addEventListener('change', scheduleAutoCalculate);
        });
        
        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-procedure').forEach(btn => {
            btn.addEventListener('click', function() {
                this.closest('.procedure-item').remove();
                updateRemoveButtons();
                scheduleAutoCalculate();
            });
        });
    }

    async function calculateAppointmentTime() {
        // Show loading spinner
        showLoading(true);
        hideProviderAlert();

        try {
            // Gather form data
            const formData = new FormData(form);
            const provider = formData.get('provider');
            const mitigatingFactors = formData.getAll('mitigating_factors');
            
            // Collect procedures data
            const procedures = [];
            const procedureItems = document.querySelectorAll('.procedure-item');
            
            procedureItems.forEach((item, index) => {
                const procedure = item.querySelector('.procedure-select').value;
                const numTeeth = parseInt(item.querySelector('input[name*="num_teeth"]').value) || 1;
                const numQuadrants = parseInt(item.querySelector('input[name*="num_quadrants"]').value) || 1;
                const numSurfaces = parseInt(item.querySelector('input[name*="num_surfaces"]').value) || 1;
                
                if (procedure) {
                    procedures.push({
                        procedure: procedure,
                        num_teeth: numTeeth,
                        num_quadrants: numQuadrants,
                        num_surfaces: numSurfaces
                    });
                }
            });

            // Validate required fields
            if (!provider || procedures.length === 0) {
                throw new Error('Please select a provider and at least one procedure.');
            }

            // Prepare request data
            const requestData = {
                provider: provider,
                mitigating_factors: mitigatingFactors,
                procedures: procedures
            };

            // Make API call
            const response = await fetch('/estimate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to calculate appointment time');
            }

            // Display results
            displayResults(data);

        } catch (error) {
            displayError(error.message);
        } finally {
            showLoading(false);
        }
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
            html += `
                <div class="mb-3">
                    <h6 class="text-secondary">Procedure Details:</h6>
            `;
            procedures.forEach((proc, index) => {
                html += `
                    <div class="small text-muted mb-1">
                        ${index + 1}. ${proc.procedure} (${proc.num_teeth} tooth${proc.num_teeth > 1 ? 's' : ''}, 
                        ${proc.num_quadrants} quadrant${proc.num_quadrants > 1 ? 's' : ''}, 
                        ${proc.num_surfaces} surface${proc.num_surfaces > 1 ? 's' : ''}/canal${proc.num_surfaces > 1 ? 's' : ''})
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
                        <strong>Base Times:</strong> 
                        Assistant: ${base_times.assistant_time} min, 
                        Doctor: ${base_times.doctor_time} min, 
                        Total: ${base_times.total_time} min
                    </small>
                </div>
            `;
        }

        // Show applied factors
        if (applied_factors && applied_factors.length > 0) {
            html += `
                <div class="applied-factors mt-3">
                    <h6 class="mb-2">
                        <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                        Applied Factors
                    </h6>
            `;
            
            applied_factors.forEach(factor => {
                const multiplierText = factor.multiplier > 2 
                    ? `+${factor.multiplier} min` 
                    : `${factor.multiplier}x`;
                
                html += `
                    <div class="factor-item">
                        <span>${factor.name}</span>
                        <span class="text-warning fw-bold">${multiplierText}</span>
                    </div>
                `;
            });
            
            html += '</div>';
        }

        html += '</div>';
        
        resultsDiv.innerHTML = html;

        // Show provider warning if applicable
        if (data.warning) {
            showProviderAlert();
        }
    }

    function displayError(message) {
        const html = `
            <div class="fade-in error-state">
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
            proc.teeth_adjustments && (
                proc.teeth_adjustments.assistant_time > 0 || 
                proc.teeth_adjustments.doctor_time > 0 || 
                proc.teeth_adjustments.total_time > 0
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
            if (providerSelect.value && document.querySelector('.procedure-select').value) {
                calculateAppointmentTime();
            }
        }, 500);
    }

    // Function to update procedure options based on selected provider
    function updateProcedureOptions(provider) {
        if (!provider) {
            // If no provider selected, show all procedures
            fetch('/api/procedures')
                .then(response => response.json())
                .then(procedures => {
                    populateProcedureDropdowns(procedures);
                })
                .catch(error => console.error('Error fetching procedures:', error));
        } else {
            // Fetch procedures for the specific provider
            fetch(`/api/procedures/${encodeURIComponent(provider)}`)
                .then(response => response.json())
                .then(procedures => {
                    populateProcedureDropdowns(procedures);
                })
                .catch(error => console.error('Error fetching provider procedures:', error));
        }
    }

    // Function to populate all procedure dropdowns
    function populateProcedureDropdowns(procedures) {
        const procedureSelects = document.querySelectorAll('.procedure-select');
        
        procedureSelects.forEach(select => {
            const currentValue = select.value;
            
            // Clear and repopulate options
            select.innerHTML = '<option value="">Select a procedure...</option>';
            
            procedures.forEach(procedure => {
                const option = document.createElement('option');
                option.value = procedure;
                option.textContent = procedure;
                select.appendChild(option);
            });
            
            // Restore previous selection if it's still available
            if (currentValue && procedures.includes(currentValue)) {
                select.value = currentValue;
            }
        });
    }

    // Add event listeners for auto-calculation and procedure filtering
    providerSelect.addEventListener('change', function() {
        updateProcedureOptions(this.value);
        scheduleAutoCalculate();
    });
    
    // Add event listeners for checkboxes
    document.querySelectorAll('input[name="mitigating_factors"]').forEach(checkbox => {
        checkbox.addEventListener('change', scheduleAutoCalculate);
    });

    // Initialize procedure event listeners
    addProcedureEventListeners();

    // Initialize procedure options (load all procedures initially)
    updateProcedureOptions('');

    // Initialize tooltips (if using Bootstrap tooltips)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
