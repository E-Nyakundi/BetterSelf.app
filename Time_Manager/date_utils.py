"""
Date utility functions for handling partial date input and auto-calculation.
Allows users to enter minimal date components and auto-fills the rest.
"""

from datetime import datetime, date, timedelta
import calendar


MONTH_NAMES = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12,
}

DAY_OF_WEEK_NAMES = {
    'mon': 0, 'monday': 0,
    'tue': 1, 'tuesday': 1,
    'wed': 2, 'wednesday': 2,
    'thu': 3, 'thursday': 3,
    'fri': 4, 'friday': 4,
    'sat': 5, 'saturday': 5,
    'sun': 6, 'sunday': 6,
}

ORDINAL_SUFFIXES = {
    'st': '', 'nd': '', 'rd': '', 'th': ''
}


def parse_month(month_input):
    """
    Convert month input (name or digit) to month number (1-12).
    
    Examples:
        "Feb" → 2
        "2" → 2
        "february" → 2
        "Mar" → 3
        "m" → raises error (too ambiguous - could be May or March)
    """
    if isinstance(month_input, int):
        return month_input
    
    if not month_input:
        return None
    
    month_str = str(month_input).strip().lower()
    
    # Try numeric
    if month_str.isdigit():
        m = int(month_str)
        if 1 <= m <= 12:
            return m
        raise ValueError(f"Invalid month: '{month_input}'. Month number must be 1-12.")
    
    # Try exact month name match
    if month_str in MONTH_NAMES:
        return MONTH_NAMES[month_str]
    
    # Try partial month name (at least 2 characters for safety)
    matches = []
    for key, value in MONTH_NAMES.items():
        if key.startswith(month_str):
            matches.append((key, value))
    
    if len(matches) == 1:
        return matches[0][1]
    elif len(matches) > 1:
        month_options = ', '.join([m[0].capitalize() for m in matches])
        raise ValueError(
            f"Ambiguous month: '{month_input}'. Could match: {month_options}. "
            f"Please use full or unambiguous abbreviation (e.g., 'Feb', 'Mar', 'May', 'June', 'July', 'Sept')."
        )
    else:
        raise ValueError(
            f"Invalid month: '{month_input}'. Please enter a month name (e.g., 'Feb', 'March', 'May') "
            f"or month number (1-12)."
        )


def parse_day(day_input):
    """
    Parse day input, removing ordinal suffixes and converting to int.
    
    Examples:
        "15th" → 15
        "1st" → 1
        "22nd" → 22
        15 → 15
    
    Note: Day-of-week names (Mon, Tue, etc.) are not allowed - use specific dates instead.
    """
    if isinstance(day_input, int):
        return day_input
    
    day_str = str(day_input).strip().lower()
    
    # Check if it's a day-of-week name before processing
    if day_str in DAY_OF_WEEK_NAMES or any(day_str.startswith(key) for key in DAY_OF_WEEK_NAMES.keys()):
        # Find which day name matches
        matched_day = None
        for key in DAY_OF_WEEK_NAMES.keys():
            if key.startswith(day_str) or day_str.startswith(key):
                matched_day = key
                break
        day_name = matched_day.capitalize() if matched_day else day_input
        raise ValueError(
            f"Invalid day: '{day_input}'. Day-of-week names like '{day_name}' are not allowed. "
            f"Please enter a specific date number (1-31), optionally with an ordinal suffix (1st, 2nd, 3rd, 4th, etc.)"
        )
    
    # Remove ordinal suffixes
    for suffix in ['st', 'nd', 'rd', 'th']:
        if day_str.endswith(suffix):
            day_str = day_str[:-len(suffix)]
    
    if day_str.isdigit():
        d = int(day_str)
        if 1 <= d <= 31:
            return d
    
    raise ValueError(
        f"Invalid day: '{day_input}'. Please enter a day number between 1-31, "
        f"optionally with an ordinal suffix (e.g., '15th', '1st', '22nd')."
    )


def parse_year(year_input):
    """
    Parse year input.
    
    Examples:
        "2026" → 2026
        2026 → 2026
    """
    if isinstance(year_input, int):
        return year_input
    
    year_str = str(year_input).strip()
    
    if year_str.isdigit():
        y = int(year_str)
        if 1900 <= y <= 2100:
            return y
    
    raise ValueError(f"Invalid year: {year_input}")


def add_ordinal_suffix(day):
    """
    Add ordinal suffix to a day number.
    
    Examples:
        1 → "1st"
        2 → "2nd"
        3 → "3rd"
        4 → "4th"
        21 → "21st"
        22 → "22nd"
        23 → "23rd"
        24 → "24th"
    """
    if not isinstance(day, int):
        day = int(day)
    
    if day % 100 in [11, 12, 13]:
        suffix = 'th'
    else:
        last_digit = day % 10
        if last_digit == 1:
            suffix = 'st'
        elif last_digit == 2:
            suffix = 'nd'
        elif last_digit == 3:
            suffix = 'rd'
        else:
            suffix = 'th'
    
    return f"{day}{suffix}"


def parse_partial_date(year=None, month=None, day=None):
    """
    Parse partial date input and return a complete date.
    Uses today's date to fill in missing components.
    
    Examples:
        year=2026 → date(2026, today.month, today.day)
        year=2026, month=2 → date(2026, 2, today.day)
        year=2026, month=2, day=15 → date(2026, 2, 15)
    """
    today = date.today()
    
    # Parse inputs
    y = parse_year(year) if year is not None else today.year
    m = parse_month(month) if month is not None else today.month
    d = parse_day(day) if day is not None else today.day
    
    # Validate and clamp day to valid range for month
    max_day = calendar.monthrange(y, m)[1]
    if d > max_day:
        d = max_day
    
    return date(y, m, d)


def calculate_week_number(target_date, first_entry_date):
    """
    Calculate the week number based on a first entry date.
    Week 1 is Sun-Sat of the first entry.
    
    Examples:
        If first_entry is Monday 2026-02-02:
        - Week 1 starts on Sunday 2026-02-01
        - Week 1 ends on Saturday 2026-02-07
    """
    if not first_entry_date or not target_date:
        return None
    
    # Get the Sunday of the week containing the first entry
    days_since_sunday = (first_entry_date.weekday() + 1) % 7  # Convert Mon=0 to Sun=0
    week1_start = first_entry_date - timedelta(days=days_since_sunday)
    
    # Calculate the Sunday of the week containing target_date
    days_since_sunday = (target_date.weekday() + 1) % 7
    target_sunday = target_date - timedelta(days=days_since_sunday)
    
    # Calculate week number
    if target_sunday < week1_start:
        return None  # Target is before first entry
    
    week_diff = (target_sunday - week1_start).days // 7
    return week_diff + 1


def get_week_range(week_number, first_entry_date):
    """
    Get the Sunday-Saturday date range for a given week number.
    
    Returns:
        tuple: (start_date, end_date) where start is Sunday and end is Saturday
    """
    if not first_entry_date:
        return None, None
    
    # Get the Sunday of the week containing the first entry
    days_since_sunday = (first_entry_date.weekday() + 1) % 7
    week1_start = first_entry_date - timedelta(days=days_since_sunday)
    
    # Calculate the Sunday of the target week
    target_sunday = week1_start + timedelta(weeks=week_number - 1)
    target_saturday = target_sunday + timedelta(days=6)
    
    return target_sunday, target_saturday


def format_date_display(d):
    """
    Format date for display with ordinal day suffix.
    
    Examples:
        date(2026, 2, 15) → "Feb 15th, 2026"
    """
    if not d:
        return ""
    
    day_suffix = add_ordinal_suffix(d.day)
    return d.strftime(f"%b {day_suffix}, %Y").replace(f" {d.day},", f" {day_suffix},")
