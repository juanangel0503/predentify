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
        procedure = data.get('procedure')
        provider = data.get('provider')
        mitigating_factors = data.get('mitigating_factors', [])
        
        # Get base times
        result = data_loader.calculate_appointment_time(
            procedure=procedure,
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