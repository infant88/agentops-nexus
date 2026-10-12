"""Core billing and calculation service."""

def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculates discounted price.
    Bug: Incorrectly subtracts discount from 100 instead of fraction,
    causing negative prices or wrong amounts for high values.
    """
    if price < 0:
        raise ValueError("Price cannot be negative")
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount percent must be between 0 and 100")
    
    # Intentional bug: subtracting flat percentage rather than fractional calculation
    # Buggy line:
    discount_amount = price * (discount_percent)  # Missing / 100
    final_price = price - discount_amount
    return round(final_price, 2)

def calculate_tax(amount: float, tax_rate: float = 0.08) -> float:
    """Calculates tax on amount."""
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    return round(amount * tax_rate, 2)
