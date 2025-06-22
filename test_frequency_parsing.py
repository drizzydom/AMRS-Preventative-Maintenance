#!/usr/bin/env python3
"""
Test frequency parsing functionality
"""

def parse_frequency_string(frequency_str):
    """Parse a frequency string like '6 Months', '1 Year', '30 Days' into numeric value and unit"""
    if not frequency_str:
        return 30, 'day'  # default
    
    import re
    freq_lower = str(frequency_str).lower().strip()
    
    # Extract numeric value from the frequency string
    numbers = re.findall(r'\d+', freq_lower)
    numeric_value = int(numbers[0]) if numbers else 1
    
    # Convert everything to days for consistency
    if 'year' in freq_lower:
        return numeric_value * 365, 'day'
    elif 'month' in freq_lower:
        return numeric_value * 30, 'day'
    elif 'week' in freq_lower:
        return numeric_value * 7, 'day'
    elif 'day' in freq_lower:
        return numeric_value, 'day'
    else:
        # If no unit specified, assume the number is in days
        if numbers:
            return numeric_value, 'day'
        return 30, 'day'  # fallback default

def test_frequency_parsing():
    """Test various frequency formats found in the JSON data"""
    test_cases = [
        ("1 Year", 365, 'day'),
        ("1 year", 365, 'day'),
        ("2 Years", 730, 'day'),
        ("6 Months", 180, 'day'),
        ("6 months", 180, 'day'),
        ("10 Months", 300, 'day'),
        ("13 Months", 390, 'day'),
        ("18 Months", 540, 'day'),
        ("3 Months", 90, 'day'),
        ("4 Months", 120, 'day'),
        ("5 Months", 150, 'day'),
        ("8 Months", 240, 'day'),
        ("30 Days", 30, 'day'),
        ("7 Days", 7, 'day'),
        ("", 30, 'day'),  # default case
        ("invalid", 30, 'day'),  # fallback case
    ]
    
    print("Testing frequency parsing...")
    print("=" * 50)
    
    all_passed = True
    for freq_str, expected_value, expected_unit in test_cases:
        actual_value, actual_unit = parse_frequency_string(freq_str)
        
        if actual_value == expected_value and actual_unit == expected_unit:
            status = "✓ PASS"
        else:
            status = "✗ FAIL"
            all_passed = False
        
        print(f"{status}: '{freq_str}' -> {actual_value} {actual_unit} (expected: {expected_value} {expected_unit})")
    
    print("=" * 50)
    if all_passed:
        print("🎉 All frequency parsing tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    test_frequency_parsing()
