from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import numpy as np
from data_loader import ProcedureDataLoader
from preauth.generator import PreAuthGenerator

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Initialize data loader
data_loader = ProcedureDataLoader('VDH_Procedure_Durations_rev0.1.xlsx')

# Initialize pre-authorization generator
preauth_generator = PreAuthGenerator()

@app.route('/')
def index():
    """Main page for time estimation"""
    procedures = data_loader.get_procedures()
    providers = data_loader.get_providers()
    mitigating_factors = data_loader.get_mitigating_factors()
    
    return render_template('index.html', 
                         procedures=procedures, 
                         providers=providers, 
                         mitigating_factors=mitigating_factors)

@app.route('/estimate', methods=['POST'])
def estimate():
    """Calculate appointment time"""
    try:
        data = request.get_json()
        provider = data.get('provider')
        mitigating_factors = data.get('mitigating_factors', [])
        procedures_data = data.get('procedures_data', [])
        
        # Handle backward compatibility for single procedure
        if not procedures_data and data.get('procedure'):
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

@app.route('/api/providers')
def get_providers():
    """API endpoint to get all providers"""
    return jsonify(data_loader.get_providers())

@app.route('/api/mitigating_factors')
def get_mitigating_factors():
    """API endpoint to get all mitigating factors"""
    return jsonify(data_loader.get_mitigating_factors())

@app.route('/api/procedures/<provider>')
def get_procedures_for_provider(provider):
    """API endpoint to get procedures filtered by provider"""
    return jsonify(data_loader.get_procedures(provider=provider))

@app.route('/api/providers/<procedure>')
def get_providers_for_procedure(procedure):
    """API endpoint to get providers filtered by procedure"""
    return jsonify(data_loader.get_providers(procedure=procedure))

# Pre-Authorization Generator Routes
@app.route('/preauth')
def preauth_index():
    """Pre-authorization generator main page"""
    return render_template('preauth/index.html')

@app.route('/preauth/generate', methods=['POST'])
def generate_preauth():
    """Generate pre-authorization from clinical text"""
    try:
        data = request.get_json()
        clinical_text = data.get('clinical_text', '')
        procedure_type = data.get('procedure_type', '')
        insurer_type = data.get('insurer_type', '')
        
        if not all([clinical_text, procedure_type, insurer_type]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = preauth_generator.generate_preauth(
            clinical_text=clinical_text,
            procedure_type_str=procedure_type,
            insurer_type_str=insurer_type
        )
        
        # Store case record data in session (temporarily disabled due to serialization issues)
        # session['case_record'] = result.case_record.__dict__
        
        return jsonify({
            'success': True,
            'extracted_info': result.case_record.__dict__,
            'narrative': result.narrative,
            'checklist': result.checklist,
            'missing_info_prompts': result.missing_info_prompts,
            'policy_flags': result.policy_flags
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/preauth/regenerate', methods=['POST'])
def regenerate_preauth():
    """Regenerate pre-authorization with edited case record"""
    try:
        data = request.get_json()
        case_record_data = data.get('case_record_data', {})
        clinical_text = data.get('clinical_text', '')
        
        if not case_record_data or not clinical_text:
            return jsonify({'error': 'Missing required data'}), 400
        
        result = preauth_generator.regenerate_preauth(
            case_record_data=case_record_data,
            clinical_text=clinical_text
        )
        
        return jsonify({
            'success': True,
            'narrative': result.narrative,
            'checklist': result.checklist,
            'missing_info_prompts': result.missing_info_prompts,
            'policy_flags': result.policy_flags
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/preauth/procedures')
def get_preauth_procedures():
    """API endpoint to get supported procedures for pre-auth"""
    return jsonify(preauth_generator.get_supported_procedures())

@app.route('/api/preauth/insurers')
def get_preauth_insurers():
    """API endpoint to get supported insurers"""
    return jsonify(preauth_generator.get_supported_insurers())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
