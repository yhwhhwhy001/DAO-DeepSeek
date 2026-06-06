# Phase 7: Civilization Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Detect civilizations via community detection on the ecology network, record three-layer history, and generate mythic narratives.

**Architecture:** Civilization Engine uses Louvain community detection on EcologyNetwork, filtered by lineage diversity/shared symbols/mutualism. History Engine records individual/communal/environmental events. Myth Engine generates founder narratives, hero lineages, and belief systems.

**Tech Stack:** Python 3.14 + networkx (for Louvain community detection)

**Project Root:** `~/Documents/Claude/dao-genesis/`

---

### Task 1: Civilization Events + Civilization Engine

**Files:**
- Create: `src/civilization_engine.py`
- Create: `tests/test_civilization_engine.py`
- Modify: `src/event_bus.py` (add CIVILIZATION_BORN/EXPANDED/CONTRACTED/FALLEN)
- Modify: `requirements.txt` (add networkx)

- [ ] **Step 1: Add events + networkx dependency**

```python
# event_bus.py additions:
    CIVILIZATION_BORN = auto()
    CIVILIZATION_EXPANDED = auto()
    CIVILIZATION_CONTRACTED = auto()
    CIVILIZATION_FALLEN = auto()
```

```
# requirements.txt addition:
networkx>=3.0
```

- [ ] **Step 2: Write tests/test_civilization_engine.py**

```python
"""Tests for Civilization Engine."""
from src.civilization_engine import CivilizationEngine, Civilization


class TestCivilization:
    def test_civilization_creation(self):
        c = Civilization(id="civ_0", founder_lineage="root_A", core_structure_id="s1",
                         born_at=100)
        assert c.status == "emerging" and c.founder_lineage == "root_A"

    def test_era_transition(self):
        c = Civilization(id="civ_0", founder_lineage="root_A", core_structure_id="s1",
                         born_at=100)
        c.size_history = [3, 5, 8, 10]
        c._update_era()
        assert c.era == "expanding"


class TestCivilizationEngine:
    def test_empty_scan(self):
        eng = CivilizationEngine()
        civs = eng.scan(ecology_network=None, symbol_data={}, tick=100)
        assert civs == []

    def test_insufficient_lineages(self):
        eng = CivilizationEngine()
        # Build a small ecology network with only 2 lineages
        import networkx as nx
        G = nx.Graph()
        G.add_node("s1", lineage_root="L1")
        G.add_node("s2", lineage_root="L2")
        G.add_edge("s1", "s2", relationship="mutualism", strength=0.5)
        civs = eng.scan(ecology_network=G, symbol_data={}, tick=100)
        assert len(civs) == 0  # need >= 3 lineages

    def test_cross_tick_matching(self):
        eng = CivilizationEngine()
        old = Civilization(id="civ_0", founder_lineage="L1", core_structure_id="s1",
                          born_at=100)
        old.member_lineages = ["L1", "L2", "L3"]
        eng.civilizations = [old]
        
        new = Civilization(id="civ_1", founder_lineage="L1", core_structure_id="s1",
                          born_at=200)
        new.member_lineages = ["L1", "L2", "L4"]
        
        matched = eng._match_civilization(new)
        assert matched is not None  # overlap = 2/4 = 0.5 → match
```

- [ ] **Step 3: Write src/civilization_engine.py**

```python
"""Civilization Engine — community detection and civilization tracking."""
from dataclasses import dataclass, field
from src.event_bus import EventBus, EventType


@dataclass
class Civilization:
    id: str
    founder_lineage: str
    core_structure_id: str
    born_at: int
    died_at: int | None = None
    member_lineages: list[str] = field(default_factory=list)
    member_structures: list[str] = field(default_factory=list)
    peak_size: int = 0
    peak_tick: int = 0
    status: str = "emerging"
    shared_symbols: list[str] = field(default_factory=list)
    dominant_channel: int = 0
    era: str = "founding"
    size_history: list[int] = field(default_factory=list)

    def _update_era(self) -> None:
        if len(self.size_history) < 3:
            return
        recent = self.size_history[-3:]
        if all(recent[i] > recent[i-1] for i in range(1, len(recent))):
            self.era = "expanding"
        elif all(recent[i] < recent[i-1] for i in range(1, len(recent))):
            self.era = "declining"
        elif self.peak_size > 0 and self.size_history[-1] >= self.peak_size * 0.9:
            self.era = "golden_age"
        else:
            self.era = "stable"


class CivilizationEngine:
    def __init__(self, bus: EventBus | None = None):
        self.bus = bus
        self.civilizations: list[Civilization] = []
        self._next_id = 0

    def scan(self, ecology_network, symbol_data: dict, tick: int) -> list[Civilization]:
        """ecology_network: networkx.Graph or None"""
        if ecology_network is None or ecology_network.number_of_nodes() < 3:
            return []

        # Simple community detection: connected components
        try:
            import networkx as nx
            communities = list(nx.connected_components(ecology_network))
        except ImportError:
            return []

        new_civs = []
        for community in communities:
            if len(community) < 3:
                continue

            # Collect lineage roots
            lineages = set()
            for node in community:
                lineage = ecology_network.nodes[node].get("lineage_root", node)
                lineages.add(lineage)

            if len(lineages) < 3:
                continue

            # Check mutualism
            has_mutualism = False
            for u, v, d in ecology_network.edges(data=True):
                if u in community and v in community:
                    if d.get("relationship") == "mutualism":
                        has_mutualism = True
                        break

            if not has_mutualism:
                continue

            # Find core (highest degree)
            core = max(community, key=lambda n: ecology_network.degree(n))
            founder = ecology_network.nodes[core].get("lineage_root", core)

            civ = Civilization(
                id=f"civ_{self._next_id}",
                founder_lineage=founder,
                core_structure_id=core,
                born_at=tick,
                member_lineages=list(lineages),
                member_structures=list(community),
                peak_size=len(lineages),
                peak_tick=tick,
            )
            self._next_id += 1
            new_civs.append(civ)

        # Cross-tick matching
        for new_civ in new_civs:
            matched = self._match_civilization(new_civ)
            if matched is None:
                self.civilizations.append(new_civ)
                if self.bus:
                    self.bus.publish(EventType.CIVILIZATION_BORN, {
                        "civilization_id": new_civ.id,
                        "founder": new_civ.founder_lineage,
                        "size": len(new_civ.member_lineages),
                    })

        # Check for expansion/contraction/fallen
        for old_civ in self.civilizations:
            if old_civ.status == "fallen":
                continue
            old_civ.size_history.append(len(old_civ.member_lineages))
            if len(old_civ.size_history) > 20:
                old_civ.size_history = old_civ.size_history[-20:]
            old_civ._update_era()
            if len(old_civ.member_lineages) > old_civ.peak_size:
                old_civ.peak_size = len(old_civ.member_lineages)
                old_civ.peak_tick = tick

        return self.civilizations

    def _match_civilization(self, new_civ: Civilization) -> Civilization | None:
        for old_civ in self.civilizations:
            if old_civ.status == "fallen":
                continue
            old_set = set(old_civ.member_lineages)
            new_set = set(new_civ.member_lineages)
            if not old_set or not new_set:
                continue
            overlap = len(old_set & new_set) / len(old_set | new_set)
            if overlap >= 0.5:
                # Update old civ with new data
                old_size = len(old_civ.member_lineages)
                old_civ.member_lineages = list(new_set | old_set)
                old_civ.member_structures = new_civ.member_structures
                old_civ.shared_symbols = new_civ.shared_symbols
                new_size = len(old_civ.member_lineages)
                if self.bus and new_size > old_size:
                    self.bus.publish(EventType.CIVILIZATION_EXPANDED, {
                        "civilization_id": old_civ.id,
                        "new_lineage": list(new_set - old_set)[0] if new_set - old_set else "",
                        "size": new_size,
                    })
                return old_civ
        return None

    def mark_fallen(self, civ_id: str, tick: int) -> None:
        for civ in self.civilizations:
            if civ.id == civ_id and civ.status != "fallen":
                civ.status = "fallen"
                civ.died_at = tick
                if self.bus:
                    self.bus.publish(EventType.CIVILIZATION_FALLEN, {
                        "civilization_id": civ.id,
                        "peak_size": civ.peak_size,
                        "lifespan": tick - civ.born_at,
                    })
```

- [ ] **Step 4: Run & commit**

```bash
cd ~/Documents/Claude/dao-genesis && pip install networkx>=3.0
python3 -m pytest tests/test_civilization_engine.py tests/test_event_bus.py -v
git add src/civilization_engine.py tests/test_civilization_engine.py src/event_bus.py requirements.txt && git commit -m "feat: add Civilization Engine with community detection"
```

---

### Task 2: History Engine

**Files:**
- Create: `src/history_engine.py`
- Create: `tests/test_history_engine.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for History Engine."""
from src.history_engine import HistoryEngine, LineageHistory, HistoryEvent


class TestLineageHistory:
    def test_record_event(self):
        lh = LineageHistory(lineage_root="L1", born_tick=100)
        lh.record(HistoryEvent(tick=150, event_type="peak", data={"size": 10}))
        assert len(lh.key_events) == 1

    def test_max_generation(self):
        lh = LineageHistory(lineage_root="L1", born_tick=100)
        lh.max_generation = 5
        assert lh.max_generation == 5


class TestHistoryEngine:
    def test_record_lineage_event(self):
        eng = HistoryEngine()
        eng.record_lineage_event("L1", tick=100, event_type="founded", data={})
        assert "L1" in eng.lineages

    def test_record_era(self):
        eng = HistoryEngine()
        eng.record_era("civ_0", tick_start=100, tick_end=200,
                       era_name="golden_age", size=15)
        assert "civ_0" in eng.civilizations
```

- [ ] **Step 2: Run & implement**

```python
"""History Engine — three-layer event recording and era detection."""
from dataclasses import dataclass, field


@dataclass
class HistoryEvent:
    tick: int
    event_type: str
    data: dict


@dataclass
class LineageHistory:
    lineage_root: str
    born_tick: int
    died_tick: int | None = None
    max_generation: int = 0
    total_structures: int = 0
    key_events: list[HistoryEvent] = field(default_factory=list)

    def record(self, event: HistoryEvent) -> None:
        self.key_events.append(event)


@dataclass
class EraEvent:
    tick_start: int
    tick_end: int
    era_name: str
    size: int
    key_development: str = ""


@dataclass
class CivilizationHistory:
    civilization_id: str
    timeline: list[EraEvent] = field(default_factory=list)


class HistoryEngine:
    def __init__(self):
        self.lineages: dict[str, LineageHistory] = {}
        self.civilizations: dict[str, CivilizationHistory] = {}
        self.environmental: list[dict] = []

    def record_lineage_event(self, lineage_root: str, tick: int,
                             event_type: str, data: dict) -> None:
        if lineage_root not in self.lineages:
            self.lineages[lineage_root] = LineageHistory(
                lineage_root=lineage_root, born_tick=tick)
        self.lineages[lineage_root].record(
            HistoryEvent(tick=tick, event_type=event_type, data=data))

    def record_era(self, civ_id: str, tick_start: int, tick_end: int,
                   era_name: str, size: int, key_dev: str = "") -> None:
        if civ_id not in self.civilizations:
            self.civilizations[civ_id] = CivilizationHistory(
                civilization_id=civ_id)
        self.civilizations[civ_id].timeline.append(
            EraEvent(tick_start, tick_end, era_name, size, key_dev))

    def record_environment(self, tick: int, region: str,
                           remnant_count: int, cell_density: float) -> None:
        self.environmental.append({
            "tick": tick, "region": region,
            "remnant_count": remnant_count, "cell_density": cell_density,
        })

    def get_lineage_narrative(self, lineage_root: str) -> str:
        lh = self.lineages.get(lineage_root)
        if not lh:
            return ""
        events = [f"tick {e.tick}: {e.event_type}" for e in lh.key_events[-5:]]
        lifespan = (lh.died_tick or 0) - lh.born_tick
        return (f"Lineage {lineage_root}: born at {lh.born_tick}, "
                f"lived {lifespan} ticks, max gen {lh.max_generation}. "
                f"Recent: {' | '.join(events)}")
```

- [ ] **Step 3: Run & commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_history_engine.py -v
git add src/history_engine.py tests/test_history_engine.py && git commit -m "feat: add History Engine with three-layer recording"
```

---

### Task 3: Myth Engine

**Files:**
- Create: `src/myth_engine.py`
- Create: `tests/test_myth_engine.py`

- [ ] **Step 1: Write tests**

```python
"""Tests for Myth Engine."""
from src.myth_engine import MythEngine, HeroLineage, BeliefTenet


class TestHeroLineage:
    def test_hero_creation(self):
        h = HeroLineage(lineage_root="L1", peak_score=85.0, knowledge_count=3,
                        channel=1, max_generation=5)
        assert h.lineage_root == "L1" and h.peak_score == 85.0


class TestMythEngine:
    def test_generate_founder_narrative(self):
        eng = MythEngine()
        narrative = eng.generate_founder_narrative(
            civ_name="civ_0", founder="L1", born_at=100,
            region="top", competitor_count=3, mutualism_count=2,
            peak_tick=300, peak_size=10, peak_cells=50)
        assert "civ_0" in narrative and "L1" in narrative

    def test_empty_heroes(self):
        eng = MythEngine()
        assert eng.get_heroes() == []

    def test_belief_extraction(self):
        eng = MythEngine()
        eng.extract_beliefs("civ_0", [
            {"id": "know_1", "antecedent": "sym_A", "consequent": "sym_B",
             "confidence": 2.0, "generation_depth": 4, "lineage_count": 3}
        ])
        beliefs = eng.get_beliefs("civ_0")
        assert len(beliefs) >= 1
```

- [ ] **Step 2: Run & implement**

```python
"""Myth Engine — founder narratives, hero lineages, and belief systems."""
from dataclasses import dataclass, field


@dataclass
class HeroLineage:
    lineage_root: str
    peak_score: float = 0.0
    knowledge_count: int = 0
    channel: int = 0
    max_generation: int = 0


@dataclass
class BeliefTenet:
    knowledge_id: str
    formulation: str
    confidence: float
    believer_count: int
    first_seen: int = 0
    last_seen: int = 0


class MythEngine:
    def __init__(self):
        self.heroes: dict[str, list[HeroLineage]] = {}  # civ_id → heroes
        self.beliefs: dict[str, list[BeliefTenet]] = {}  # civ_id → tenets
        self.narratives: dict[str, dict] = {}  # civ_id → narrative dict

    def generate_founder_narrative(self, **kwargs) -> str:
        return (
            f"{kwargs.get('civ_name', 'Unknown')} was founded by "
            f"{kwargs.get('founder', 'Unknown')} at tick {kwargs.get('born_at', 0)} "
            f"in the {kwargs.get('region', 'Unknown')} region. "
            f"It rose amidst {kwargs.get('competitor_count', 0)} rivals "
            f"and formed {kwargs.get('mutualism_count', 0)} alliances. "
            f"At its peak (tick {kwargs.get('peak_tick', 0)}), "
            f"it encompassed {kwargs.get('peak_size', 0)} lineages "
            f"with {kwargs.get('peak_cells', 0)} cells."
        )

    def extract_beliefs(self, civ_id: str, knowledge_items: list[dict]) -> None:
        tenets = []
        for k in knowledge_items:
            if k.get("generation_depth", 0) >= 3:
                tenets.append(BeliefTenet(
                    knowledge_id=k["id"],
                    formulation=f"{k['antecedent']} leads to {k['consequent']}",
                    confidence=k.get("confidence", 0.0),
                    believer_count=k.get("lineage_count", 0),
                ))
        tenets.sort(key=lambda t: t.believer_count * t.confidence, reverse=True)
        self.beliefs[civ_id] = tenets

    def add_hero(self, civ_id: str, hero: HeroLineage) -> None:
        if civ_id not in self.heroes:
            self.heroes[civ_id] = []
        self.heroes[civ_id].append(hero)

    def get_heroes(self, civ_id: str = None) -> list[HeroLineage]:
        if civ_id:
            return self.heroes.get(civ_id, [])
        return [h for heroes in self.heroes.values() for h in heroes]

    def get_beliefs(self, civ_id: str) -> list[BeliefTenet]:
        return self.beliefs.get(civ_id, [])
```

- [ ] **Step 3: Run & commit**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_myth_engine.py -v
git add src/myth_engine.py tests/test_myth_engine.py && git commit -m "feat: add Myth Engine with narratives, heroes, and beliefs"
```

---

### Task 4: CLI + run.py

**Files:**
- Modify: `src/cli/renderer.py` (Civilization panel)
- Modify: `run.py` (wire Phase 7 engines)

READ existing files first.

**Renderer:** Add `civilization_data` param. Add Civilization panel between Cognition and Ecology.

**run.py:** Create CivilizationEngine, HistoryEngine, MythEngine. Every 100 ticks: build ecology network graph, run civ_engine.scan(), update history and myth engines.

- [ ] **Implement, smoke test, commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/cli/renderer.py run.py && git commit -m "feat: add Civilization panel and wire Phase 7 engines"
```

---

### Task 5: Integration & Verification

- [ ] **Full test suite + 1000-tick verification + commit & push**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/ -v
git add -A && git commit -m "feat: Phase 7 civilization layer complete — DAO Genesis MVP"
git push origin main
```
