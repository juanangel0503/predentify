# PreDentify - Appointment Time Estimator

A web-based tool for dental practices to accurately estimate appointment times based on procedures, providers, and patient-specific factors.

## Features

- **Procedure Selection**: Choose from 40+ dental procedures with intelligent filtering
- **Provider-Specific Timing**: Different providers have different base times for procedures
- **Multi-Procedure Support**: Add multiple procedures with automatic 30% reduction for additional procedures
- **Mitigating Factors**: Account for patient-specific factors that affect appointment duration
- **Time Breakdown**: Shows separate assistant/hygienist and doctor time
- **Real-time Calculation**: Automatically updates estimates as selections change
- **Provider Compatibility**: Dynamic filtering based on provider capabilities
- **Procedure Relationships**: Smart filtering of Procedure 2 options based on Procedure 1 selection

## Recent Updates (v1.1)

### ✅ Implemented Excel Formula Logic
- **Procedure 1 Formulas**: Implemented exact Excel formulas for all major procedures
  - **Implant**: Teeth ≤1 → 90min, Teeth >1 → 80 + 10×Teeth
  - **Filling**: Surfaces ≤1 → 30min, complex formula for Surfaces >1
  - **Crown**: Teeth ≤1 → 90min, Teeth >1 → 90 + 30×(Teeth-1)
  - **Crown Delivery**: Teeth ≤1 → 40min, Teeth >1 → 40 + 10×(Teeth-1)
  - **Root Canal**: Surfaces ≤1 → 60min, Surfaces >1 → 60 + 10×(Surfaces-1)
  - **Gum Graft**: Teeth ≤1 → 70min, Teeth >1 → 70 + 20×(Teeth-1)
  - **Pulpectomy**: Surfaces ≤1 → 50min, Surfaces >1 → 50 + 5×(Surfaces-1)
  - **Extraction**: Complex multi-condition formula based on Teeth and Quadrants

### ✅ Provider-Specific Base Times
- **Metadata1 Integration**: Uses provider-specific lookup tables for base times
- **Dynamic Calculation**: Different providers have different base times for the same procedure
- **Fallback Logic**: Falls back to generic procedure times when provider-specific data unavailable

### ✅ Enhanced Procedure Management
- **Procedure Order Logic**: Procedure 1 from `/api/procedures`, subsequent from `/api/procedures2`
- **Smart Filtering**: Procedure 2 options filtered by both provider compatibility and Procedure 1 relationships
- **Auto-Reset**: Additional procedures reset when Provider or Procedure 1 changes
- **Duplicate Prevention**: Renamed duplicate procedures (Additional Filling, Additional Extraction, Additional Sedation)

### ✅ Improved Time Calculations
- **Accurate Rounding**: Uses Excel MROUND logic (round to nearest 10)
- **Doctor Time Calculation**: Doctor time = Total time - Assistant time
- **30% Reduction Logic**: Applied to additional procedures with exceptions for Sedation, Additional Filling, Socket Preservation
- **Assistant Time Logic**: Sums all when Sedation involved, otherwise uses first procedure only

## Installation

1. **Clone or download** the project to your local machine

2. **Set up virtual environment**:

   ```bash
   python3 -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure data files are present**:
   - `data/procedures.json` - Procedure definitions and base times
   - `data/provider_compatibility.json` - Provider-procedure compatibility matrix
   - `data/mitigating_factors.json` - Mitigating factors with applicability rules

## Usage

1. **Start the application**:

   ```bash
   source myenv/bin/activate  # Activate virtual environment
   python app.py
   ```

2. **Access the web interface**:

   - Open your browser and go to `http://localhost:5000`

3. **Using the estimator**:
   - Select a provider from the dropdown
   - Choose Procedure 1 from the filtered list
   - Optionally add Procedure 2 (filtered by provider and Procedure 1)
   - Add mitigating factors (filtered by selected procedure)
   - View the calculated appointment time breakdown

## File Structure

```
predentify/
├── app.py                              # Main Flask application
├── data_loader.py                      # Calculation logic with Excel formulas
├── requirements.txt                    # Python dependencies
├── VDH_Procedure_Durations_rev0.2.xlsx # Reference Excel file
├── data/
│   ├── procedures.json                 # Procedure definitions and base times
│   ├── provider_compatibility.json     # Provider-procedure compatibility
│   └── mitigating_factors.json         # Mitigating factors with rules
├── templates/
│   ├── index.html                      # Main web interface
│   └── preauth.html                    # Preauthorization interface
├── static/
│   ├── css/
│   │   ├── style.css                   # Custom styling
│   │   └── preauth/
│   │       └── preauth.css             # Preauth styling
│   └── js/
│       ├── app.js                      # Frontend JavaScript
│       └── preauth/
│           └── preauth.js              # Preauth JavaScript
└── README.md                           # This file
```

## API Endpoints

The application provides several API endpoints:

- `GET /` - Main web interface
- `GET /preauth` - Preauthorization interface
- `GET /api/procedures` - List all available procedures
- `GET /api/procedures/<provider>` - List procedures available to specific provider
- `GET /api/procedures2/<provider>/<procedure1>` - List Procedure 2 options
- `GET /api/providers` - List all providers
- `GET /api/providers/<procedure>` - List providers who can perform procedure
- `GET /api/mitigating-factors/<procedure>` - List mitigating factors for procedure
- `POST /estimate` - Calculate appointment time

### Example API Usage

```bash
# Get procedures for specific provider
curl http://localhost:5000/api/procedures/Dr.%20Miekella

# Get Procedure 2 options
curl http://localhost:5000/api/procedures2/Dr.%20Miekella/Filling

# Calculate appointment time
curl -X POST http://localhost:5000/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "Dr. Miekella",
    "procedures": [
      {"procedure": "Filling", "num_teeth": 3, "num_surfaces": 1, "num_quadrants": 4}
    ],
    "mitigating_factors": ["Special Needs"]
  }'
```

## Data Structure

The application uses JSON files for data storage:

### procedures.json
- **Procedure definitions**: Base times, assistant times, section (procedure1/procedure2)
- **Provider-specific overrides**: Special handling for New Patient Exam times

### provider_compatibility.json
- **Provider-procedure matrix**: Which providers can perform which procedures
- **Comprehensive coverage**: All provider-procedure combinations

### mitigating_factors.json
- **Factor definitions**: Duration/multiplier values
- **Applicability rules**: Which procedures each factor applies to
- **Type classification**: Additive (10min) vs Multiplicative (1.15x, 1.1x)

## Mitigating Factors

The following factors can affect appointment duration:

### Additive Factors (+10 minutes each)
- **Special Needs**
- **Language Barrier**
- **PITA**
- **TLC**
- **Extra Freezing Required**
- **Limited Opening / TMJ Issues**
- **Cosmetic Case**
- **Need for Informed Consent or Discussion**

### Multiplicative Factors
- **Provider Learning Curve** (1.15x multiplier)
- **Assistant Unfamiliarity** (1.10x multiplier)

## Calculation Examples

### Filling Procedure
- **Provider**: Dr. Miekella
- **Teeth**: 3, **Surfaces**: 1, **Quadrants**: 4
- **Result**: Total: 30min, Assistant: 10min, Doctor: 20min

### Implant Surgery
- **Provider**: Dr. Miekella
- **Teeth**: 3
- **Result**: Total: 110min (80 + 10×3), Assistant: 30min, Doctor: 80min

### Multi-Procedure Example
- **Procedure 1**: Implant Surgery (Teeth: 1) → 90min
- **Procedure 2**: Additional Sedation → 60min (no 30% reduction)
- **Result**: Total: 150min, Assistant: 90min, Doctor: 60min

## Technical Details

- **Backend**: Flask (Python) with JSON data storage
- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **Calculation Engine**: Custom logic implementing Excel formulas
- **Data Processing**: JSON-based with provider-specific lookups
- **Styling**: Custom CSS with Font Awesome icons
- **Responsive Design**: Mobile-friendly interface

## Troubleshooting

### Common Issues

1. **Server won't start**:
   - Check for syntax errors: `python -m py_compile data_loader.py`
   - Ensure virtual environment is activated
   - Kill existing processes: `pkill -f "python app.py"`

2. **Calculation errors**:
   - Verify JSON files are valid: `python -c "import json; json.load(open('data/procedures.json'))"`
   - Check console output for error messages

3. **Missing procedures**:
   - Ensure provider compatibility data is complete
   - Check procedure relationships in app.py

### Support

For issues or questions:
1. Check console output for error messages
2. Verify all JSON files are valid
3. Ensure virtual environment is properly activated
4. Test individual API endpoints

## License

This project is designed for internal use at dental practices. Please ensure compliance with your organization's data handling policies.

---

**PreDentify v1.1** - Enhanced with Excel formula accuracy and provider-specific calculations

Built with ❤️ for better appointment scheduling
