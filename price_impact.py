"""
Price Impact Calculator
Calculates the price impact of swaps based on slippage tiers.
"""
from typing import Dict, Optional, Tuple
from utils import safe_to_numeric
import strategy_config as config


def calculate_price_impact(pool_event: Dict) -> Optional[Tuple[float, str, float]]:
    """
    Calculate price impact from slippage tiers.
    
    This function looks at the pool's price table to find swaps that cause
    significant price movement. It checks both directions (AtoB and BtoA)
    and finds the largest swap that fits within our impact range.
    
    Args:
        pool_event: Pool event dictionary containing price table and liquidity
        
    Returns:
        Tuple of (impact_basis_points, direction, swap_size) or None if no valid impact found
        - impact_basis_points: How much the price moved (in basis points, 100 = 1%)
        - direction: 'AtoB' or 'BtoA' indicating swap direction
        - swap_size: Size of the swap that caused this impact
    """
    pool_price_table = pool_event.get('PoolPriceTable')
    if not pool_price_table:
        return None
    
    liquidity = pool_event.get('Liquidity', {})
    amount_a = safe_to_numeric(liquidity.get('AmountCurrencyA', 0))
    amount_b = safe_to_numeric(liquidity.get('AmountCurrencyB', 0))
    
    if amount_a == 0 or amount_b == 0:
        return None
    
    # Check AtoB direction (selling A, buying B)
    impact = _check_direction(
        pool_price_table, 'AtoB', amount_a, amount_b
    )
    if impact:
        return impact
    
    # Check BtoA direction (selling B, buying A)
    impact = _check_direction(
        pool_price_table, 'BtoA', amount_a, amount_b
    )
    if impact:
        return impact
    
    return None


def _check_direction(
    pool_price_table: Dict,
    direction: str,
    amount_a: float,
    amount_b: float
) -> Optional[Tuple[float, str, float]]:
    """
    Check price impact for a specific direction (AtoB or BtoA).
    
    Args:
        pool_price_table: Price table from pool event
        direction: 'AtoB' or 'BtoA'
        amount_a: Liquidity of currency A
        amount_b: Liquidity of currency B
        
    Returns:
        Tuple of (impact_basis_points, direction, swap_size) or None
    """
    prices_key = f'{direction}Prices'
    mid_price_key = f'{direction}Price'
    
    price_tiers = pool_price_table.get(prices_key, [])
    if not price_tiers:
        return None
    
    # Start from largest swaps (end of list) and work backwards
    for tier in reversed(price_tiers):
        slippage_bp = safe_to_numeric(tier.get('SlippageBasisPoints', 0))
        max_amount_in = safe_to_numeric(tier.get('MaxAmountIn', 0))
        price = safe_to_numeric(tier.get('Price', 1.0))
        
        # Check if impact is within our acceptable range
        if not (config.MIN_IMPACT_BASIS_POINTS <= slippage_bp <= config.MAX_IMPACT_BASIS_POINTS):
            continue
        
        # Calculate impact as deviation from mid price
        mid_price = safe_to_numeric(pool_price_table.get(mid_price_key, 1.0))
        if mid_price == 0:
            continue
        
        # Impact = how much price deviates from mid price
        impact = abs(1.0 - (price / mid_price)) * 10000  # Convert to basis points
        
        # Check if swap size is significant relative to liquidity
        # For AtoB, we check against A liquidity; for BtoA, against B liquidity
        base_liquidity = amount_a if direction == 'AtoB' else amount_b
        liquidity_ratio = max_amount_in / base_liquidity if base_liquidity > 0 else 0
        
        if liquidity_ratio >= config.MIN_LIQUIDITY_RATIO:
            return (impact, direction, max_amount_in)
    
    return None

