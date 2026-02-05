"""Message parser for transaction format: AMOUNT/DESCRIPTION"""

from decimal import Decimal, InvalidOperation


def parse_transaction_message(message: str) -> dict | None:
    """
    Parse transaction message in format: AMOUNT/DESCRIPTION

    Examples:
        - "50/caffè al bar" → {'amount': Decimal('50.00'), 'description': 'caffè al bar'}
        - "125.50/spesa settimanale" → {'amount': Decimal('125.50'), 'description': 'spesa settimanale'}
        - "15,99/libro" → {'amount': Decimal('15.99'), 'description': 'libro'}

    Returns:
        dict with 'amount' (Decimal) and 'description' (str), or None if invalid
    """
    if not message or not isinstance(message, str):
        return None

    message = message.strip()

    # Check for separator
    if "/" not in message:
        return None

    # Split on first occurrence only (description might contain /)
    parts = message.split("/", maxsplit=1)
    if len(parts) != 2:
        return None

    amount_str, description = parts
    amount_str = amount_str.strip()
    description = description.strip()

    # Validate description
    if not description or len(description) > 200:
        return None

    # Parse amount (handle both comma and dot as decimal separator)
    # Remove currency symbols (€, $, etc.) and spaces
    amount_str = amount_str.replace("€", "").replace("$", "").replace(" ", "")
    amount_str = amount_str.replace(",", ".")

    try:
        amount = Decimal(amount_str)
    except (InvalidOperation, ValueError):
        return None

    # Validate amount (must be positive and non-zero)
    if amount <= 0:
        return None

    return {
        "amount": amount.quantize(Decimal("0.01")),
        "description": description,
    }
