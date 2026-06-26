"""Bolum maliyet takibi: Kie kredi bakiyesi deltasi + LLM token maliyeti.

Kie tarafi bakiye farkiyla olculur; negatif/okunamayan delta durustce None.
LLM tarafi brain.client.USAGE_LOG'dan toplanir.
"""
from brain import client as brain_client

# MTok basina (input_usd, output_usd). Cache yazimi 1.25x input, okumasi 0.1x input.
PRICE_PER_MTOK = {
    "opus-4-8": (5.0, 25.0),
    "sonnet": (3.0, 15.0),
    "haiku": (1.0, 5.0),
}
DEFAULT_PRICE = (5.0, 25.0)


def _price_for(model: str):
    for key, price in PRICE_PER_MTOK.items():
        if key in (model or ""):
            return price
    return DEFAULT_PRICE


class CostTracker:
    def __init__(self, omni_client, credits_per_usd: float):
        self.omni = omni_client
        self.credits_per_usd = float(credits_per_usd)
        self.credits_start = None
        self._usage_start_idx = 0

    def _read_balance(self):
        try:
            balance = self.omni.get_credit_balance()
            return float(balance) if balance is not None else None
        except Exception:
            return None

    def start(self) -> None:
        self._usage_start_idx = len(brain_client.USAGE_LOG)
        self.credits_start = self._read_balance()

    def finish(self) -> dict:
        credits_end = self._read_balance()

        credits_spent = None
        if self.credits_start is not None and credits_end is not None:
            delta = self.credits_start - credits_end
            if delta >= 0:
                credits_spent = delta

        kie_usd = None
        if credits_spent is not None and self.credits_per_usd > 0:
            kie_usd = round(credits_spent / self.credits_per_usd, 4)

        llm_input = llm_output = 0
        llm_usd = 0.0
        for entry in brain_client.USAGE_LOG[self._usage_start_idx:]:
            in_price, out_price = _price_for(entry.get("model", ""))
            inp = entry.get("input_tokens", 0)
            out = entry.get("output_tokens", 0)
            cache_write = entry.get("cache_creation_input_tokens", 0)
            cache_read = entry.get("cache_read_input_tokens", 0)
            llm_input += inp + cache_write + cache_read
            llm_output += out
            llm_usd += (
                inp * in_price
                + cache_write * in_price * 1.25
                + cache_read * in_price * 0.1
                + out * out_price
            ) / 1_000_000

        return {
            "credits_start": self.credits_start,
            "credits_end": credits_end,
            "credits_spent": credits_spent,
            "kie_usd": kie_usd,
            "llm_input_tokens": llm_input,
            "llm_output_tokens": llm_output,
            "llm_usd": round(llm_usd, 4),
        }
