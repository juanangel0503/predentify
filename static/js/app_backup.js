// PreDentify - Appointment Time Estimator JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('estimationForm');
    const resultsDiv = document.getElementById('results');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const providerAlert = document.getElementById('providerAlert');

    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        calculateAppointmentTime();
    });

    async function calculateAppointmentTime() {
        // Show loading spinner
        showLoading(true);
        hideProviderAlert();

        try {
            // Gather form data
            const formData = new FormData(form);
            const procedure = formData.get('procedure');
            const provider = formData.get('provider');
            const mitigatingFactors = formData.getAll('mitigating_factors');

            // Validate required fields
            if (!procedure || !provider) {
                throw new Error('Please select both a procedure and provider.');
            }

            // Prepare request data
            const requestData = {
                procedure: procedure,
                provider: provider,
                mitigating_factors: mitigatingFactors
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

        const { procedure, provider, base_times, final_times, applied_factors } = data;

        let html = `
            <div class="fade-in">
                <h6 class="text-primary mb-3">
                    <i class="fas fa-check-circle me-2"></i>
                    ${procedure} - ${provider}
                </h6>
                
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
        if (hasAppliedFactors(base_times, final_times)) {
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
                <div class="applied-factors">
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

    function showLoading(show) {
        loadingSpinner.style.display = show ? 'block' : 'none';
    }

    function showProviderAlert() {
        providerAlert.style.display = 'block';
    }

    function hideProviderAlert() {
        providerAlert.style.display = 'none';
    }

    // Auto-calculate when form changes (optional feature)
    const procedureSelect = document.getElementById('procedure');
    const providerSelect = document.getElementById('provider');
    
    let autoCalculateTimeout;
    
    function scheduleAutoCalculate() {
        clearTimeout(autoCalculateTimeout);
        autoCalculateTimeout = setTimeout(() => {
            if (procedureSelect.value && providerSelect.value) {
                calculateAppointmentTime();
            }
        }, 500);
    }

    // Add event listeners for auto-calculation
    procedureSelect.addEventListener('change', scheduleAutoCalculate);
    providerSelect.addEventListener('change', scheduleAutoCalculate);
    
    // Add event listeners for checkboxes
    document.querySelectorAll('input[name="mitigating_factors"]').forEach(checkbox => {
        checkbox.addEventListener('change', scheduleAutoCalculate);
    });

    // Initialize tooltips (if using Bootstrap tooltips)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 