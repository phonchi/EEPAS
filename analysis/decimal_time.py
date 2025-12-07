from datetime import datetime, timedelta
import numpy as np

def decimal_time_precise(year, month, day, hour=0, minute=0, second=0, start=0):
    """
    Convert year-month-day-hour-minute-second to decimal time format, handling various cases including negative seconds

    Parameters:
        year: Year (can be scalar or array)
        month: Month (can be scalar or array)
        day: Day (can be scalar or array)
        hour, minute, second: Hour, minute, second (can be scalar or array)
        start: Starting year (default is 0)

    Returns:
        Decimal time format (relative to starting year)
    """
    # Convert to numpy arrays for uniform processing
    year = np.atleast_1d(np.array(year, dtype=float))
    month = np.atleast_1d(np.array(month, dtype=float))
    day = np.atleast_1d(np.array(day, dtype=float))
    hour = np.atleast_1d(np.array(hour, dtype=float))
    minute = np.atleast_1d(np.array(minute, dtype=float))
    second = np.atleast_1d(np.array(second, dtype=float))

    # Check if input is scalar
    scalar_input = (len(year) == 1)

    # Correct month = 0 cases
    month[month == 0] = 1

    # Adjust array lengths
    n = len(year)
    if len(month) < n: month = np.resize(month, n)
    if len(day) < n: day = np.resize(day, n)
    if len(hour) < n: hour = np.resize(hour, n)
    if len(minute) < n: minute = np.resize(minute, n)
    if len(second) < n: second = np.resize(second, n)

    results = []

    for i in range(n):
        # Handle negative seconds
        # Normalize time to valid hour-minute-second
        total_seconds = int(hour[i]) * 3600 + int(minute[i]) * 60 + second[i]

        # Handle negative total seconds (subtract a day and adjust)
        days_adjust = 0
        while total_seconds < 0:
            total_seconds += 86400  # Add one day in seconds
            days_adjust -= 1  # Decrease one day

        # Recalculate hour, minute and second
        hr_int = int(total_seconds // 3600) % 24
        min_int = int((total_seconds % 3600) // 60)
        sec_int = int(total_seconds % 60)
        sec_frac = total_seconds - int(total_seconds)

        # Calculate datetime
        try:
            # Ensure date and month are valid
            day_val = max(1, int(day[i]))
            month_val = max(1, int(month[i]))

            # Create base datetime
            base_dt = datetime(int(year[i]), month_val, day_val)

            # Add day adjustment (handle date decrease due to negative seconds)
            if days_adjust != 0:
                base_dt += timedelta(days=days_adjust)

            # Add time component
            dt = datetime(
                base_dt.year, base_dt.month, base_dt.day,
                hr_int, min_int, sec_int
            )

            # Add fractional seconds
            if sec_frac > 0:
                dt += timedelta(seconds=sec_frac)

        except ValueError as e:
            print(f"Warning: Invalid date calculation for {int(year[i])}-{month_val}-{day_val}, Error: {e}")
            # Use the first day of the month as alternative, ensuring time component is valid
            try:
                dt = datetime(int(year[i]), month_val, 1, hr_int, min_int, sec_int)
                print(f"Using first day of month instead: {dt}")
            except ValueError:
                # If still fails, use the most basic valid date and time
                print(f"Fallback to basic valid date")
                dt = datetime(int(year[i]), 1, 1, 0, 0, 0)

        # Calculate the first day of the year
        year_start = datetime(int(year[i]), 1, 1)

        # Calculate days in the year (handle leap year)
        if int(year[i]) % 4 == 0 and (int(year[i]) % 100 != 0 or int(year[i]) % 400 == 0):
            days_in_year = 366
        else:
            days_in_year = 365

        # Calculate days passed from year start to now (including hour-minute-second)
        days_passed = (dt - year_start).total_seconds() / 86400

        # Calculate decimal time
        decimal_time = (year[i] - start) + days_passed / days_in_year

        results.append(decimal_time)

    # Return result (scalar or array)
    if scalar_input:
        return results[0]
    return np.array(results)

def ymd_time_precise(time, start):
    """
    Convert decimal time to year-month-day format, using datetime library

    Parameters:
        time: Decimal time (can be scalar or array)
        start: Starting year

    Returns:
        Array containing year, month, day (each row corresponds to one time point)
    """
    # Convert to numpy array for uniform processing
    time = np.atleast_1d(np.array(time, dtype=float))

    # Check if input is scalar
    scalar_input = (len(time) == 1)

    # Create result array containing year, month, day
    result = np.zeros((len(time), 3))

    for i in range(len(time)):
        try:
            # Calculate full year
            full_year = int(time[i]) + int(start)

            # Calculate fractional part of year
            year_fraction = time[i] - int(time[i])

            # Determine days in the year (handle leap year)
            if full_year % 4 == 0 and (full_year % 100 != 0 or full_year % 400 == 0):
                days_in_year = 366
            else:
                days_in_year = 365

            # Calculate days passed (including fractional part)
            days_passed = year_fraction * days_in_year

            # Separate integer days and fractional part
            days_int = int(days_passed)
            days_frac = days_passed - days_int

            # Calculate corresponding date
            target_date = datetime(full_year, 1, 1) + timedelta(days=days_int)

            # Store year-month-day result
            result[i, 0] = full_year
            result[i, 1] = target_date.month
            result[i, 2] = target_date.day

        except Exception as e:
            print(f"Warning: Error converting time {time[i]} + {start}: {e}")
            # Use default value (January 1st of current year)
            result[i, 0] = int(start)
            result[i, 1] = 1
            result[i, 2] = 1

    # Return result (scalar or array)
    if scalar_input:
        return result[0]
    return result
