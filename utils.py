from typing import Dict, Union


def safe_to_numeric(value: Union[str, int, float]) -> Union[int, float]:
    """
    Safely convert a value to numeric type (int or float).
    
    Args:
        value: Value that might be string, int, or float
        
    Returns:
        Numeric value (int or float)
    """
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        # Try hex conversion first (for hex strings)
        if value.startswith('0x') or (len(value) > 0 and all(c in '0123456789abcdefABCDEF' for c in value)):
            try:
                return int(value, 16)
            except ValueError:
                pass
        # Try regular int/float conversion
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
    return 0


def get_currency_decimals(pool_event: Dict, currency: str) -> int:
    """
    Get decimals for a currency from pool event.
    
    Args:
        pool_event: Pool event dictionary
        currency: 'A' or 'B' to specify which currency
        
    Returns:
        Number of decimals (default 18 if not found)
    """
    pool = pool_event.get('Pool', {})
    if currency == 'A':
        currency_obj = pool.get('CurrencyA', {})
    else:
        currency_obj = pool.get('CurrencyB', {})
    
    return currency_obj.get('Decimals', 18)


def apply_decimals(amount: float, decimals: int) -> float:
    """
    Convert amount from smallest unit to human-readable format.
    
    Args:
        amount: Amount in smallest unit
        decimals: Number of decimals
        
    Returns:
        Amount in human-readable format
    """
    if amount == 0:
        return 0.0
    return amount / (10 ** decimals)


def format_amount(amount: float, decimals: int, precision: int = 2) -> str:
    """
    Format amount with decimals applied and specified precision.
    
    Args:
        amount: Amount in smallest unit
        decimals: Number of decimals
        precision: Decimal places for display
        
    Returns:
        Formatted string
    """
    human_readable = apply_decimals(amount, decimals)
    return f"{human_readable:,.{precision}f}"

