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

    // NEW: Function to get procedure2 options for secondary procedures
    async function getProcedure2Options() {
        try {
            const response = await fetch('/api/procedures2');
            if (!response.ok) {
                throw new Error(`Failed to load procedure2 items: ${response.status}`);
            }
            const procedure2Items = await response.json();
            
            let options = '';
            procedure2Items.forEach(procedure => {
                options += `<option value="${procedure}">${procedure}</option>`;
            });
            
            console.log(`🔄 Adding procedure2 row with ${procedure2Items.length} available procedure2 items`);
            return options;
        } catch (error) {
            console.error('Error loading procedure2 items:', error);
            return '<option value="">Error loading procedures...</option>';
        }
    }
