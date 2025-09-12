from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from data_loader import ProcedureDataLoader

app = Flask(__name__)

# Initialize data loader
data_loader = ProcedureDataLoader('VDH_Procedure_Durations_rev0.1.xlsx')

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

@app.route('/api/providers')
def get_providers():
    """API endpoint to get all providers"""
    return jsonify(data_loader.get_providers())

@app.route('/api/mitigating_factors')
def get_mitigating_factors():
    """API endpoint to get all mitigating factors"""
    return jsonify(data_loader.get_mitigating_factors())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
