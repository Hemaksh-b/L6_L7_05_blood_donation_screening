import pytest
from blood_donation_screening import process_donor_cohort, verify_storage_centrifuge


def make_cohort(donors, registered=True, ctype="standard", fast_track=False):
    return {
        "clinic_registered": registered,
        "type": ctype,
        "fast_track": fast_track,
        "donors": donors,
    }


GOOD = {"age": 25, "weight_kg": 65, "hb": 14.0}


# ================= process_donor_cohort =================

# --- input validation: both halves of the `or` ---
def test_single_accepted_donor():
    result = process_donor_cohort([make_cohort([GOOD])], 450)
    assert result["collected_ml"] == 450
    assert result["status"] == "ACCEPTED"


def test_invalid_cohorts_not_list():
    with pytest.raises(ValueError):
        process_donor_cohort("not a list", 450)


def test_invalid_volume_zero():
    with pytest.raises(ValueError):
        process_donor_cohort([], 0)


def test_invalid_volume_negative():
    with pytest.raises(ValueError):
        process_donor_cohort([], -10)


# --- outer loop: never runs / cohort skipped ---
def test_empty_cohort_list():
    assert process_donor_cohort([], 450) == {"collected_ml": 0, "status": "ZERO_YIELD"}


def test_unregistered_clinic_skipped():
    result = process_donor_cohort([make_cohort([GOOD], registered=False)], 450)
    assert result == {"collected_ml": 0, "status": "ZERO_YIELD"}


def test_missing_clinic_registered_key_defaults_to_skip():
    result = process_donor_cohort([{"donors": [GOOD]}], 450)
    assert result["status"] == "ZERO_YIELD"


# --- inner loop: no donors / defaults via .get ---
def test_cohort_with_no_donors():
    result = process_donor_cohort([make_cohort([])], 450)
    assert result["status"] == "ZERO_YIELD"


def test_cohort_missing_donors_and_type_keys():
    result = process_donor_cohort([{"clinic_registered": True}], 450)
    assert result["status"] == "ZERO_YIELD"


def test_donor_with_missing_fields_is_deferred():
    result = process_donor_cohort([make_cohort([{}])], 450)
    assert result["status"] == "ZERO_YIELD"


# --- `age < 17 or weight < 50` : each condition alone, boundaries ---
def test_underage_donor_deferred():
    d = {"age": 16, "weight_kg": 65, "hb": 14.0}
    assert process_donor_cohort([make_cohort([d])], 450)["status"] == "ZERO_YIELD"


def test_age_boundary_17_accepted():
    d = {"age": 17, "weight_kg": 65, "hb": 14.0}
    assert process_donor_cohort([make_cohort([d])], 450)["collected_ml"] == 450


def test_underweight_donor_deferred():
    d = {"age": 30, "weight_kg": 49, "hb": 14.0}
    assert process_donor_cohort([make_cohort([d])], 450)["status"] == "ZERO_YIELD"


def test_weight_boundary_50_accepted():
    d = {"age": 30, "weight_kg": 50, "hb": 14.0}
    assert process_donor_cohort([make_cohort([d])], 450)["collected_ml"] == 450


# --- hemoglobin branches ---
def test_hb_low_standard_cohort_continues():
    low = {"age": 30, "weight_kg": 70, "hb": 12.4}
    result = process_donor_cohort([make_cohort([low, GOOD])], 450)
    assert result["collected_ml"] == 450
    assert result["status"] == "ACCEPTED"


def test_hb_boundary_12_5_accepted():
    d = {"age": 30, "weight_kg": 70, "hb": 12.5}
    assert process_donor_cohort([make_cohort([d])], 450)["collected_ml"] == 450


def test_hb_low_high_altitude_resets_total_and_breaks():
    low = {"age": 30, "weight_kg": 70, "hb": 11.0}
    result = process_donor_cohort(
        [make_cohort([GOOD, low, GOOD], ctype="high_altitude")], 450
    )
    assert result == {"collected_ml": 0, "status": "ZERO_YIELD"}


def test_high_altitude_cohort_with_normal_hb_not_reset():
    result = process_donor_cohort([make_cohort([GOOD], ctype="high_altitude")], 450)
    assert result["collected_ml"] == 450


def test_hb_high_deferred():
    d = {"age": 30, "weight_kg": 70, "hb": 18.1}
    assert process_donor_cohort([make_cohort([d])], 450)["status"] == "ZERO_YIELD"


def test_hb_boundary_18_accepted():
    d = {"age": 30, "weight_kg": 70, "hb": 18.0}
    assert process_donor_cohort([make_cohort([d])], 450)["collected_ml"] == 450


# --- fast_track both ways ---
def test_fast_track_bonus_added():
    result = process_donor_cohort([make_cohort([GOOD], fast_track=True)], 450)
    assert result["collected_ml"] == 500
    assert result["status"] == "ACCEPTED"


def test_fast_track_applies_after_high_altitude_break():
    low = {"age": 30, "weight_kg": 70, "hb": 11.0}
    result = process_donor_cohort(
        [make_cohort([low], ctype="high_altitude", fast_track=True)], 450
    )
    assert result == {"collected_ml": 50, "status": "ACCEPTED"}


def test_multiple_cohorts_accumulate():
    result = process_donor_cohort([make_cohort([GOOD]), make_cohort([GOOD])], 300)
    assert result["collected_ml"] == 600


# --- final status branches ---
def test_deferral_count_exactly_4_not_high():
    bad = {"age": 10, "weight_kg": 65, "hb": 14.0}
    result = process_donor_cohort([make_cohort([GOOD, bad, bad, bad, bad])], 450)
    assert result["status"] == "ACCEPTED"


def test_high_deferral_with_five_deferrals():
    bad = {"age": 10, "weight_kg": 65, "hb": 14.0}
    result = process_donor_cohort([make_cohort([GOOD, bad, bad, bad, bad, bad])], 450)
    assert result == {"collected_ml": 450, "status": "HIGH_DEFERRAL"}


# ================= verify_storage_centrifuge =================
def test_centrifuge_no_data_empty_list():
    assert verify_storage_centrifuge([]) == "NO_DATA"


def test_centrifuge_no_data_none():
    assert verify_storage_centrifuge(None) == "NO_DATA"


def test_centrifuge_abort_on_two_consecutive_drops():
    assert verify_storage_centrifuge([[3500, 2900, 2800]]) == "ABORT_SPIN"


def test_centrifuge_single_drop_then_recovery_resets_streak():
    assert verify_storage_centrifuge([[3500, 2900, 3200, 2900, 3300]]) == "STABLE"


def test_centrifuge_rpm_boundary_3000_is_ok():
    assert verify_storage_centrifuge([[3000, 3000, 3000]]) == "STABLE"


def test_centrifuge_empty_run_then_stable():
    assert verify_storage_centrifuge([[], [3500]]) == "STABLE"


def test_centrifuge_second_run_aborts():
    assert verify_storage_centrifuge([[3500, 3500], [2000, 2000]]) == "ABORT_SPIN"


def test_centrifuge_streak_resets_between_runs():
    # one drop at end of run 1 and one at start of run 2 must NOT abort
    assert verify_storage_centrifuge([[3500, 2900], [2900, 3500]]) == "STABLE"
