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
    let isDataLoaded = false;
    let autoCalculateTimeout;
    let isAutoCalculating = false;

    // Procedures that should NOT show detail prompts (teeth, quadrants, surfaces/canals)
    const excludedFromDetailPrompts = [
        'Appliance Adjustment',
        'Bite Adjustment', 
        'Botox',
        'CBCT',
        'Consultation',
        'Crown',
        'Re-cement',
        'Emergency Exam',
        'Happy Visit',
        'Hygiene',
        'Implant Follow-Up',
        'In-Office Whitening',
        'Invisalign Complete',
        'Invisalign Insert',
        'Invisalign Insert 2',
        'Invisalign Recall',
        'Kids Hygiene',
        'Kids Hygiene 0–2',
        'Kids Hygiene 3–7',
        'Kids Hygiene 8–11',
        'Laser Bacterial Reduction',
        'Laser Desensitization',
        'New Patient Exam',
        'Night Guard Insert',
        'Post-op Exam',
        'Re-evaluation',
        'Polish and Fluoride',
        'Recall Exam',
        'SDF Application',
        'Sedation Specific Exam',
        'Surgical Debridement'
    ];

    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        calculateAppointmentTime();
    });

    // Add procedure functionality
    addProcedureBtn.addEventListener('click', async function() {
        await addProcedureRow();
    });

    async function addProcedureRow() {
        try {
            // Fetch procedure 2 items from API
            const response = await fetch('/api/procedures2');
            if (!response.ok) {
                throw new Error(`Failed to load procedure2 items: ${response.status}`);
            }
            const procedure2Items = await response.json();
            
            // Generate options for procedure 2 items
            let procedure2Options = '';
            procedure2Items.forEach(procedure => {
                procedure2Options += `<option value="${procedure}">${procedure}</option>`;
            });
            
            const procedureHtml = `
                <div class="procedure-item border rounded p-3 mb-3">
                    <div class="row align-items-end">
                        <div class="col-md-4">
                            <label class="form-label small">Procedure</label>
                            <select class="form-select procedure-select" name="procedures[${procedureCount}][procedure]" required>
                                <option value="">Select procedure...</option>
                                ${procedure2Options}
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label small">Teeth</label>
                            <input type="number" class="form-control teeth-input" name="procedures[${procedureCount}][num_teeth]" 
                                   value="1" min="1" max="32" placeholder="1">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label small quadrants-label">Quadrants</label>
                            <input type="number" class="form-control quadrants-input" name="procedures[${procedureCount}][num_quadrants]" 
                                   value="1" min="1" max="4" placeholder="1" style="display: none;">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label small surfaces-canals-label">Surfaces/Canals</label>
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
            
            console.log(`🔄 Adding procedure2 row with ${procedure2Items.length} available procedure2 items`);
            
            // Show remove buttons for all procedures if more than one
            updateRemoveButtons();
            
            // Add event listeners to new inputs
            addProcedureEventListeners();
            
            // Update field visibility for new row
            updateFieldVisibility();
            
            // Schedule auto-calculation for new row
            scheduleAutoCalculate();
        } catch (error) {
            console.error('Error loading procedure2 items:', error);
            alert('Error loading additional procedures. Please try again.');
        }
    }
        // Schedule auto-calculation for new row
        scheduleAutoCalculate();
    }

    // FIXED: Always return all available procedures for new rows
    function getProcedureOptions() {
        if (allProcedures.length === 0) {
            console.warn('No procedures loaded yet, returning empty options');
            return '';
        }
        
        let options = '';
        allProcedures.forEach(procedure => {
            options += `<option value="${procedure}">${procedure}</option>`;
        });
        
        console.log(`🔄 Adding new procedure row with ${allProcedures.length} available procedures`);
        return options;
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
        scheduleAutoCalculate(); // Recalculate after removal
    }

    // NEW: Reset form fields to default values
    function resetFormFields() {
        console.log('🔄 Resetting form fields to default values');
        
        document.querySelectorAll('.procedure-item').forEach(item => {
            const teethInput = item.querySelector('.teeth-input');
            const quadrantsInput = item.querySelector('.quadrants-input');
            const surfacesInput = item.querySelector('.surfaces-input');
            
            if (teethInput) teethInput.value = '1';
            if (quadrantsInput) quadrantsInput.value = '1';
            if (surfacesInput) surfacesInput.value = '1';
        });
        
        // Clear results
        resultsDiv.innerHTML = '';
        
        console.log('✅ Form fields reset to default values');
    }

    function addProcedureEventListeners() {
        // Remove procedure buttons
        document.querySelectorAll('.remove-procedure').forEach(btn => {
            btn.addEventListener('click', function() {
                removeProcedureRow(this);
            });
        });

        // Teeth input changes - with auto-calculation
        document.querySelectorAll('.teeth-input').forEach(input => {
            input.addEventListener('input', function() {
                updateFieldVisibility();
                scheduleAutoCalculate();
            });
        });

        // Quadrants input changes - with auto-calculation
        document.querySelectorAll('.quadrants-input').forEach(input => {
            input.addEventListener('input', function() {
                scheduleAutoCalculate();
            });
        });

        // Surfaces input changes - with auto-calculation
        document.querySelectorAll('.surfaces-input').forEach(input => {
            input.addEventListener('input', function() {
                scheduleAutoCalculate();
            });
        });

        // Procedure selection changes - with auto-calculation, provider filtering, and field reset
        document.querySelectorAll('.procedure-select').forEach(select => {
            select.addEventListener('change', function() {
                console.log('🔄 Procedure changed to:', this.value);
                updateFieldVisibility();
                // FIXED: Pass the selected procedure value to updateProviderOptions
                updateProviderOptions(this.value);
                // NEW: Reset form fields when procedure changes
                resetFormFields();
                scheduleAutoCalculate();
            });
        });
    }

    // Enhanced auto-calculation with better feedback and debouncing
    function scheduleAutoCalculate() {
        if (!isDataLoaded) {
            console.log('Data not loaded yet, skipping auto-calculation');
            return;
        }

        // Clear existing timeout
        clearTimeout(autoCalculateTimeout);
        
        // Show auto-calculation indicator
        showAutoCalculationIndicator();
        
        // Set new timeout with debouncing
        autoCalculateTimeout = setTimeout(() => {
            if (isFormValidForAutoCalculation()) {
                console.log('🔄 Auto-calculating appointment time...');
                isAutoCalculating = true;
                calculateAppointmentTime(true); // true indicates this is an auto-calculation
            } else {
                hideAutoCalculationIndicator();
            }
        }, 800); // Increased debounce time for better UX
    }

    function isFormValidForAutoCalculation() {
        const provider = document.getElementById('provider');
        const procedureSelects = document.querySelectorAll('.procedure-select');
        
        if (!provider || !provider.value) {
            return false;
        }
        
        // Check if at least one procedure is selected
        for (let select of procedureSelects) {
            if (select.value) {
                return true;
            }
        }
        
        return false;
    }

    function showAutoCalculationIndicator() {
        // Add a subtle indicator that auto-calculation is pending
        const indicator = document.getElementById('autoCalcIndicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
    }

    function hideAutoCalculationIndicator() {
        const indicator = document.getElementById('autoCalcIndicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    // Enhanced field visibility with proper Quadrants, Surfaces & Canals logic
    function updateFieldVisibility() {
        document.querySelectorAll('.procedure-item').forEach(item => {
            const procedureSelect = item.querySelector('.procedure-select');
            const teethInput = item.querySelector('.teeth-input');
            const quadrantsInput = item.querySelector('.quadrants-input');
            const quadrantsLabel = item.querySelector('.quadrants-label');
            const surfacesInput = item.querySelector('.surfaces-input');
            const surfacesCanalsLabel = item.querySelector('.surfaces-canals-label');
            
            // Check if elements exist before accessing their properties
            if (!procedureSelect || !teethInput || !quadrantsInput || !surfacesInput) {
                return; // Skip this item if elements don't exist
            }
            
            const procedure = procedureSelect.value;
            const teeth = parseInt(teethInput.value) || 1;
            
            // Check if procedure is in exclusion list
            const isExcluded = excludedFromDetailPrompts.includes(procedure);
            
            if (isExcluded) {
                // Hide all detail fields for excluded procedures
                teethInput.style.display = 'none';
                quadrantsInput.style.display = 'none';
                surfacesInput.style.display = 'none';
                if (quadrantsLabel) quadrantsLabel.style.display = 'none';
                if (surfacesCanalsLabel) surfacesCanalsLabel.style.display = 'none';
                
                // Hide the teeth label as well
                const teethLabel = item.querySelector('label[for*="num_teeth"]');
                if (teethLabel) {
                    teethLabel.style.display = 'none';
                }
                
                console.log(`Procedure "${procedure}" is excluded from detail prompts - hiding all detail fields`);
                return;
            } else {
                // Show teeth field for non-excluded procedures
                teethInput.style.display = 'block';
                const teethLabel = item.querySelector('label[for*="num_teeth"]');
                if (teethLabel) {
                    teethLabel.style.display = 'block';
                }
            }
            
            // Reset field visibility
            quadrantsInput.style.display = 'none';
            surfacesInput.style.display = 'none';
            if (quadrantsLabel) quadrantsLabel.style.display = 'none';
            if (surfacesCanalsLabel) surfacesCanalsLabel.style.display = 'none';
            
            // FIXED: Show quadrants only if more than one tooth
            if (teeth > 1) {
                quadrantsInput.style.display = 'block';
                if (quadrantsLabel) quadrantsLabel.style.display = 'block';
                console.log(`Teeth: ${teeth} - showing Quadrants field`);
            } else {
                console.log(`Teeth: ${teeth} - hiding Quadrants field (only show for >1 tooth)`);
            }
            
            // FIXED: Show Surfaces only for Filling procedures
            if (procedure === 'Filling') {
                surfacesInput.style.display = 'block';
                if (surfacesCanalsLabel) {
                    surfacesCanalsLabel.style.display = 'block';
                    surfacesCanalsLabel.textContent = 'Surfaces';
                }
                console.log(`Procedure "${procedure}" - showing Surfaces field`);
            }
            
            // FIXED: Show Canals only for Root Canal procedures
            if (procedure === 'Root Canal') {
                surfacesInput.style.display = 'block';
                if (surfacesCanalsLabel) {
                    surfacesCanalsLabel.style.display = 'block';
                    surfacesCanalsLabel.textContent = 'Canals';
                }
                console.log(`Procedure "${procedure}" - showing Canals field`);
            }
            
            // Hide both for everything else (already handled by reset above)
        });
    }

    // Enhanced procedure loading with better error handling
    function loadProceduresForProvider(provider) {
        if (!provider) {
            populateProcedureDropdowns(allProcedures);
            return Promise.resolve();
        }

        return fetch('/api/procedures/' + encodeURIComponent(provider))
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(procedures => {
                // FIXED: Only filter existing procedure dropdowns, not new ones
                populateProcedureDropdowns(procedures);
                return procedures;
            })
            .catch(error => {
                console.error('Error fetching provider procedures:', error);
                // Fallback to all procedures if provider-specific fetch fails
                populateProcedureDropdowns(allProcedures);
                displayError('Failed to load procedures for provider. Showing all procedures.');
                return allProcedures;
            });
    }

    // Enhanced provider loading with better error handling
    function loadProvidersForProcedure(procedure) {
        if (!procedure) {
            populateProviderDropdown(allProviders);
            return Promise.resolve();
        }

        return fetch('/api/providers/' + encodeURIComponent(procedure))
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(providers => {
                populateProviderDropdown(providers);
                return providers;
            })
            .catch(error => {
                console.error('Error fetching procedure providers:', error);
                // Fallback to all providers if procedure-specific fetch fails
                populateProviderDropdown(allProviders);
                displayError('Failed to load providers for procedure. Showing all providers.');
                return allProviders;
            });
    }

    // Bidirectional filtering functions
    function updateProcedureOptions(provider) {
        if (!isDataLoaded) {
            console.warn('Data not loaded yet, skipping procedure update');
            return;
        }
        console.log('🔄 Updating procedure options for provider:', provider);
        loadProceduresForProvider(provider);
    }

    function updateProviderOptions(procedure) {
        if (!isDataLoaded) {
            console.warn('Data not loaded yet, skipping procedure update');
            return;
        }
        console.log('🔄 Updating provider options for procedure:', procedure);
        loadProvidersForProcedure(procedure);
    }

    // FIXED: Enhanced procedure dropdown population with better logic
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
        
        console.log(`🔄 Updated ${procedureSelects.length} procedure dropdowns with ${procedures.length} procedures`);
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

    function calculateAppointmentTime(isAutoCalculation = false) {
        console.log('=== DEBUG: Starting calculateAppointmentTime ===', { isAutoCalculation });
        
        const provider = document.getElementById('provider');
        if (!provider) {
            console.error('Provider element not found');
            displayError('Provider selection not found.');
            return;
        }
        
        const providerValue = provider.value;
        console.log('Provider value:', providerValue);
        
        const procedures = [];
        
        // Collect all procedure data with null checks
        const procedureItems = document.querySelectorAll('.procedure-item');
        console.log('Found procedure items:', procedureItems.length);
        
        procedureItems.forEach((item, index) => {
            const procedureSelect = item.querySelector('.procedure-select');
            const teethInput = item.querySelector('.teeth-input');
            const quadrantsInput = item.querySelector('.quadrants-input');
            const surfacesInput = item.querySelector('.surfaces-input');
            
            console.log(`Procedure item ${index}:`, {
                procedureSelect: !!procedureSelect,
                teethInput: !!teethInput,
                quadrantsInput: !!quadrantsInput,
                surfacesInput: !!surfacesInput
            });
            
            // Check if all required elements exist
            if (!procedureSelect || !teethInput || !quadrantsInput || !surfacesInput) {
                console.warn('Missing form elements in procedure item', index);
                return; // Skip this item
            }
            
            const procedure = procedureSelect.value;
            const isExcluded = excludedFromDetailPrompts.includes(procedure);
            
            if (isExcluded) {
                // For excluded procedures, use default values
                procedures.push({
                    procedure: procedure,
                    num_teeth: 1,
                    num_quadrants: 1,
                    num_surfaces: 1
                });
                console.log(`Procedure "${procedure}" is excluded - using default values`);
            } else {
                // For regular procedures, collect actual values
                const numTeeth = parseInt(teethInput.value) || 1;
                const numQuadrants = parseInt(quadrantsInput.value) || 1;
                const numSurfaces = parseInt(surfacesInput.value) || 1;
                
                console.log(`Procedure ${index} data:`, {
                    procedure: procedure,
                    numTeeth: numTeeth,
                    numQuadrants: numQuadrants,
                    numSurfaces: numSurfaces
                });
                
                procedures.push({
                    procedure: procedure,
                    num_teeth: numTeeth,
                    num_quadrants: numQuadrants,
                    num_surfaces: numSurfaces
                });
            }
        });
        
        if (procedures.length === 0) {
            displayError('Please select at least one procedure.');
            return;
        }
        
        if (!providerValue) {
            displayError('Please select a provider.');
            return;
        }
        
        // Show loading state
        showLoading(true);
        
        // Make API request
        fetch('/estimate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                provider: providerValue,
                procedures: procedures,
                mitigating_factors: getSelectedMitigatingFactors()
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                displayResults(data);
            } else {
                displayError(data.error || 'Unknown error occurred');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            displayError('Failed to calculate appointment time. Please try again.');
        })
        .finally(() => {
            showLoading(false);
            isAutoCalculating = false;
            hideAutoCalculationIndicator();
        });
    }

    function getSelectedMitigatingFactors() {
        const checkboxes = document.querySelectorAll('input[name="mitigating_factors"]:checked');
        return Array.from(checkboxes).map(checkbox => checkbox.value);
    }

    function displayResults(data) {
        const { procedures, provider, base_times, final_times, applied_factors } = data;
        
        let html = `
            <div class="fade-in">
                <div class="text-center text-success mb-3">
                    <i class="fas fa-check-circle fa-3x"></i>
                    <h5 class="mt-2">Estimated Time</h5>
                </div>
                <div class="row">
                    <div class="col-md-4 text-center">
                        <div class="border rounded p-3">
                            <h6 class="text-muted">Assistant Time</h6>
                            <h4 class="text-primary">${final_times.assistant_time} min</h4>
                        </div>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="border rounded p-3">
                            <h6 class="text-muted">Doctor Time</h6>
                            <h4 class="text-info">${final_times.doctor_time} min</h4>
                        </div>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="border rounded p-3 bg-primary text-white">
                            <h6 class="opacity-75">Total Time</h6>
                            <h3>${final_times.total_time} min</h3>
                        </div>
                    </div>
                </div>
                <div class="mt-3 text-center">
                    <small class="text-muted">
                        <i class="fas fa-user-md me-1"></i>
                        ${procedures.length} Procedure${procedures.length > 1 ? 's' : ''} - ${provider}
                    </small>
                </div>
        `;
        
        // Show procedure details
        if (procedures && procedures.length > 0) {
            html += '<div class="mt-3"><small class="text-muted">Details: ';
            const details = procedures.map(proc => {
                const parts = [];
                if (proc.num_teeth > 1) parts.push(`${proc.num_teeth} tooths`);
                if (proc.num_quadrants > 1) parts.push(`${proc.num_quadrants} quadrant`);
                if (proc.num_surfaces > 1) parts.push(`${proc.num_surfaces} surface/canal`);
                return parts.length > 0 ? parts.join(', ') : '1 tooth, 1 quadrant, 1 surface/canal';
            });
            html += details.join('; ') + '</small></div>';
        }

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

    // Enhanced auto-calculation event listeners
    const providerSelect = document.getElementById('provider');
    
    // Add event listeners for auto-calculation, bidirectional filtering, and field reset
    if (providerSelect) {
        providerSelect.addEventListener('change', function() {
            console.log('🔄 Provider changed to:', this.value);
            updateProcedureOptions(this.value);
            // NEW: Reset form fields when provider changes
            resetFormFields();
            scheduleAutoCalculate();
        });
    }

    // Add event listeners for checkboxes
    document.querySelectorAll('input[name="mitigating_factors"]').forEach(checkbox => {
        checkbox.addEventListener('change', scheduleAutoCalculate);
    });

    // Initialize procedure event listeners
    addProcedureEventListeners();

    // Enhanced initial data loading with better error handling and loading states
    function initializeApplication() {
        console.log('Initializing application...');
        
        // Show loading state
        showLoading(true);
        
        Promise.all([
            fetch('/api/procedures').then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to load procedures: ${response.status}`);
                }
                return response.json();
            }),
            fetch('/api/providers').then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to load providers: ${response.status}`);
                }
                return response.json();
            })
        ])
        .then(([procedures, providers]) => {
            console.log('Data loaded successfully:', {
                procedures: procedures.length,
                providers: providers.length
            });
            
            allProcedures = procedures;
            allProviders = providers;
            isDataLoaded = true;
            
            // Initialize procedure options (load all procedures initially)
            updateProcedureOptions('');
            
            // Initialize field visibility only if we have procedure items
            if (document.querySelectorAll('.procedure-item').length > 0) {
                updateFieldVisibility();
            }
            
            // Hide loading state
            showLoading(false);
            
            console.log('Application initialized successfully');
        })
        .catch(error => {
            console.error('Error loading initial data:', error);
            showLoading(false);
            displayError('Failed to load application data. Please refresh the page.');
        });
    }

    // Start the application initialization
    initializeApplication();

    // Initialize tooltips (if using Bootstrap tooltips)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
