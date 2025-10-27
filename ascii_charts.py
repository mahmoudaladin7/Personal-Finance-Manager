from __future__ import annotations
from typing import List, Tuple
from decimal import Decimal

def hbar_chart(pairs: List[Tuple[str, Decimal]], width: int = 40) -> List[str]:
   
    if not pairs:
        return ["(no data)"]
    max_val = max((v for _, v in pairs), default=Decimal("0"))
    if max_val <= 0:
        scale = Decimal("0")
    else:
        scale = Decimal(width) / max_val

    lines = []
    for label, val in pairs:
        n = int((val * scale).to_integral_value(rounding="ROUND_FLOOR"))
        bar = "█" * max(0, n)
        lines.append(f"{label:>12} | {bar} {val}")
    return lines
