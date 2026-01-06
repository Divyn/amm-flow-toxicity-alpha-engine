"""
Position Manager
Monitors active positions and checks stop loss / take profit conditions.
"""
import time
from typing import Dict
from signal_generator import get_active_positions


def monitor_positions(current_pool_state: Dict):
    """
    Monitor active positions and check if they should be closed.
    
    This function checks:
    1. If entry time has passed (execute the trade)
    2. If stop loss or take profit has been hit (close the position)
    
    Args:
        current_pool_state: Current pool state dictionary
    """
    pool = current_pool_state.get('Pool', {})
    pool_id = pool.get('PoolId', '')
    
    active_positions = get_active_positions()
    
    if pool_id not in active_positions:
        return
    
    position = active_positions[pool_id]
    
    # Check if entry time has passed
    if time.time() < position['entry_time']:
        return  # Still waiting for entry
    
    # Mark as entered if still pending
    if position['status'] == 'pending':
        position['status'] = 'entered'
        print(f"[ENTERED] Position for {pool_id}")
        # In production, execute the trade here
    
    # Check current price vs entry price for stop loss / take profit
    # This is simplified - in production you'd track entry price and compare
    pool_price_table = current_pool_state.get('PoolPriceTable', {})
    
    # TODO: Implement actual P&L calculation and exit logic
    # For now, just log that we're monitoring
    # In production, you would:
    # 1. Get entry price from position
    # 2. Get current price from pool_price_table
    # 3. Calculate P&L in basis points
    # 4. Check if stop loss or take profit hit
    # 5. Close position if needed

