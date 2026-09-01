

# ============================================
# PROTOTYPE 1 MW WIND TURBINE
# ============================================

RATED_POWER_MW = 1.0

CUT_IN_KMH = 3.0
RATED_SPEED_KMH = 12.0
CUT_OUT_KMH = 25.0


def wind_power_curve(speed_kmh: float) -> float:
    """
    Smooth prototype wind-turbine power curve.

    Output:
        MW per 1 MW installed capacity
    """

    # Below cut-in speed
    if speed_kmh < CUT_IN_KMH:
        return 0.0

    # Between cut-in and rated speed
    if speed_kmh < RATED_SPEED_KMH:

        normalized_speed = (
            (speed_kmh - CUT_IN_KMH)
            / (RATED_SPEED_KMH - CUT_IN_KMH)
        )

        power = (
            RATED_POWER_MW
            * normalized_speed ** 3
        )

        return min(
            max(power, 0.0),
            RATED_POWER_MW
        )

    # Rated region
    if speed_kmh <= CUT_OUT_KMH:
        return RATED_POWER_MW

    # Above cut-out: safety shutdown
    return 0.0


# ============================================
# TEST THE CURVE
# ============================================

if __name__ == "__main__":

    print("\n==============================================")
    print("      POWERFLEX BD - WIND POWER CURVE")
    print("==============================================")

    test_speeds = [
        0,
        2,
        3,
        5,
        7,
        9,
        10,
        11,
        12,
        15,
        20,
        25,
        26,
        30
    ]

    for speed in test_speeds:

        power = wind_power_curve(speed)

        print(
            f"{speed:>5.1f} km/h "
            f"-> {power:.4f} MW/MW"
        )

    print("==============================================")