class CockConfig:
    # Default values for cock size
    DEFAULT_COCK_SIZE = 5
    MAX_COCK_SIZE = 60 # 60-200 cm is most ideal (That doesn't mean the size can't go higher. It is used for correct event calculation)
    MIN_COCK_SIZE = 1

    # Cooldown time (in hours)
    COOLDOWN_HOURS = 24

    # Calculation constants
    MAX_PROB_COCK_SIZE_INCREASE = 0.95
    MIN_PROB_COCK_SIZE_INCREASE = 0.35
    SCALING_FACTOR = 0.60

    # Event durations (in moves)
    EVENT_RUBBER_DURATION = 4
    EVENT_ROCKET_MIN_DURATION = 2
    EVENT_ROCKET_MAX_DURATION = 5

    # Event probabilities
    PROB_MICRO = 0.08
    PROB_RUBBER = 0.02
    PROB_TELEPORT = 0.03
    PROB_AGING = 0.04
    PROB_ROCKET = 0.02
    PROB_MAGNETIC = 0.03
    PROB_SHRINK_RAY = 0.03
    PROB_GROWTH_SPURT = 0.06
    PROB_PHANTOM_SHRINK = 0.03
    PROB_BLACK_HOLE = 0.05
