// Pre-Authorization Generator JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('preAuthForm');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const extractedInfoCard = document.getElementById('extractedInfoCard');
    const resultsCard = document.getElementById('resultsCard');
    const policyFlagsAlert = document.getElementById('policyFlagsAlert');
    
    let currentCaseRecordId = null;
    let currentResult = null;

    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        generatePreAuth();
    });

    // Handle copy narrative button
    document.getElementById('copyNarrativeBtn').addEventListener('click', function() {
        copyNarrative();
    });

    // Handle edit info button
    document.getElementById('editInfoBtn').addEventListener('click', function() {
        showEditModal();
    });

    // Handle regenerate button
    document.getElementById('regenerateBtn').addEventListener('click', function() {
        regeneratePreAuth();
    });

    // Handle save edits button
    document.getElementById('saveEditsBtn').addEventListener('click', function() {
        saveEdits();
    });

    async function generatePreAuth() {
        showLoading(true);
        hideResults();

        try {
            const formData = new FormData(form);
            const data = {
                clinical_text: formData.get('clinical_text'),
                procedure_type: formData.get('procedure_type'),
                insurer_type: formData.get('insurer_type')
            };

            const response = await fetch('/preauth/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to generate pre-authorization');
            }

            currentResult = result;
            currentCaseRecordId = result.case_record_id;

            displayResults(result);

        } catch (error) {
            showError(error.message);
        } finally {
            showLoading(false);
        }
    }

    async function regeneratePreAuth() {
        showLoading(true);

        try {
            const edits = getCurrentEdits();

            const response = await fetch('/preauth/regenerate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    case_record_id: currentCaseRecordId,
                    edits: edits
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Failed to regenerate pre-authorization');
            }

            currentResult = result;
            displayResults(result);

        } catch (error) {
            showError(error.message);
        } finally {
            showLoading(false);
        }
    }

    function displayResults(result) {
        // Display extracted information (simplified for demo)
        displayExtractedInfo(result);
        
        // Display narrative
        displayNarrative(result.narrative);
        
        // Display checklist
        displayChecklist(result.checklist);
        
        // Display missing info prompts
        displayMissingInfoPrompts(result.missing_info_prompts);
        
        // Display policy flags
        displayPolicyFlags(result.policy_flags);
        
        // Display validation status
        displayValidationStatus(result.validation);
        
        // Show results cards
        showResults();
    }

    function displayExtractedInfo(result) {
        const extractedInfo = document.getElementById('extractedInfo');
        
        let html = '<div class="fade-in">';
        
        // Show validation status
        if (result.validation) {
            if (result.validation.is_valid) {
                html += '<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>All required information extracted successfully</div>';
            } else {
                html += '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle me-2"></i>Some required information is missing</div>';
            }
        }
        
        // Show basic extracted info (simplified)
        html += '<div class="extracted-info-item">';
        html += '<div class="info-label">Procedure Type</div>';
        html += '<div class="info-value">' + document.getElementById('procedureType').value.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) + '</div>';
        html += '</div>';
        
        html += '<div class="extracted-info-item">';
        html += '<div class="info-label">Insurer</div>';
        html += '<div class="info-value">' + document.getElementById('insurerType').selectedOptions[0].text + '</div>';
        html += '</div>';
        
        if (result.validation && result.validation.missing_fields.length > 0) {
            html += '<div class="extracted-info-item validation-error">';
            html += '<div class="info-label"><i class="fas fa-exclamation-circle me-1"></i>Missing Fields</div>';
            html += '<div class="info-value">' + result.validation.missing_fields.join(', ') + '</div>';
            html += '</div>';
        }
        
        html += '</div>';
        
        extractedInfo.innerHTML = html;
    }

    function displayNarrative(narrative) {
        const narrativeText = document.getElementById('narrativeText');
        narrativeText.innerHTML = '<div class="fade-in">' + narrative + '</div>';
    }

    function displayChecklist(checklist) {
        const checklistItems = document.getElementById('checklistItems');
        
        let html = '<div class="fade-in">';
        
        if (checklist.length === 0) {
            html += '<div class="text-muted text-center py-4">';
            html += '<i class="fas fa-info-circle fa-2x mb-3"></i>';
            html += '<p>No specific documentation requirements found.</p>';
            html += '</div>';
        } else {
            checklist.forEach(item => {
                html += '<div class="form-check">';
                html += '<input class="form-check-input" type="checkbox" id="' + item.id + '">';
                html += '<label class="form-check-label" for="' + item.id + '">';
                html += '<strong>' + item.name + '</strong>';
                if (item.required) {
                    html += '<span class="required-badge">Required</span>';
                } else {
                    html += '<span class="optional-badge">Optional</span>';
                }
                html += '<div class="text-muted">' + item.description + '</div>';
                html += '</label>';
                
                if (item.file_upload) {
                    html += '<div class="file-upload-placeholder mt-2">';
                    html += '<i class="fas fa-cloud-upload-alt"></i>';
                    html += '<div>Click to upload or drag file here</div>';
                    html += '<small class="text-muted">PDF, JPG, PNG accepted</small>';
                    html += '</div>';
                }
                
                html += '</div>';
            });
        }
        
        html += '</div>';
        
        checklistItems.innerHTML = html;
    }

    function displayMissingInfoPrompts(prompts) {
        const missingInfoPrompts = document.getElementById('missingInfoPrompts');
        
        let html = '<div class="fade-in">';
        
        if (prompts.length === 0) {
            html += '<div class="text-success text-center py-4">';
            html += '<i class="fas fa-check-circle fa-2x mb-3"></i>';
            html += '<p>All required information appears to be present.</p>';
            html += '</div>';
        } else {
            html += '<div class="alert alert-info">';
            html += '<i class="fas fa-info-circle me-2"></i>';
            html += 'Please provide the following missing information:';
            html += '</div>';
            
            prompts.forEach((prompt, index) => {
                html += '<div class="prompt-item">';
                html += '<i class="fas fa-question-circle me-2"></i>';
                html += '<strong>Question ' + (index + 1) + ':</strong> ' + prompt;
                html += '</div>';
            });
        }
        
        html += '</div>';
        
        missingInfoPrompts.innerHTML = html;
    }

    function displayPolicyFlags(flags) {
        if (flags.length === 0) {
            policyFlagsAlert.style.display = 'none';
            return;
        }
        
        const policyFlagsList = document.getElementById('policyFlagsList');
        
        let html = '';
        flags.forEach(flag => {
            html += '<div class="policy-flag">';
            html += '<i class="fas fa-info-circle me-2"></i>' + flag;
            html += '</div>';
        });
        
        policyFlagsList.innerHTML = html;
        policyFlagsAlert.style.display = 'block';
    }

    function displayValidationStatus(validation) {
        // This could be expanded to show more detailed validation information
        console.log('Validation status:', validation);
    }

    function copyNarrative() {
        const narrativeText = document.getElementById('narrativeText').innerText;
        
        navigator.clipboard.writeText(narrativeText).then(() => {
            const copyBtn = document.getElementById('copyNarrativeBtn');
            const originalText = copyBtn.innerHTML;
            
            copyBtn.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
            copyBtn.classList.add('copy-success');
            
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.classList.remove('copy-success');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            alert('Failed to copy text to clipboard');
        });
    }

    function showEditModal() {
        // This would show a modal with editable fields
        // For now, just show a simple alert
        alert('Edit functionality coming soon! This would allow you to edit extracted information and regenerate the pre-authorization.');
    }

    function saveEdits() {
        // This would save the edits and regenerate
        document.getElementById('editModal').querySelector('[data-bs-dismiss="modal"]').click();
        regeneratePreAuth();
    }

    function getCurrentEdits() {
        // This would collect current edits from the edit form
        // For now, return empty object
        return {};
    }

    function showLoading(show) {
        loadingSpinner.style.display = show ? 'block' : 'none';
    }

    function hideResults() {
        extractedInfoCard.style.display = 'none';
        resultsCard.style.display = 'none';
        policyFlagsAlert.style.display = 'none';
    }

    function showResults() {
        extractedInfoCard.style.display = 'block';
        resultsCard.style.display = 'block';
        
        // Scroll to results
        resultsCard.scrollIntoView({ behavior: 'smooth' });
    }

    function showError(message) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-circle me-2"></i>
                <strong>Error:</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Insert error alert after the form
        form.insertAdjacentHTML('afterend', alertHtml);
        
        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            const alert = document.querySelector('.alert-danger');
            if (alert) {
                alert.remove();
            }
        }, 10000);
    }

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
