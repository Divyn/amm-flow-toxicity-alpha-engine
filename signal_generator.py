"""
Signal Generator
Creates and validates trading signals based on pool events.
"""
import time
from typing import Dict, Optional, Tuple
from utils import get_currency_decimals
from price_impact import calculate_price_impact
from flow_detector import is_isolated_shock
from position_sizing import calculate_position_size
import strategy_config as config

# Track active positions to avoid duplicate trades
active_positions: Dict[str, Dict] = {}


def should_fade(pool_event: Dict, impact_data: Tuple[float, str, float]) -> bool:
    """
    Decide if we should fade (bet against) this price move.
    
    We fade when:
    1. The move is an isolated shock (not persistent flow)
    2. We don't already have a position in this pool
    
    Args:
        pool_event: Pool event dictionary
        impact_data: Tuple of (impact_bp, direction, swap_size)
        
    Returns:
        True if we should fade, False otherwise
    """
    impact_bp, direction, swap_size = impact_data
    
    pool = pool_event.get('Pool', {})
    pool_id = pool.get('PoolId', '')
    
    if not pool_id:
        return False
    
    # Get event timestamp
    tx_header = pool_event.get('TransactionHeader', {})
    event_time = tx_header.get('Time', 0) // 1_000_000_000  # Convert nanoseconds to seconds
    
    # Check if this is an isolated shock (not persistent flow)
    if not is_isolated_shock(pool_id, direction, event_time):
        print(f"[SKIP] Persistent flow detected for {pool_id}, not fading")
        return False
    
    # Check if we already have a position in this pool
    if pool_id in active_positions:
        print(f"[SKIP] Active position exists for {pool_id}")
        return False
    
    return True


def create_fade_signal(
    pool_event: Dict,
    impact_data: Tuple[float, str, float]
) -> Dict:
    """
    Create a fade signal with all entry details.
    
    A fade signal means we're betting the price will reverse after a sudden move.
    We take the opposite side of the aggressive swap.
    
    Args:
        pool_event: Pool event dictionary
        impact_data: Tuple of (impact_bp, direction, swap_size)
        
    Returns:
        Dictionary containing all signal details:
        - pool_id, currencies, directions
        - position size and entry timing
        - stop loss and take profit levels
    """
    impact_bp, direction, swap_size = impact_data
    
    pool = pool_event.get('Pool', {})
    pool_id = pool.get('PoolId', '')
    currency_a = pool.get('CurrencyA', {})
    currency_b = pool.get('CurrencyB', {})
    
    # Determine fade direction (opposite of the swap)
    # If swap is AtoB (selling A), we fade by buying A (BtoA)
    # If swap is BtoA (selling B), we fade by buying B (AtoB)
    fade_direction = 'BtoA' if direction == 'AtoB' else 'AtoB'
    
    # Calculate position size
    position_size = calculate_position_size(pool_event, impact_bp, fade_direction)
    
    # Get decimals for proper formatting
    decimals_a = get_currency_decimals(pool_event, 'A')
    decimals_b = get_currency_decimals(pool_event, 'B')
    
    # Determine which currency's decimals to use
    if direction == 'AtoB':
        swap_decimals = decimals_a
    else:
        swap_decimals = decimals_b
    
    # Position size decimals depend on what we're buying
    if fade_direction == 'BtoA':
        position_decimals = decimals_a  # Buying A
    else:
        position_decimals = decimals_b  # Buying B
    
    signal = {
        'pool_id': pool_id,
        'pool_address': pool.get('SmartContract', ''),
        'currency_a': currency_a.get('Symbol', ''),
        'currency_b': currency_b.get('Symbol', ''),
        'swap_direction': direction,
        'fade_direction': fade_direction,
        'impact_basis_points': impact_bp,
        'swap_size': swap_size,  # Raw amount
        'swap_size_decimals': swap_decimals,
        'position_size': position_size,  # Raw amount
        'position_size_decimals': position_decimals,
        'entry_time': time.time() + config.WAIT_TIME_SECONDS,  # Wait before entry
        'stop_loss_bp': config.STOP_LOSS_BASIS_POINTS,
        'take_profit_bp': config.TAKE_PROFIT_BASIS_POINTS,
        'status': 'pending'
    }
    
    return signal


def get_active_positions() -> Dict[str, Dict]:
    """
    Get all active positions.
    
    Returns:
        Dictionary mapping pool_id to position signal
    """
    return active_positions


def add_position(pool_id: str, signal: Dict):
    """
    Add a new position to tracking.
    
    Args:
        pool_id: Pool identifier
        signal: Signal dictionary
    """
    active_positions[pool_id] = signal


def has_position(pool_id: str) -> bool:
    """
    Check if we have an active position in a pool.
    
    Args:
        pool_id: Pool identifier
        
    Returns:
        True if position exists, False otherwise
    """
    return pool_id in active_positions

