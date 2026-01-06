"""
Position Sizing Calculator
Calculates appropriate position sizes based on liquidity and price impact.
"""
from typing import Dict
from utils import get_currency_decimals, safe_to_numeric
import strategy_config as config


def calculate_position_size(
    pool_event: Dict,
    impact_bp: float,
    fade_direction: str
) -> float:
    """
    Calculate position size based on liquidity and price impact.
    
    The position size is:
    - Based on available liquidity (we don't want to be too large)
    - Inversely proportional to impact (higher impact = smaller position)
    - Never below a minimum threshold
    
    Args:
        pool_event: Pool event dictionary
        impact_bp: Price impact in basis points
        fade_direction: Direction of fade trade ('AtoB' or 'BtoA')
        
    Returns:
        Position size in smallest unit (raw amount) of the asset being bought
    """
    liquidity = pool_event.get('Liquidity', {})
    amount_a = safe_to_numeric(liquidity.get('AmountCurrencyA', 0))
    amount_b = safe_to_numeric(liquidity.get('AmountCurrencyB', 0))
    
    # Determine which currency we're buying and its liquidity
    if fade_direction == 'BtoA':
        # Fading by buying A, so position size is in A
        base_liquidity = amount_a
        decimals = get_currency_decimals(pool_event, 'A')
    else:  # fade_direction == 'AtoB'
        # Fading by buying B, so position size is in B
        base_liquidity = amount_b
        decimals = get_currency_decimals(pool_event, 'B')
    
    if base_liquidity == 0:
        return 0.0
    
    # Size inversely proportional to impact
    # Higher impact = more risky = smaller position
    # Formula: 1 / (1 + impact/1000) with minimum of 0.1
    # This means:
    # - 100 bps (1%) impact → factor = 0.91 (91% of max)
    # - 1000 bps (10%) impact → factor = 0.5 (50% of max)
    # - 10000 bps (100%) impact → factor = 0.09 (9% of max, but capped at 0.1)
    impact_factor = max(0.1, 1.0 / (1.0 + impact_bp / 1000.0))
    
    # Base position size = liquidity * max ratio * impact factor
    position_size_raw = base_liquidity * config.MAX_POSITION_SIZE_RATIO * impact_factor
    
    # Apply minimum position size
    min_position_size_raw = config.MIN_POSITION_SIZE * (10 ** decimals)
    
    final_size = max(position_size_raw, min_position_size_raw)
    
    return final_size

