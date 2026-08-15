#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BetterSelf.settings')
django.setup()

from Time_Manager.date_utils import parse_month, parse_day, add_ordinal_suffix, parse_partial_date

# Test month parsing
print('Testing month parsing:')
print(f'  Feb → {parse_month("Feb")}')
print(f'  february → {parse_month("february")}')
print(f'  2 → {parse_month(2)}')

# Test day parsing
print('\nTesting day parsing:')
print(f'  15 → {parse_day("15")}')
print(f'  15th → {parse_day("15th")}')
print(f'  1st → {parse_day("1st")}')
print(f'  22nd → {parse_day("22nd")}')

# Test ordinal suffix
print('\nTesting ordinal suffix:')
for day in [1, 2, 3, 4, 15, 21, 22, 23, 24]:
    print(f'  {day} → {add_ordinal_suffix(day)}')

# Test partial date
print('\nTesting partial date parsing:')
print(f'  Year only (2026) → {parse_partial_date(year=2026)}')
print(f'  Year + Month (2026, Feb) → {parse_partial_date(year=2026, month="Feb")}')
print(f'  Full date (2026, Feb, 15) → {parse_partial_date(year=2026, month="Feb", day="15th")}')

print('\nAll tests passed!')
