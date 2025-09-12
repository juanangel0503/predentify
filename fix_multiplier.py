# Quick fix for the multiplier issue
import sys
import re

# Read the current data_loader.py
with open('data_loader.py', 'r') as f:
    content = f.read()

# Find and replace the factors.append section
old_pattern = r"""            factors\.append\(\{
                'name': factor_name,
                'value': value,
                'is_multiplier': value <= 2\.0  # Values <= 2 are multipliers, > 2 are additive
            \}\)"""

new_pattern = """            factors.append({
                'name': factor_name,
                'value': value,
                'multiplier': value,  # Add this field for JavaScript compatibility
                'is_multiplier': value <= 2.0  # Values <= 2 are multipliers, > 2 are additive
            })"""

# Replace the pattern
updated_content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

# Write back to file
with open('data_loader.py', 'w') as f:
    f.write(updated_content)

print("Fixed multiplier field in data_loader.py")
