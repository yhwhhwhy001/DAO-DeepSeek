"""Utility Engine — Q-table, SARSA update, reward computation, inheritance."""
from collections import OrderedDict

ALPHA = 0.1
GAMMA = 0.9
MAX_Q_STATES = 200
Q_INHERIT_DECAY = 0.5
MAX_Q_INHERIT = 50
MIN_Q_INHERIT = 10


def compute_reward(
    energy_delta: float = 0.0,
    survived: bool = True,
    structure_joined: bool = False,
    structure_lost: bool = False,
    near_death_recovery: bool = False,
    signals_received: int = 0,
) -> float:
    r = 0.0
    if survived:
        r += 0.1
    r += energy_delta * 2.0
    if structure_joined:
        r += 0.5
    if structure_lost:
        r -= 0.3
    if near_death_recovery:
        r += 1.0
    r += signals_received * 0.2
    return r


class UtilityEngine:
    def __init__(self, max_states: int = MAX_Q_STATES):
        self._q_table: OrderedDict[str, dict[str, float]] = OrderedDict()
        self.max_states = max_states
        self._access_order: list[str] = []

    def get_q(self, state_key: str, action: str) -> float:
        return self._q_table.get(state_key, {}).get(action, 0.0)

    def update(self, state_key: str, action: str, reward: float,
               next_state_key: str, next_action: str) -> None:
        current_q = self.get_q(state_key, action)
        next_q = self.get_q(next_state_key, next_action)
        td_error = reward + GAMMA * next_q - current_q
        new_q = current_q + ALPHA * td_error

        if state_key not in self._q_table:
            self._q_table[state_key] = {}
        self._q_table[state_key][action] = new_q

        if state_key in self._access_order:
            self._access_order.remove(state_key)
        self._access_order.append(state_key)

        while len(self._q_table) > self.max_states:
            oldest = self._access_order.pop(0)
            self._q_table.pop(oldest, None)

    def create_inherited(self) -> "UtilityEngine":
        child = UtilityEngine(max_states=self.max_states)
        if not self._q_table:
            return child
        if len(self._q_table) < MIN_Q_INHERIT:
            recent_states = list(self._q_table.keys())
        else:
            recent_states = self._access_order[-MAX_Q_INHERIT:]
        for sk in recent_states:
            if sk in self._q_table:
                child._q_table[sk] = {}
                for a, v in self._q_table[sk].items():
                    child._q_table[sk][a] = v * Q_INHERIT_DECAY
        child._access_order = list(recent_states)
        return child
