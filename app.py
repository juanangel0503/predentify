from flask import Flask, render_template, request, jsonify, session
from data_loader import ProcedureDataLoader
from preauth.generator import PreAuthGenerator

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Initialize data loader
data_loader = ProcedureDataLoader('data')

@app.route('/')
def index():
    """Main page for appointment time estimation"""
    procedures = data_loader.get_procedures()
    providers = data_loader.get_providers()
    mitigating_factors = data_loader.get_mitigating_factors()
    
    return render_template('index.html', 
                         procedures=procedures, 
                         providers=providers, 
                         mitigating_factors=mitigating_factors)

@app.route('/estimate', methods=['POST'])
def estimate_time():
    """API endpoint to calculate appointment time"""
    try:
        data = request.get_json()
        provider = data.get('provider')
        procedures = data.get('procedures', [])
        mitigating_factors = data.get('mitigating_factors', [])
        
        if not provider or not procedures:
            return jsonify({'error': 'Provider and procedures are required'}), 400
        
        # Calculate appointment time
        result = data_loader.calculate_appointment_time(
            procedures=procedures,
            provider=provider,
            mitigating_factors=mitigating_factors
        )
        
        return jsonify({
            'success': True,
            'procedures': result.get('procedure_details', []),
            'provider': result.get('provider', provider),
            'base_times': result.get('base_times', {}),
            'final_times': result.get('final_times', {}),
            'applied_factors': result.get('applied_factors', []),
            'raw_result': result  # Keep original for debugging
        })
    
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
        # FIXED: Correct parameter order - provider first, then procedure
        if data_loader.check_provider_performs_procedure(provider, procedure):
            compatible_procedures.append(procedure)
    
    return jsonify(compatible_procedures)

@app.route('/api/procedures2')
def get_procedures2():
    """API endpoint to get procedure 2 items only"""
    return jsonify(data_loader.get_procedures2())

@app.route('/api/procedures2/<provider>/<procedure1>')
def get_procedures2_filtered(provider, procedure1):
    """API endpoint to get procedure 2 items filtered by provider and procedure 1"""
    all_procedure2 = data_loader.get_procedures2()
    compatible_procedure2 = []
    
    # Define procedure 1 to procedure 2 relationships
    procedure_relationships = {
        "Filling": ["Pulp Cap", "Sedation"],
        "Implant surgery": ["Bone Graft", "Post", "Pulp Cap", "Root Canal Treated Tooth", "Sinus Lift", "Socket Preservation", "Sedation"],
        "Root Canal": ["Post", "Pulp Cap", "Sedation", "Filling"],
        "Crown preparation": ["Post", "Pulp Cap", "Sedation", "Filling"],
        "Extraction": ["Bone Graft", "Socket Preservation", "Sedation", "Filling"]
    }
    # Get valid procedure 2 items for this procedure 1
    valid_procedure2_for_procedure1 = procedure_relationships.get(procedure1, [])
    for proc2 in valid_procedure2_for_procedure1:
        # Check if provider can perform this procedure 2 AND it is valid for this procedure 1
        if data_loader.check_provider_performs_procedure(provider, proc2):
            compatible_procedure2.append(proc2)
    
    return jsonify(compatible_procedure2)

@app.route('/api/providers')
def get_providers():
    """API endpoint to get all providers"""
    return jsonify(data_loader.get_providers())

@app.route('/api/providers/<procedure>')
def get_providers_for_procedure(procedure):
    """API endpoint to get providers who can perform a specific procedure"""
    all_providers = data_loader.get_providers()
    compatible_providers = []
    
    for provider in all_providers:
        # FIXED: Correct parameter order - provider first, then procedure
        if data_loader.check_provider_performs_procedure(provider, procedure):
            compatible_providers.append(provider)
    
    return jsonify(compatible_providers)

@app.route('/api/mitigating_factors')
def get_mitigating_factors():
    """API endpoint to get mitigating factors"""
    return jsonify(data_loader.get_mitigating_factors())

# Pre-Authorization Generator Routes
@app.route('/preauth')
def preauth_index():
    """Pre-authorization generator main page"""
    return render_template('preauth/index.html')

@app.route('/preauth/generate', methods=['POST'])
def generate_preauth():
    """API endpoint to generate pre-authorization"""
    try:
        data = request.get_json()
        clinical_text = data.get('clinical_text', '')
        procedure = data.get('procedure', '')
        insurer = data.get('insurer', '')
        
        if not all([clinical_text, procedure, insurer]):
            return jsonify({'error': 'Clinical text, procedure, and insurer are required'}), 400
        
        # Initialize pre-auth generator
        preauth_generator = PreAuthGenerator()
        
        # Generate pre-authorization
        result = preauth_generator.generate_preauth(
            clinical_text=clinical_text,
            procedure=procedure,
            insurer=insurer
        )
        
        # Store case record in session (simplified for now)
        # Note: In production, you'd want proper serialization for enums
        session['current_case'] = {
            'clinical_text': clinical_text,
            'procedure': procedure,
            'insurer': insurer,
            'extracted_info': result.extracted_info.__dict__ if hasattr(result.extracted_info, '__dict__') else {}
        }
        
        return jsonify({
            'success': True,
            'narrative': result.narrative,
            'checklist': result.checklist,
            'missing_prompts': result.missing_prompts,
            'policy_flags': result.policy_flags,
            'extracted_info': {
                'procedure_type': result.extracted_info.procedure_type.value if hasattr(result.extracted_info.procedure_type, 'value') else str(result.extracted_info.procedure_type),
                'insurer_type': result.extracted_info.insurer_type.value if hasattr(result.extracted_info.insurer_type, 'value') else str(result.extracted_info.insurer_type),
                'clinical_findings': result.extracted_info.clinical_findings,
                'artifacts': result.extracted_info.artifacts
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/preauth/regenerate', methods=['POST'])
def regenerate_preauth():
    """API endpoint to regenerate pre-authorization after edits"""
    try:
        data = request.get_json()
        clinical_text = data.get('clinical_text', '')
        procedure = data.get('procedure', '')
        insurer = data.get('insurer', '')
        edited_info = data.get('edited_info', {})
        
        if not all([clinical_text, procedure, insurer]):
            return jsonify({'error': 'Clinical text, procedure, and insurer are required'}), 400
        
        # Initialize pre-auth generator
        preauth_generator = PreAuthGenerator()
        
        # Regenerate pre-authorization with edited info
        result = preauth_generator.regenerate_preauth(
            clinical_text=clinical_text,
            procedure=procedure,
            insurer=insurer,
            edited_info=edited_info
        )
        
        return jsonify({
            'success': True,
            'narrative': result.narrative,
            'checklist': result.checklist,
            'missing_prompts': result.missing_prompts,
            'policy_flags': result.policy_flags
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/preauth/procedures')
def get_preauth_procedures():
    """API endpoint to get procedures for pre-authorization"""
    # Return procedures that typically require pre-authorization
    preauth_procedures = [
        'Crown preparation',
        'Bridge',
        'Implant surgery',
        'Orthodontic treatment',
        'Additional scaling units',
        'Onlay',
        'Veneer'
    ]
    return jsonify(preauth_procedures)

@app.route('/api/preauth/insurers')
def get_preauth_insurers():
    """API endpoint to get supported insurers"""
    insurers = ['CDCP', 'Private (Generic Template)']
    return jsonify(insurers)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
