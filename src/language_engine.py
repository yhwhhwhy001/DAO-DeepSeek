"""Language Engine — enhanced SIGNAL communication and stats tracking."""


def build_signal(channel: int, symbols: list[str]) -> dict:
    return {"channel": channel, "symbols": symbols[-3:]}


class LanguageEngine:
    def __init__(self):
        self._total_signals = 0
        self._cross_lineage = 0
        self._symbol_send_counts: dict[str, int] = {}
        self._channel_usage: dict[int, int] = {}
        self._behavior_changes = 0

    def record_send(self, sender_id: str, receiver_id: str,
                    channel: int, symbols: list[str],
                    same_lineage: bool) -> None:
        self._total_signals += 1
        if not same_lineage:
            self._cross_lineage += 1
        for s in symbols:
            self._symbol_send_counts[s] = self._symbol_send_counts.get(s, 0) + 1
        self._channel_usage[channel] = self._channel_usage.get(channel, 0) + 1

    def record_behavior_change(self) -> None:
        self._behavior_changes += 1

    def get_stats(self) -> dict:
        total = max(self._total_signals, 1)
        top_symbol = max(self._symbol_send_counts, key=self._symbol_send_counts.get) if self._symbol_send_counts else "N/A"
        top_channel = max(self._channel_usage, key=self._channel_usage.get) if self._channel_usage else 0
        return {
            "total_signals": self._total_signals,
            "cross_lineage": self._cross_lineage,
            "cross_lineage_pct": self._cross_lineage / total * 100,
            "top_symbol": top_symbol,
            "top_channel": top_channel,
            "behavior_change_pct": self._behavior_changes / total * 100,
        }
