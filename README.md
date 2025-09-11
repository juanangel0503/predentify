# PreDentify - Appointment Time Estimator

A web-based tool for dental practices to accurately estimate appointment times based on procedures, providers, and patient-specific factors.

## Features

- **Procedure Selection**: Choose from 40+ dental procedures
- **Provider-Specific Timing**: Different providers may have different timing for procedures
- **Mitigating Factors**: Account for patient-specific factors that affect appointment duration
- **Time Breakdown**: Shows separate assistant/hygienist and doctor time
- **Real-time Calculation**: Automatically updates estimates as selections change
- **Provider Compatibility**: Warns when a provider doesn't typically perform a selected procedure

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

4. **Ensure Excel file is present**:
   - Make sure `VDH_Procedure_Durations_rev0.1.xlsx` is in the root directory
   - This file contains all procedure timing data

## Usage

1. **Start the application**:

   ```bash
   source myenv/bin/activate  # Activate virtual environment
   python app.py
   ```

2. **Access the web interface**:

   - Open your browser and go to `http://localhost:5000`

3. **Using the estimator**:
   - Select a procedure from the dropdown
   - Choose a provider
   - Optionally select mitigating factors
   - View the calculated appointment time breakdown

## File Structure

```
predentify/
├── app.py                              # Main Flask application
├── data_loader.py                      # Excel data processing logic
├── requirements.txt                    # Python dependencies
├── VDH_Procedure_Durations_rev0.1.xlsx # Procedure timing data
├── templates/
│   └── index.html                      # Main web interface
├── static/
│   ├── css/
│   │   └── style.css                   # Custom styling
│   └── js/
│       └── app.js                      # Frontend JavaScript
├── test_app.py                         # Test script
└── README.md                           # This file
```

## API Endpoints

The application provides several API endpoints:

- `GET /` - Main web interface
- `GET /api/procedures` - List all available procedures
- `GET /api/providers` - List all providers
- `GET /api/mitigating_factors` - List all mitigating factors
- `POST /estimate` - Calculate appointment time

### Example API Usage

```bash
# Get all procedures
curl http://localhost:5000/api/procedures

# Calculate appointment time
curl -X POST http://localhost:5000/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "procedure": "Filling",
    "provider": "Kayla",
    "mitigating_factors": ["Special Needs"]
  }'
```

## Data Structure

The application reads procedure data from the Excel file with the following structure:

- **Procedures**: Listed in the "Procedure 1" column
- **Base Times**: Assistant/Hygienist Time and Doctor Time columns
- **Provider Compatibility**: Binary flags (1/0) for each provider
- **Mitigating Factors**: Factors with multipliers or additional time

## Mitigating Factors

The following factors can affect appointment duration:

- **Special Needs** (+10 min)
- **Language Barrier** (+10 min)
- **PITA** (+10 min)
- **TLC** (+10 min)
- **Extra Freezing Required** (+10 min)
- **Limited Opening / TMJ Issues** (+10 min)
- **Cosmetic Case** (+10 min)
- **Provider Learning Curve** (1.15x multiplier)
- **Assistant Unfamiliarity** (1.10x multiplier)
- **Need for Informed Consent** (+10 min)

## Testing

Run the test suite to verify everything is working:

```bash
source myenv/bin/activate
python test_app.py
```

## Future Enhancements

This is version 1.0 of PreDentify. Planned enhancements include:

1. **AI-Powered Predictions**: Machine learning to improve time estimates
2. **Insurance Integration**: Generate preauthorization narratives
3. **Patient History**: Factor in patient-specific historical data
4. **Scheduling Integration**: Connect with appointment scheduling systems
5. **Mobile App**: Native mobile application
6. **Analytics Dashboard**: Track timing accuracy and optimize estimates

## Technical Details

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **Data Processing**: Pandas for Excel file handling
- **Styling**: Custom CSS with Font Awesome icons
- **Responsive Design**: Mobile-friendly interface

## Troubleshooting

### Common Issues

1. **Excel file not found**:

   - Ensure `VDH_Procedure_Durations_rev0.1.xlsx` is in the root directory

2. **Port already in use**:

   - Kill existing Flask processes: `pkill -f "python app.py"`
   - Or change the port in `app.py`

3. **Dependencies not installed**:
   - Make sure virtual environment is activated
   - Run `pip install -r requirements.txt`

### Support

For issues or questions, please check:

1. Ensure all dependencies are installed
2. Verify the Excel file is present and readable
3. Check console output for error messages

## License

This project is designed for internal use at dental practices. Please ensure compliance with your organization's data handling policies.

---

**PreDentify v1.0** - Built with ❤️ for better appointment scheduling
