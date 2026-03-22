def build_signal_signature(symbol: str, side: str, family: str, rounded_entry: float) -> str:
    return f"{symbol}|{side}|{family}|{rounded_entry}"
