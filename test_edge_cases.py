#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BetterSelf.settings')
django.setup()

from Time_Manager.date_utils import parse_month, parse_day, parse_partial_date

# Test edge cases
print("Testing edge cases:\n")

# Test month input "Mar"
print("1. Month input 'Mar':")
try:
    result = parse_month("Mar")
    print(f"   ✓ parse_month('Mar') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test day input "Tue"
print("\n2. Day input 'Tue':")
try:
    result = parse_day("Tue")
    print(f"   ✓ parse_day('Tue') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test day input "Mon"
print("\n3. Day input 'Mon':")
try:
    result = parse_day("Mon")
    print(f"   ✓ parse_day('Mon') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test month input with partial
print("\n4. Month input 'Mar' in partial date:")
try:
    result = parse_partial_date(year=2026, month="Mar")
    print(f"   ✓ parse_partial_date(year=2026, month='Mar') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test other month names
print("\n5. Other month names:")
for month in ["Jan", "MAY", "december", "Sep"]:
    try:
        result = parse_month(month)
        print(f"   ✓ parse_month('{month}') → {result}")
    except Exception as e:
        print(f"   ✗ parse_month('{month}') Error: {e}")
