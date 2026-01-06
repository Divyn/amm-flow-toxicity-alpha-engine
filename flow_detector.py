"""
Flow Detector
Detects whether a price move is an isolated shock or persistent flow.
We only want to fade isolated shocks, not persistent trends.
"""
from collections import deque
from typing import Dict
import strategy_config as config

# Track recent events per pool to detect isolated shocks vs persistent flow
pool_event_history: Dict[str, deque] = {}


def is_isolated_shock(pool_id: str, direction: str, current_time: int) -> bool:
    """
    Check if this is an isolated shock vs persistent flow.
    
    An isolated shock is a single large trade that moves the price temporarily.
    Persistent flow means multiple trades in the same direction, indicating
    a real trend we shouldn't bet against.
    
    Args:
        pool_id: Unique identifier for the pool
        direction: 'AtoB' or 'BtoA' indicating swap direction
        current_time: Current timestamp in seconds
        
    Returns:
        True if isolated (good to fade), False if persistent (avoid)
    """
    # Initialize history for this pool if needed
    if pool_id not in pool_event_history:
        pool_event_history[pool_id] = deque(maxlen=10)
    
    history = pool_event_history[pool_id]
    
    # Remove events older than our detection window
    recent_events = [
        event for event in history
        if current_time - event['time'] < config.FLOW_DETECTION_WINDOW_SECONDS
    ]
    
    # Count how many events in the same direction happened recently
    same_direction_count = sum(
        1 for event in recent_events
        if event['direction'] == direction
    )
    
    # Update history with this new event
    pool_event_history[pool_id] = deque(recent_events, maxlen=10)
    pool_event_history[pool_id].append({
        'direction': direction,
        'time': current_time
    })
    
    # Isolated if very few (or no) events in same direction recently
    return same_direction_count <= config.MAX_SAME_DIRECTION_EVENTS

