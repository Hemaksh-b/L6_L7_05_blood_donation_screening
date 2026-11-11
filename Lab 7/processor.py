import math


def validate_blood_type(blood_code):
    """
    Standardizes blood group and Rh factor (e.g. 'O+', 'AB-').
    Handles unexpected, malformed, or None inputs safely without crashing.
    """
    if not isinstance(blood_code, str):
        return "Invalid blood type"

    cleaned = blood_code.strip().upper()
    if len(cleaned) < 2:
        return "Invalid blood type"

    antigen = cleaned[:-1]
    rh_char = cleaned[-1]
    valid_antigens = {"A", "B", "AB", "O"}
    rh_map = {"+": "Positive", "-": "Negative"}

    if antigen not in valid_antigens or rh_char not in rh_map:
        return "Invalid blood type"

    return f"{antigen} {rh_map[rh_char]}"


def calculate_pulse_pressure(bp_string):
    """
    Calculates pulse pressure (systolic - diastolic) and arterial ratio.
    Handles unexpected, malformed, zero-division, or None inputs safely.
    """
    if not isinstance(bp_string, str):
        return "Invalid BP input"

    parts = bp_string.strip().split('/')
    if len(parts) != 2:
        return "Invalid BP format"

    sys_str, dia_str = parts[0].strip(), parts[1].strip()
    try:
        systolic = int(sys_str)
        diastolic = int(dia_str)
        if systolic <= 0 or diastolic <= 0:
            return "Invalid BP values"
        pulse_diff = systolic - diastolic
        ratio = round(systolic / diastolic, 2)
    except (ValueError, ZeroDivisionError, OverflowError):
        return "Invalid BP values"

    return f"Diff: {pulse_diff}, Ratio: {ratio}"


def parse_donor_registry(donor_entry):
    """
    Parses pipe-delimited record: 'DonorID|WeightKg|Hemoglobin'.
    Handles unexpected, malformed, NaN/Inf, or None inputs safely.
    """
    if not isinstance(donor_entry, str):
        return "Invalid donor record"

    fields = donor_entry.split('|')
    if len(fields) != 3:
        return "Invalid donor record format"

    donor_id = fields[0].strip()
    if not donor_id:
        return "Invalid donor ID"

    try:
        weight = float(fields[1].strip())
        hemoglobin = float(fields[2].strip())
    except (ValueError, OverflowError):
        return "Invalid donor metrics"

    if not (math.isfinite(weight) and math.isfinite(hemoglobin)):
        return "Invalid donor metrics"
    if weight <= 0 or hemoglobin <= 0:
        return "Invalid donor metrics"

    eligible = weight >= 50.0 and hemoglobin >= 12.5
    return f"Donor {donor_id}: {'Eligible' if eligible else 'Deferred'}"


def main():
    print("==== Running validate_blood_type ====")
    b_input = input("Enter blood type (e.g. A+, O-, AB+): ")
    print("Validated:", validate_blood_type(b_input))

    print("\n==== Running calculate_pulse_pressure ====")
    bp_input = input("Enter BP (e.g. 120/80): ")
    print("BP Metrics:", calculate_pulse_pressure(bp_input))

    print("\n==== Running parse_donor_registry ====")
    d_input = input("Enter record (ID|Weight|Hemoglobin): ")
    print("Status:", parse_donor_registry(d_input))

if __name__ == "__main__":
    main()