# Add to __init__ method after line 11:
        self.procedure1_to_procedure2 = {}  # Mapping of Procedure 1 -> Procedure 2

# Add to load_data method after provider_compatibility loading:
            with open(os.path.join(self.data_dir, 'procedure1_to_procedure2.json'), 'r') as f:
                self.procedure1_to_procedure2 = json.load(f)

# New methods to add after get_procedures method:
    def get_procedure1_procedures(self) -> List[str]:
        """Get list of available Procedure 1 procedures"""
        procedure1_procedures = []
        for procedure in self.available_procedures:
            proc_data = self.procedures_data.get(procedure, {})
            if proc_data.get('section') == 'procedure1':
                procedure1_procedures.append(procedure)
        return sorted(procedure1_procedures)

    def get_procedure2_procedures_for_procedure1_and_provider(self, procedure1: str, provider: str) -> List[str]:
        """Get list of valid Procedure 2 procedures based on Procedure 1 and Provider"""
        valid_procedure2 = []
        
        # Get possible Procedure 2 procedures for this Procedure 1
        if procedure1 in self.procedure1_to_procedure2:
            possible_procedure2 = self.procedure1_to_procedure2[procedure1]
            
            # Filter by provider compatibility and availability
            for proc2 in possible_procedure2:
                if (proc2 in self.available_procedures and 
                    self.check_provider_performs_procedure(provider, proc2)):
                    valid_procedure2.append(proc2)
        
        return sorted(valid_procedure2)

    def get_all_procedure2_procedures(self) -> List[str]:
        """Get list of all available Procedure 2 procedures"""
        procedure2_procedures = []
        for procedure in self.available_procedures:
            proc_data = self.procedures_data.get(procedure, {})
            if proc_data.get('section') == 'procedure2':
                procedure2_procedures.append(procedure)
        return sorted(procedure2_procedures)
