"""
Strategy Configuration
Contains all configurable parameters for the trading strategy.
"""

# Price Impact Thresholds
MIN_IMPACT_BASIS_POINTS = 50  # Minimum price impact to consider (0.5%)
MAX_IMPACT_BASIS_POINTS = 500  # Maximum impact to fade (5%)

# Liquidity Requirements
MIN_LIQUIDITY_RATIO = 0.1  # Minimum liquidity relative to swap size

# Entry Timing
WAIT_TIME_SECONDS = 2  # Wait time before entry (seconds)

# Position Sizing
MAX_POSITION_SIZE_RATIO = 0.05  # Max position size as ratio of liquidity
MIN_POSITION_SIZE = 0.01  # Minimum position size (in human-readable units)

# Risk Management
STOP_LOSS_BASIS_POINTS = 100  # Stop loss at 1% adverse move
TAKE_PROFIT_BASIS_POINTS = 50  # Take profit at 0.5% favorable move

# Flow Detection
FLOW_DETECTION_WINDOW_SECONDS = 30  # Time window to detect persistent flow
MAX_SAME_DIRECTION_EVENTS = 1  # Max events in same direction to consider isolated

