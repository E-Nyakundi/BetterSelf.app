#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BetterSelf.settings')
django.setup()

from Time_Manager.date_utils import parse_month, parse_day

# Test ambiguous inputs
print("Testing ambiguous and problematic inputs:\n")

# Test ambiguous month
print("1. Ambiguous month 'M' (could be May, March):")
try:
    result = parse_month("M")
    print(f"   ✓ parse_month('M') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test ambiguous month
print("\n2. Ambiguous month 'J' (could be Jan, Jun, Jul):")
try:
    result = parse_month("J")
    print(f"   ✓ parse_month('J') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test short but unambiguous
print("\n3. Unambiguous short 'Apr' (April):")
try:
    result = parse_month("Apr")
    print(f"   ✓ parse_month('Apr') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test short but unambiguous
print("\n4. Unambiguous short 'Aug' (August):")
try:
    result = parse_month("Aug")
    print(f"   ✓ parse_month('Aug') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test invalid day number
print("\n5. Invalid day '32' (out of range):")
try:
    result = parse_day("32")
    print(f"   ✓ parse_day('32') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test invalid month number
print("\n6. Invalid month '13' (out of range):")
try:
    result = parse_month("13")
    print(f"   ✓ parse_month('13') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test valid cases with ordinals
print("\n7. Valid day with ordinal '31st':")
try:
    result = parse_day("31st")
    print(f"   ✓ parse_day('31st') → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test day as integer
print("\n8. Day as integer '5':")
try:
    result = parse_day(5)
    print(f"   ✓ parse_day(5) → {result}")
except Exception as e:
    print(f"   ✗ Error: {e}")
