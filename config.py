class CockConfig:
    # Debug mode
    DEBUG_MODE = False  # Set to True to bypass cooldowns for testing

    # Default values for cock size
    DEFAULT_COCK_SIZE = 5.0
    MAX_COCK_SIZE = 60.0 # 60-200 cm is most ideal (That doesn't mean the size can't go higher. It is used for correct event calculation)
    MIN_COCK_SIZE = 0.1

    # Cooldown time (in hours)
    COOLDOWN_HOURS = 24

    # Calculation constants
    MAX_PROB_COCK_SIZE_INCREASE = 0.95
    MIN_PROB_COCK_SIZE_INCREASE = 0.35
    SCALING_FACTOR = 0.60

    # Event system
    PROB_ANY_SPECIAL_EVENT = 0.35

    # Event durations (in moves)
    EVENT_RUBBER_DURATION = 4
    EVENT_ROCKET_MIN_DURATION = 2
    EVENT_ROCKET_MAX_DURATION = 4
    EVENT_BORROWER_MIN_DURATION = 1
    EVENT_BORROWER_MAX_DURATION = 3
    EVENT_PHANTOM_LIMB_DURATION = 1
    EVENT_EXISTENTIAL_CRISIS_DURATION = 1
    EVENT_CONFESSION_DURATION = 1

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
    PROB_AVERAGE_RECALIBRATION = 0.025
    PROB_PHANTOM_LIMB_SYNDROME = 0.03
    PROB_BORROWER = 0.025
    PROB_EXISTENTIAL_CRISIS = 0.02
    PROB_HUMBLEBRAG_TAX = 0.02
    PROB_CONFESSION = 0.025
    PROB_RECALL_CONFESSION = 0.03
