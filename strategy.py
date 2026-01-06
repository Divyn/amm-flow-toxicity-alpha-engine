"""
Main Trading Strategy
Orchestrates the fade strategy: waits for sudden price jumps, bets they won't last,
trades with strict risk limits, and exits quickly.
"""
from typing import Dict
from bitquery import BitqueryStream
from utils import format_amount, get_currency_decimals
from price_impact import calculate_price_impact
from signal_generator import should_fade, create_fade_signal, add_position
from position_manager import monitor_positions
import strategy_config as config


def process_pool_event(pool_event: Dict):
    """
    Process a single pool event and generate trading signals.
    
    This is the main event processing function that:
    1. Calculates price impact
    2. Decides if we should fade
    3. Creates and stores the signal
    
    Args:
        pool_event: Pool event dictionary from Bitquery stream
    """
    pool = pool_event.get('Pool', {})
    pool_id = pool.get('PoolId', '')
    
    if not pool_id:
        return
    
    # Calculate price impact
    impact_data = calculate_price_impact(pool_event)
    
    if not impact_data:
        return
    
    impact_bp, direction, swap_size = impact_data
    
    # Get decimals and symbol for display
    if direction == 'AtoB':
        swap_decimals = get_currency_decimals(pool_event, 'A')
        swap_symbol = pool.get('CurrencyA', {}).get('Symbol', 'A')
    else:
        swap_decimals = get_currency_decimals(pool_event, 'B')
        swap_symbol = pool.get('CurrencyB', {}).get('Symbol', 'B')
    
    print(f"\n[EVENT] Pool: {pool_id}")
    print(f"  Direction: {direction}")
    print(f"  Impact: {impact_bp:.2f} bps")
    print(f"  Swap Size: {format_amount(swap_size, swap_decimals)} {swap_symbol}")
    
    # Check if we should fade
    if should_fade(pool_event, impact_data):
        signal = create_fade_signal(pool_event, impact_data)
        
        # Determine position currency symbol for display
        if signal['fade_direction'] == 'AtoB':
            position_symbol = signal['currency_b']  # Buying B
            position_decimals = get_currency_decimals(pool_event, 'B')
        else:  # fade_direction == 'BtoA'
            position_symbol = signal['currency_a']  # Buying A
            position_decimals = get_currency_decimals(pool_event, 'A')
        
        print(f"\n[FADE SIGNAL]")
        print(f"  Pool: {signal['currency_a']}/{signal['currency_b']}")
        print(f"  Fade Direction: {signal['fade_direction']}")
        print(f"  Position Size: {format_amount(signal['position_size'], position_decimals)} {position_symbol}")
        print(f"  Entry Time: {time.ctime(signal['entry_time'])}")
        print(f"  Stop Loss: {signal['stop_loss_bp']} bps")
        print(f"  Take Profit: {signal['take_profit_bp']} bps")
        
        # Store as pending position
        add_position(pool_id, signal)
        
        return signal
    
    return None


def handle_message(data_dict: Dict):
    """
    Handle incoming message from Bitquery stream.
    
    Args:
        data_dict: Parsed message dictionary from Kafka
    """
    # Process pool events
    pool_events = data_dict.get('PoolEvents', [])
    for pool_event in pool_events:
        # Monitor existing positions first
        monitor_positions(pool_event)
        
        # Process new event for potential signals
        process_pool_event(pool_event)


def main():
    """Main strategy execution."""
    print("Strategy initialized. Listening for pool events...")
    print(f"Configuration:")
    print(f"  Min Impact: {config.MIN_IMPACT_BASIS_POINTS} bps")
    print(f"  Max Impact: {config.MAX_IMPACT_BASIS_POINTS} bps")
    print(f"  Wait Time: {config.WAIT_TIME_SECONDS}s")
    print(f"  Max Position Size: {config.MAX_POSITION_SIZE_RATIO*100}% of liquidity")
    
    stream = BitqueryStream(topic='eth.dexpools.proto', group_id_suffix='strategy')
    
    try:
        while True:
            data_dict = stream.poll()
            if data_dict is not None:
                handle_message(data_dict)
    except KeyboardInterrupt:
        print("\nStopping strategy...")
        from signal_generator import get_active_positions
        active_positions = get_active_positions()
        print(f"Active positions: {len(active_positions)}")
    finally:
        stream.close()


if __name__ == '__main__':
    import time
    main()
