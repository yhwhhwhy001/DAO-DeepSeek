# 修仙 Rougelike 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 Web UI 中加入玩家修士角色——WASD 操控、法术战斗、境界突破、轮回转世。

**Architecture:** 后端 `cultivator.py` 实现境界/法术/突破/轮回引擎，server 增加 player 消息协议。前端 `useKeyboard` 监听按键，`HUDOverlay` 渲染 HUD，`PlayerRenderer` 渲染玩家标记，`CameraController` 跟随镜头。

**Tech Stack:** Python 3.14 + FastAPI + React 18 + PixiJS 8 + TypeScript

**Project Root:** `~/Documents/Claude/dao-genesis/`

---

### Task 1: 修士引擎 (cultivator.py)

**Files:**
- Create: `src/cultivator.py`
- Create: `tests/test_cultivator.py`

- [ ] **Step 1: Write tests**

```python
"""修士引擎测试"""
from src.cultivator import Cultivator, Realm, breakthrough, REALMS


class TestRealm:
    def test_start_at_qi_condensation(self):
        cv = Cultivator(cell_id="p1")
        assert cv.realm.name == "练气"
        assert cv.energy == 10.0

    def test_breakthrough_succeeds_on_high_roll(self):
        cv = Cultivator(cell_id="p1")
        cv.energy = 30.0
        result = breakthrough(cv, force_success=True)
        assert result
        assert cv.realm.name == "筑基"

    def test_breakthrough_fails(self):
        cv = Cultivator(cell_id="p1")
        cv.energy = 30.0
        result = breakthrough(cv, force_failure=True)
        assert not result
        assert cv.energy < 30.0  # lost energy

    def test_reincarnation_preserves_skills(self):
        cv = Cultivator(cell_id="p1")
        cv.skills = ["金灵诀", "混元诀"]
        cv.energy = 80.0
        new_cv = cv.reincarnate(new_cell_id="p2")
        assert new_cv.cell_id == "p2"
        assert new_cv.skills == ["金灵诀", "混元诀"]
        assert new_cv.energy == 80.0 * 0.3 + 5.0  # 24 + 5 = 29
        assert new_cv.realm.name == "练气"  # realm resets

    def test_spell_cast_deducts_cost(self):
        cv = Cultivator(cell_id="p1")
        cv.energy = 30.0
        cv.cast("护体罡气")
        assert cv.energy == 25.0
        assert cv.shield_ticks == 10

    def test_skill_slots_by_realm(self):
        cv = Cultivator(cell_id="p1")
        assert cv.max_skills == 1  # 练气
        cv.energy = 30.0
        breakthrough(cv, force_success=True)
        assert cv.max_skills == 2  # 筑基
        cv.energy = 60.0
        breakthrough(cv, force_success=True)
        breakthrough(cv, force_success=True)
        assert cv.max_skills == 3  # 元婴
```

- [ ] **Step 2: Run (expect fail)**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_cultivator.py -v
```

- [ ] **Step 3: Write src/cultivator.py**

```python
"""修士引擎 —— 境界、法术、突破、轮回"""
import random
from dataclasses import dataclass, field

SPELL_COSTS = {"吐纳术": 0, "护体罡气": 5, "神念探查": 3, "血遁术": 15, "夺舍术": 50}
REALMS = [
    {"name": "练气", "min_energy": 0, "tribulation": 0.0, "max_skills": 1},
    {"name": "筑基", "min_energy": 10, "tribulation": 0.10, "max_skills": 2},
    {"name": "金丹", "min_energy": 30, "tribulation": 0.20, "max_skills": 2},
    {"name": "元婴", "min_energy": 60, "tribulation": 0.30, "max_skills": 3},
    {"name": "化神", "min_energy": 100, "tribulation": 0.40, "max_skills": 3},
    {"name": "渡劫", "min_energy": 200, "tribulation": 0.50, "max_skills": 4},
]


@dataclass
class Realm:
    name: str
    min_energy: float
    tribulation: float
    max_skills: int


class Cultivator:
    def __init__(self, cell_id: str):
        self.cell_id = cell_id
        self.energy = 10.0
        self.max_energy = 10.0
        self._realm_index = 0
        self.skills: list[str] = []
        self.shield_ticks = 0
        self.herbs = 0          # 天材地宝
        self.reincarnation_count = 0
        self.max_realm_reached = 0
        self.tick_age = 0
        self.total_kills = 0
        self.total_energy_absorbed = 0.0
        self._rng = random.Random()

    @property
    def realm(self) -> Realm:
        r = REALMS[self._realm_index]
        return Realm(**r)

    @property
    def max_skills(self) -> int:
        return self.realm.max_skills

    def cast(self, spell: str) -> bool:
        cost = SPELL_COSTS.get(spell, 0)
        if self.energy < cost:
            return False
        self.energy -= cost
        if spell == "护体罡气":
            self.shield_ticks = 10
        return True

    def try_breakthrough(self) -> bool:
        return breakthrough(self)

    def reincarnate(self, new_cell_id: str) -> "Cultivator":
        cv = Cultivator(new_cell_id)
        cv.energy = self.energy * 0.3 + 5.0
        cv.max_energy = cv.energy
        cv.skills = list(self.skills)
        cv.reincarnation_count = self.reincarnation_count + 1
        cv.max_realm_reached = max(self._realm_index, self.max_realm_reached)
        cv.total_kills = self.total_kills
        cv.total_energy_absorbed = self.total_energy_absorbed
        return cv


def breakthrough(cv: Cultivator, force_success=False, force_failure=False) -> bool:
    if cv._realm_index >= len(REALMS) - 1:
        return False
    next_realm = REALMS[cv._realm_index + 1]
    if cv.energy < next_realm["min_energy"]:
        return False

    prob = next_realm["tribulation"]
    if force_success:
        success = True
    elif force_failure:
        success = False
    else:
        success = cv._rng.random() > prob

    if success:
        cv._realm_index += 1
        cv.max_realm_reached = max(cv._realm_index, cv.max_realm_reached)
        return True
    else:
        cv.energy *= 0.5
        return False
```

- [ ] **Step 4: Run tests**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/test_cultivator.py -v
```

Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/cultivator.py tests/test_cultivator.py && git commit -m "feat: 修士引擎——境界/法术/突破/轮回"
```

---

### Task 2: 后端玩家协议

**Files:**
- Modify: `server/main.py` (增加玩家 spawn + 操作处理)

Read current server/main.py first. Then:

- [ ] **Step 1: Add player support to GameSession**

In `__init__`, add `self.player: Cultivator | None = None`

In `init()`, after world setup, spawn player:
```python
        from src.cultivator import Cultivator
        pos = self.world.grid.random_empty_position()
        if pos:
            from src.cell import Cell
            player_cell = Cell(x=pos[0], y=pos[1], type=0, energy=10.0)
            self.world.grid.place(player_cell)
            self.decision.register_cell(player_cell.id, generate_random_ruleset(rng))
            self.player = Cultivator(player_cell.id)
            self.player._rng = rng
```

In `step()`, process player tick before decision engine:
```python
        # 玩家 tick
        player_data = None
        if self.player and self.player.cell_id:
            player_cell = self.world.grid.get_by_id(self.player.cell_id)
            if player_cell:
                self.player.energy = player_cell.energy
                self.player.tick_age += 1
                if self.player.shield_ticks > 0:
                    self.player.shield_ticks -= 1
                self.player.try_breakthrough()
                player_data = {
                    "energy": round(self.player.energy, 1),
                    "max_energy": round(self.player.max_energy, 1),
                    "realm": self.player.realm.name,
                    "realm_index": self.player._realm_index,
                    "skills": self.player.skills,
                    "herbs": self.player.herbs,
                    "shield_ticks": self.player.shield_ticks,
                    "reincarnation": self.player.reincarnation_count,
                }
            else:
                self.player = None
```

Return player_data in the state dict:
```python
        return {
            "type": "tick",
            ...
            "player": player_data,
        }
```

Add grid.get_by_id method to Grid (in src/grid.py):
```python
    def get_by_id(self, cell_id: str) -> Cell | None:
        for cell in self._cells.values():
            if cell.id == cell_id:
                return cell
        return None
```

- [ ] **Step 2: Add player command handling to websocket endpoint**

After existing commands, add:
```python
        elif cmd == "player_move":
            if session.player and session.world:
                dx, dy = msg.get("dx", 0), msg.get("dy", 0)
                cell = session.world.grid.get_by_id(session.player.cell_id)
                if cell:
                    nx, ny = cell.x + dx, cell.y + dy
                    resolved = session.world.grid._resolve(nx, ny)
                    if resolved and session.world.grid.is_empty(*resolved):
                        session.world.grid.remove(cell.x, cell.y)
                        cell.x, cell.y = resolved
                        session.world.grid.place(cell)

        elif cmd == "player_spell":
            if session.player:
                spell = msg.get("spell", "")
                if spell == "吐纳术":
                    cell = session.world.grid.get_by_id(session.player.cell_id)
                    if cell:
                        for dx in range(-2, 3):
                            for dy in range(-2, 3):
                                nx, ny = cell.x + dx, cell.y + dy
                                absorbed = session.resource.absorb(nx, ny, cell.type, 1.0)
                                if absorbed > 0:
                                    cell.energy += absorbed * 3
                                    session.player.total_energy_absorbed += absorbed
                elif spell in SPELL_COSTS:
                    session.player.cast(spell)
                    if spell == "血遁术":
                        cell = session.world.grid.get_by_id(session.player.cell_id)
                        if cell:
                            empty = session.world.grid.random_empty_position()
                            if empty:
                                session.world.grid.remove(cell.x, cell.y)
                                cell.x, cell.y = empty
                                session.world.grid.place(cell)

        elif cmd == "player_reincarnate":
            if session.player:
                pos = session.world.grid.random_empty_position()
                if pos:
                    from src.cell import Cell
                    new_cell = Cell(x=pos[0], y=pos[1], type=0, energy=session.player.energy * 0.3 + 5)
                    session.world.grid.place(new_cell)
                    session.decision.register_cell(new_cell.id, generate_random_ruleset(rng))
                    session.player = session.player.reincarnate(new_cell.id)
```

- [ ] **Step 3: Run tests + verify**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/ -q
python3 -c "
from server.main import session
session.init('experiments/web.yaml')
print(f'Player spawned: {session.player.cell_id if session.player else \"NO\"} ')
session.step()
print(f'Player energy: {session.player.energy if session.player else \"NO\"}')
"
```

- [ ] **Step 4: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add src/grid.py server/main.py && git commit -m "feat: 后端玩家协议——移动/法术/轮回 + Grid.get_by_id"
```

---

### Task 3: 前端——键盘 + 修士状态

**Files:**
- Create: `client/src/hooks/useKeyboard.ts`
- Create: `client/src/hooks/useCultivator.ts`
- Modify: `client/src/hooks/useWebSocket.ts` (send player commands)

- [ ] **Step 1: useKeyboard.ts**

```typescript
import { useEffect } from 'react';

type KeyHandler = Record<string, () => void>;

export function useKeyboard(handlers: KeyHandler) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // 不拦截输入框按键
      if (e.target instanceof HTMLInputElement) return;
      const h = handlers[e.key.toLowerCase()] || handlers[e.key];
      if (h) { e.preventDefault(); h(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [handlers]);
}
```

- [ ] **Step 2: useCultivator.ts**

```typescript
import { useState, useCallback } from 'react';

export interface PlayerState {
  energy: number; max_energy: number; realm: string; realm_index: number;
  skills: string[]; herbs: number; shield_ticks: number; reincarnation: number;
}

export function useCultivator(sendMsg: (msg: object) => void) {
  const [player, setPlayer] = useState<PlayerState | null>(null);

  const updateFromTick = useCallback((data: any) => {
    if (data.player) setPlayer(data.player);
  }, []);

  const moveTo = useCallback((dx: number, dy: number) => {
    sendMsg({ type: 'player_move', dx, dy });
  }, [sendMsg]);

  const castSpell = useCallback((spell: string) => {
    sendMsg({ type: 'player_spell', spell });
  }, [sendMsg]);

  const reincarnate = useCallback(() => {
    sendMsg({ type: 'player_reincarnate' });
  }, [sendMsg]);

  return { player, updateFromTick, moveTo, castSpell, reincarnate };
}
```

- [ ] **Step 3: Update useWebSocket** — expose raw sendMsg function

```typescript
// Add to return:
  const sendMsg = useCallback((msg: object) => {
    wsRef.current?.send(JSON.stringify(msg));
  }, []);
  return { state, connected, error, connect, pause, resume, setSpeed, sendMsg };
```

- [ ] **Step 4: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add client/src/hooks/ && git commit -m "feat: 键盘监听 + 修士状态 hooks"
```

---

### Task 4: 前端——HUD 覆盖层

**Files:**
- Create: `client/src/components/HUDOverlay.tsx`
- Create: `client/src/components/SpellBar.tsx`
- Create: `client/src/components/EventLog.tsx`
- Modify: `client/src/App.tsx` (integrate HUD)

- [ ] **Step 1: Write HUD components**

`HUDOverlay.tsx` — 顶部状态栏：
```tsx
export default function HUDOverlay({ player, show }: { player: any; show: boolean }) {
  if (!show || !player) return null;
  return (
    <div style={{ position:'absolute', top:0, left:0, right:0, padding:'8px 16px',
      background:'linear-gradient(180deg, rgba(0,0,0,0.8) 0%, transparent 100%)',
      display:'flex', gap:16, alignItems:'center', color:'#fff', fontSize:13, fontFamily:'monospace', zIndex:10 }}>
      <span style={{ color:'#ffd700', fontSize:16 }}>✦ {player.realm}期</span>
      <span>灵力: {player.energy}/{player.max_energy}</span>
      <span>劫难: {Math.round(player.realm_index * 10)}%</span>
      <span>丹药: {player.herbs}</span>
      <span style={{ color:'#888' }}>轮回: #{player.reincarnation}</span>
    </div>
  );
}
```

`SpellBar.tsx` — 底部法术栏：
```tsx
export default function SpellBar({ castSpell, player }: { castSpell: (s: string) => void; player: any }) {
  const spells = ['吐纳术','护体罡气','神念探查','血遁术','夺舍术','聚灵丹','悟道丹'];
  const unlocked = player ? Math.min(2 + player.realm_index, spells.length) : 3;
  return (
    <div style={{ position:'absolute', bottom:0, left:0, right:0, padding:'8px 16px',
      background:'linear-gradient(0deg, rgba(0,0,0,0.8) 0%, transparent 100%)',
      display:'flex', gap:8, justifyContent:'center', zIndex:10 }}>
      <span style={{ color:'#888', fontSize:12, alignSelf:'center' }}>WASD 移动</span>
      {spells.slice(0, unlocked).map((s, i) => (
        <button key={s} onClick={() => castSpell(s)} style={spellBtnStyle}>
          [{i+1}] {s}
        </button>
      ))}
      <span style={{ color:'#888', fontSize:12, alignSelf:'center' }}>Tab 观察</span>
    </div>
  );
}
const spellBtnStyle: React.CSSProperties = { background:'#1a1a2e', color:'#c8c8d0', border:'1px solid #3a3a5e',
  padding:'4px 10px', borderRadius:4, cursor:'pointer', fontFamily:'monospace', fontSize:12 };
```

- [ ] **Step 2: Update App.tsx** — wire HUD + keyboard + cultivator

```tsx
// In App:
import { useKeyboard } from './hooks/useKeyboard';
import { useCultivator } from './hooks/useCultivator';
import HUDOverlay from './components/HUDOverlay';
import SpellBar from './components/SpellBar';

// Inside component:
  const { state, connected, error, connect, pause, resume, setSpeed, sendMsg } = useWebSocket();
  const { player, updateFromTick, moveTo, castSpell, reincarnate } = useCultivator(sendMsg);
  const [hudMode, setHudMode] = useState(true);

  // Update player from tick
  useEffect(() => { if (state) updateFromTick(state); }, [state]);

  // Keyboard
  useKeyboard({
    w: () => moveTo(0, -1), s: () => moveTo(0, 1),
    a: () => moveTo(-1, 0), d: () => moveTo(1, 0),
    '1': () => castSpell('吐纳术'), '2': () => castSpell('护体罡气'),
    '3': () => castSpell('神念探查'), '4': () => castSpell('血遁术'),
    '5': () => castSpell('夺舍术'), '6': () => castSpell('聚灵丹'),
    '7': () => castSpell('悟道丹'),
    'tab': () => setHudMode(m => !m),
  });

  // If HUD mode: show HUD overlay, hide side panel
  // If observation mode: show side panel, hide HUD
```

- [ ] **Step 3: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add client/src/components/ client/src/App.tsx && git commit -m "feat: HUD覆盖层 + 法术栏 + 键盘控制"
```

---

### Task 5: 前端——玩家渲染 + 镜头跟随

**Files:**
- Create: `client/src/engine/PlayerRenderer.ts`
- Modify: `client/src/engine/PixiApp.ts` (highlight player + camera offset)
- Modify: `client/src/components/GameCanvas.tsx`

- [ ] **Step 1: Update PixiApp** — add drawPlayer + cameraOffset

```typescript
// In PixiApp:
  playerCellId: string | null = null;
  cameraOffset = { x: 0, y: 0 };

  setPlayerCellId(id: string | null) { this.playerCellId = id; }

  updateCamera(playerX: number, playerY: number, canvasW: number, canvasH: number) {
    this.cameraOffset.x = Math.max(0, Math.min(playerX * this.step - canvasW / 2,
      this.step * 80 - canvasW));
    this.cameraOffset.y = Math.max(0, Math.min(playerY * this.step - canvasH / 2,
      this.step * 40 - canvasH));
  }

  _drawCells(grid) {
    // ... existing draw code, but offset by cameraOffset
    for (const c of grid.cells) {
      const [x, y, type, energy] = c;
      const sx = x * this.step + this.step / 2 - this.cameraOffset.x;
      const sy = y * this.step + this.step / 2 - this.cameraOffset.y;
      // ... draw at (sx, sy)
    }
    // 玩家金色光晕
    for (const c of grid.cells) {
      if (c[4] === this.playerCellId) {
        const sx = c[0] * this.step + this.step / 2 - this.cameraOffset.x;
        const sy = c[1] * this.step + this.step / 2 - this.cameraOffset.y;
        // golden glow (larger circle behind + star symbol)
        g.circle(sx, sy, 10).fill({ color: 0xffd700, alpha: 0.3 });
        g.circle(sx, sy, 6).fill({ color: 0xffd700, alpha: 0.6 });
      }
    }
  }
```

- [ ] **Step 2: Update server** — include player cell id in grid cells array

```python
# In step(), add cell id as 5th element for player detection:
cells = [[c.x, c.y, c.type, round(c.energy, 1), c.id if c.id == self.player.cell_id else ""]
         for c in g.all_cells]
```

- [ ] **Step 3: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add client/src/engine/ server/main.py && git commit -m "feat: 玩家金色标记 + 镜头跟随"
```

---

### Task 6: 轮回弹窗

**Files:**
- Create: `client/src/components/ReincarnationModal.tsx`
- Modify: `client/src/App.tsx` (show modal on player death)

- [ ] **Step 1: Write ReincarnationModal**

```tsx
export default function ReincarnationModal({ stats, onReincarnate }: { stats: any; onReincarnate: () => void }) {
  if (!stats) return null;
  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,0.85)', display:'flex',
      alignItems:'center', justifyContent:'center', zIndex:100 }}>
      <div style={{ background:'#1a1a2e', border:'1px solid #4a4a6e', borderRadius:8, padding:24,
        textAlign:'center', color:'#c8c8d0', fontFamily:'monospace', minWidth:300 }}>
        <div style={{ fontSize:24, color:'#ffd700', marginBottom:16 }}>✦ 魂归天地</div>
        <div>境界: {stats.realm} (最高: {stats.max_realm})</div>
        <div>存活: {stats.age} tick</div>
        <div>功法保留: {stats.skills?.join(', ') || '无'}</div>
        <div>灵力保留: {stats.energy_kept?.toFixed(1)} (30%)</div>
        <button onClick={onReincarnate} style={{ marginTop:20, padding:'10px 24px', fontSize:16,
          background:'#ffd700', color:'#000', border:'none', borderRadius:4, cursor:'pointer' }}>
          投胎转世
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Wire in App.tsx** — detect player null → show modal

- [ ] **Step 3: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add client/src/components/ReincarnationModal.tsx client/src/App.tsx && git commit -m "feat: 轮回弹窗——死亡摘要 + 投胎转世"
```

---

### Task 7: Tab 切换 (HUD ↔ 观察模式)

**Files:**
- Modify: `client/src/App.tsx`

- [ ] **Step 1: Implement toggle**

When `hudMode = true`: show HUD overlay + spell bar, hide side panel. Canvas is absolute-positioned full screen.
When `hudMode = false` (Tab): show side panel, hide HUD, canvas is in flex layout.

- [ ] **Step 2: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add client/src/App.tsx && git commit -m "feat: Tab键切换HUD游戏模式 ↔ 观察模式"
```

---

### Task 8: 集成验证

- [ ] **Step 1: Full test suite**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/ -q
```

- [ ] **Step 2: Build frontend**

```bash
cd ~/Documents/Claude/dao-genesis/client && npx tsc --noEmit && npm run build
```

- [ ] **Step 3: Server smoke test**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -c "
from server.main import session
session.init('experiments/web.yaml')
state = session.step()
print(f'Player: {state.get(\"player\")}')
"
```

- [ ] **Step 4: Final commit & push**

```bash
cd ~/Documents/Claude/dao-genesis && git add -A && git commit -m "feat: 修仙Roguelike完成——DAO Genesis 修仙版" && git push origin main
```
