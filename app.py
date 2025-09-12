from flask import Flask, render_template, request, jsonify, session
from data_loader import ProcedureDataLoader

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'  # Enable sessions

# Initialize JSON-based data loader
data_loader = ProcedureDataLoader('data')

# Pre-Authorization Generator
from preauth.generator import PreAuthGenerator
preauth_generator = PreAuthGenerator()

@app.route('/')
def index():
    """Main page with the appointment estimation form"""
    procedures = data_loader.get_procedures()
    providers = data_loader.get_providers()
    mitigating_factors = data_loader.get_mitigating_factors()
    
    return render_template('index.html', 
                         procedures=procedures, 
                         providers=providers,
                         mitigating_factors=mitigating_factors)

@app.route('/estimate', methods=['POST'])
def estimate_time():
    """Calculate appointment time based on selected parameters"""
    try:
        data = request.get_json()
        provider = data.get('provider')
        mitigating_factors = data.get('mitigating_factors', [])
        procedures_data = data.get('procedures', [])
        
        # Handle both single procedure (backward compatibility) and multiple procedures
        if not procedures_data:
            # Backward compatibility: single procedure
            procedure = data.get('procedure')
            num_teeth = int(data.get('num_teeth', 1))
            num_surfaces = int(data.get('num_surfaces', 1))
            num_quadrants = int(data.get('num_quadrants', 1))
            
            result = data_loader.calculate_single_appointment_time(
                procedure=procedure,
                provider=provider,
                mitigating_factors=mitigating_factors,
                num_teeth=num_teeth,
                num_surfaces=num_surfaces,
                num_quadrants=num_quadrants
            )
        else:
            # Multiple procedures
            result = data_loader.calculate_appointment_time(
                procedures=procedures_data,
                provider=provider,
                mitigating_factors=mitigating_factors
            )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/procedures')
def get_procedures():
    """API endpoint to get all procedures"""
    return jsonify(data_loader.get_procedures())

@app.route('/api/procedures/<provider>')
def get_procedures_for_provider(provider):
    """API endpoint to get procedures that a specific provider can perform"""
    all_procedures = data_loader.get_procedures()
    compatible_procedures = []
    
    for procedure in all_procedures:
        if data_loader.check_provider_performs_procedure(procedure, provider):
            compatible_procedures.append(procedure)
    
    return jsonify(compatible_procedures)

@app.route('/api/providers')
def get_providers():
    """API endpoint to get all providers"""
    return jsonify(data_loader.get_providers())

@app.route('/api/mitigating_factors')
def get_mitigating_factors():
    """API endpoint to get all mitigating factors"""
    return jsonify(data_loader.get_mitigating_factors())

# Pre-Authorization Generator routes
@app.route('/preauth')
def preauth_index():
    """Pre-authorization generator main page"""
    procedures = preauth_generator.get_supported_procedures()
    insurers = preauth_generator.get_supported_insurers()
    
    return render_template('preauth/index.html', 
                         procedures=procedures,
                         insurers=insurers)

@app.route('/preauth/generate', methods=['POST'])
def generate_preauth():
    """Generate pre-authorization from clinical text"""
    try:
        data = request.get_json()
        clinical_text = data.get('clinical_text', '')
        procedure_type = data.get('procedure_type', '')
        insurer_type = data.get('insurer_type', '')
        
        if not all([clinical_text, procedure_type, insurer_type]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: clinical_text, procedure_type, insurer_type'
            }), 400
        
        result = preauth_generator.generate_preauth(clinical_text, procedure_type, insurer_type)
        
        # Convert result to dictionary for JSON serialization
        response_data = {
            'success': result.success,
            'narrative': result.narrative,
            'checklist': result.checklist,
            'missing_info_prompts': result.missing_info_prompts,
            'policy_flags': result.policy_flags,
            'validation': {
                'is_valid': result.validation.is_valid,
                'missing_fields': result.validation.missing_fields,
                'warnings': result.validation.warnings
            }
        }
        
        # Include case record for editing if successful
        if result.success and result.case_record:
            response_data['case_record_id'] = id(result.case_record)  # Simple ID for demo
            # Note: Skipping session storage for now due to enum serialization issues
            # In production, use proper storage with custom serialization
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error generating pre-authorization: {str(e)}'
        }), 500

@app.route('/preauth/regenerate', methods=['POST'])
def regenerate_preauth():
    """Regenerate pre-authorization with edits"""
    try:
        data = request.get_json()
        case_record_id = data.get('case_record_id')
        edits = data.get('edits', {})
        
        if not case_record_id:
            return jsonify({
                'success': False,
                'error': 'Missing case_record_id'
            }), 400
        
        # Retrieve case record from session (in production, use proper storage)
        case_record = session.get(f'case_record_{case_record_id}')
        
        if not case_record:
            return jsonify({
                'success': False,
                'error': 'Case record not found'
            }), 404
        
        result = preauth_generator.regenerate_with_edits(case_record, edits)
        
        # Convert result to dictionary
        response_data = {
            'success': result.success,
            'narrative': result.narrative,
            'checklist': result.checklist,
            'missing_info_prompts': result.missing_info_prompts,
            'policy_flags': result.policy_flags,
            'validation': {
                'is_valid': result.validation.is_valid,
                'missing_fields': result.validation.missing_fields,
                'warnings': result.validation.warnings
            }
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error regenerating pre-authorization: {str(e)}'
        }), 500

@app.route('/api/preauth/procedures')
def get_preauth_procedures():
    """API endpoint to get supported procedures"""
    return jsonify(preauth_generator.get_supported_procedures())

@app.route('/api/preauth/insurers')
def get_preauth_insurers():
    """API endpoint to get supported insurers"""
    return jsonify(preauth_generator.get_supported_insurers())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
