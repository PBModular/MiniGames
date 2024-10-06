class CockConfig:
    # Default values for cock size
    DEFAULT_COCK_SIZE = 5
    MAX_COCK_SIZE = 60
    MIN_COCK_SIZE = 0.1
    MAX_INCREASE = 5

    # Cooldown time (in hours)
    COOLDOWN_HOURS = 24

    # Event durations (in moves)
    EVENT_RUBBER_DURATION = 4
    EVENT_ROCKET_MIN_DURATION = 2
    EVENT_ROCKET_MAX_DURATION = 5

    # Event probabilities
    PROB_MICRO = 0.03
    PROB_RUBBER = 0.02
    PROB_TELEPORT = 0.02
    PROB_AGING = 0.04
    PROB_ROCKET = 0.01
    PROB_MAGNETIC = 0.03
    PROB_SHRINK_RAY = 1
    PROB_GROWTH_SPURT = 0.10
    PROB_PHANTOM_SHRINK = 0.05
    PROB_BLACK_HOLE = 0.08
