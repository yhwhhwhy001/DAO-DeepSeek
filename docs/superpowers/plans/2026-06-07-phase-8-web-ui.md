# Phase 8: Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 DAO Genesis 从终端 Rich 渲染迁移到 Web 界面——FastAPI + WebSocket 后端 + React + PixiJS 前端。

**Architecture:** 后端 GameSession 封装 WorldEngine + 所有引擎，WebSocket 每 tick 推送 JSON 快照。前端 React 管理面板，PixiJS 渲染网格。播放/暂停/调速。

**Tech Stack:** Python 3.14, FastAPI, uvicorn, React 18, TypeScript, Vite, PixiJS 8

**Project Root:** `~/Documents/Claude/dao-genesis/`

---

### Task 1: Backend Server

**Files:**
- Create: `server/main.py`
- Create: `server/requirements.txt`
- Create: `run_web.py`

- [ ] **Step 1: Write server/main.py**

```python
"""DAO Genesis Web 服务端 — FastAPI + WebSocket"""
import asyncio
import json
import yaml
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from src.world_engine import WorldEngine
from src.event_bus import EventType
from src.structure_detector import StructureDetector
from src.pattern_hasher import PatternHasher
from src.entropy_engine import EntropyEngine
from src.leaderboard import build_leaderboard
from src.memory_engine import MemoryEngine
from src.lineage_analyzer import LineageAnalyzer
from src.decision_engine import DecisionEngine
from src.ruleset import generate_random_ruleset
from src.life_detector import LifeDetector
from src.map_engine import MapEngine
from src.resource_engine import ResourceEngine
from src.ecology_engine import EcologyEngine
from src.symbol_engine import SymbolEngine
from src.knowledge_engine import KnowledgeEngine
from src.language_engine import LanguageEngine
from src.civilization_engine import CivilizationEngine
from src.history_engine import HistoryEngine
from src.myth_engine import MythEngine
import random
import networkx as nx

app = FastAPI(title="DAO Genesis")


class GameSession:
    def __init__(self):
        self.world: WorldEngine | None = None
        self.running = False
        self.tps = 60
        self._tick = 0

    def init(self, config_path: str):
        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.world = WorldEngine(config)

        # 所有引擎
        self.detector = StructureDetector(self.world.grid, self.world.bus)
        self.pattern_hasher = PatternHasher()
        self.entropy = EntropyEngine(self.world.grid, self.world.bus, self.detector,
                                     num_types=config["physics"]["num_types"])
        self.memory = MemoryEngine(self.world.bus, self.detector)
        self.lineage_analyzer = LineageAnalyzer()

        rng = random.Random(42)
        self.decision = DecisionEngine(self.world.grid, seed=42)
        self.decision._detector = self.detector
        for cell in list(self.world.grid.all_cells):
            self.decision.register_cell(cell.id, generate_random_ruleset(rng))
        self.world.time_engine.decision_engine = self.decision

        self.life = LifeDetector(self.world.bus)
        self.map_engine = MapEngine(height=config["world"]["height"])
        self.resource = ResourceEngine()
        self.ecology = EcologyEngine()
        self.symbol_engine = SymbolEngine()
        self.knowledge_engine = KnowledgeEngine()
        self.language_engine = LanguageEngine()
        self.civ_engine = CivilizationEngine(self.world.bus)
        self.history = HistoryEngine()
        self.myth = MythEngine()

        self.world.state_engine.map_engine = self.map_engine
        self.world.state_engine.resource_engine = self.resource
        self.world.time_engine.resource_engine = self.resource

        # 分裂继承
        def on_fission(event):
            self.decision.inherit_on_fission(event.data["parent_id"], event.data["child_id"], rng)
        self.world.bus.subscribe(EventType.STRUCTURE_FISSION, on_fission)

        def on_destroy(event):
            self.decision.remove_cell(event.data["cell_id"])
        self.world.bus.subscribe(EventType.CELL_DESTROYED, on_destroy)

    def step(self) -> dict:
        self.world.time_engine.step()
        self._tick += 1

        g = self.world.grid
        cells = []
        for cell in g.all_cells:
            cells.append({"x": cell.x, "y": cell.y, "type": cell.type,
                          "energy": round(cell.energy, 2), "id": cell.id[:8]})

        remnants = []
        if self.resource:
            for r in self.resource.all_remnants:
                remnants.append({"x": r.x, "y": r.y, "energy": round(r.energy, 2), "type": r.type})

        # 熵
        entropy_data = None
        if self.entropy.current_snapshot:
            s = self.entropy.current_snapshot
            entropy_data = {
                "global": round(s["global_entropy"], 2),
                "local_mean": round(s["local_entropy_mean"], 2),
                "local_std": round(s["local_entropy_std"], 2),
                "structure": round(s["structure_entropy"], 2),
                "trend": self.entropy.current_trend,
            }

        # 排行榜
        active = self.detector.get_active()
        pattern_occs = {h: r.total_occurrences for h, r in self.pattern_hasher.patterns.items()}
        struct_dicts = []
        for s in active:
            types_seen = set()
            for c in g.all_cells:
                if c.id in s.cells:
                    types_seen.add(c.type)
            struct_dicts.append({"id": s.id, "age": s.age, "size": len(s.cells),
                                 "type_count": len(types_seen), "shape_hash": s.shape_hash})
        ranked = build_leaderboard(struct_dicts, pattern_occs, top_n=5)
        leaderboard_data = [{"id": r["id"], "age": r["age"], "size": r["size"],
                             "hash": r.get("shape_hash", "")[:6], "score": round(r["score"], 2)}
                            for r in ranked]

        # 生命
        lifeforms = self.life.get_lifeforms()
        life_data = {"proto": len([lf for lf in lifeforms if lf.peak_score >= 60]),
                     "true_count": len([lf for lf in lifeforms if lf.peak_score >= 80]),
                     "top": [{"id": lf.structure_id, "score": round(lf.peak_score, 1)}
                             for lf in sorted(lifeforms, key=lambda x: x.peak_score, reverse=True)[:3]]}

        # 认知
        lang_stats = self.language_engine.get_stats()
        cognition_data = {"symbols": len(self.symbol_engine.symbols),
                          "signals": lang_stats["total_signals"],
                          "top_symbol": lang_stats.get("top_symbol", "N/A")}

        return {
            "type": "tick",
            "tick": self._tick,
            "grid": {"width": g.width, "height": g.height,
                     "cells": cells, "remnants": remnants},
            "stats": {"alive": g.alive_count, "energy": round(g.total_energy, 1),
                      "structures": self.detector.active_count,
                      "stable": self.detector.stable_count,
                      "lifeforms": len(lifeforms)},
            "panels": {
                "entropy": entropy_data,
                "leaderboard": leaderboard_data,
                "life": life_data,
                "cognition": cognition_data,
            },
        }


session = GameSession()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        msg = await ws.receive_json()
        cmd = msg.get("type")

        if cmd == "start":
            config = msg.get("config", "experiments/highspeed.yaml")
            session.init(config)
            session.running = True
            asyncio.create_task(_run_loop(ws))

        elif cmd == "pause":
            session.running = False

        elif cmd == "resume":
            session.running = True

        elif cmd == "set_speed":
            session.tps = msg.get("tps", 60)


async def _run_loop(ws: WebSocket):
    while True:
        try:
            if session.running and session.world:
                state = session.step()
                await ws.send_json(state)
                await asyncio.sleep(1 / session.tps)
            else:
                await asyncio.sleep(0.1)
        except Exception:
            break


# 静态文件 (生产模式)
static_dir = Path(__file__).parent.parent / "client" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True))
```

- [ ] **Step 2: Write server/requirements.txt**

```
fastapi>=0.100.0
uvicorn>=0.23.0
websockets>=12.0
```

- [ ] **Step 3: Write run_web.py**

```python
"""DAO Genesis Web 启动脚本"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 4: Install deps, verify server starts**

```bash
cd ~/Documents/Claude/dao-genesis && pip install fastapi uvicorn websockets -q
python3 -c "from server.main import app; print('Server OK')"
```

- [ ] **Step 5: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add server/ run_web.py && git commit -m "feat: add FastAPI + WebSocket game server"
```

---

### Task 2: React Frontend Scaffold

**Files:**
- Create: `client/` 项目 (package.json, vite.config.ts, tsconfig.json, index.html, src/*)

使用 Vite 创建 React + TypeScript 项目：

```bash
cd ~/Documents/Claude/dao-genesis
npm create vite@latest client -- --template react-ts
cd client && npm install && npm install pixi.js@^8
```

清理默认模板文件，创建：

- `client/src/main.tsx` — React 入口
- `client/src/App.tsx` — 主布局 (Toolbar + Canvas + SidePanel + BottomBar)
- `client/src/App.css` — 全局样式 (暗色主题)
- `client/src/hooks/useWebSocket.ts` — WebSocket 连接 hook
- `client/src/components/Toolbar.tsx`
- `client/src/components/GameCanvas.tsx`
- `client/src/components/SidePanel.tsx`
- `client/src/components/PanelSection.tsx`
- `client/src/components/BottomBar.tsx`
- `client/src/engine/PixiApp.ts`

- [ ] **Step 1: 创建 Vite 项目并安装依赖**

```bash
cd ~/Documents/Claude/dao-genesis
npm create vite@latest client -- --template react-ts 2>&1 || echo "Vite project created"
cd client && npm install && npm install pixi.js@^8
```

- [ ] **Step 2: 编写核心文件**

`client/src/hooks/useWebSocket.ts`:
```typescript
import { useState, useRef, useCallback } from 'react';

export interface SimulationState {
  tick: number;
  grid: { width: number; height: number; cells: any[]; remnants: any[] };
  stats: Record<string, number>;
  panels: Record<string, any>;
}

export function useWebSocket() {
  const [state, setState] = useState<SimulationState | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;
    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: 'start', config: 'experiments/highspeed.yaml' }));
    };
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'tick') setState(data);
    };
    ws.onclose = () => setConnected(false);
  }, []);

  const pause = () => wsRef.current?.send(JSON.stringify({ type: 'pause' }));
  const resume = () => wsRef.current?.send(JSON.stringify({ type: 'resume' }));
  const setSpeed = (tps: number) => wsRef.current?.send(JSON.stringify({ type: 'set_speed', tps }));

  return { state, connected, connect, pause, resume, setSpeed };
}
```

`client/src/App.tsx`:
```tsx
import { useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import Toolbar from './components/Toolbar';
import GameCanvas from './components/GameCanvas';
import SidePanel from './components/SidePanel';
import BottomBar from './components/BottomBar';
import './App.css';

export default function App() {
  const { state, connected, connect, pause, resume, setSpeed } = useWebSocket();

  useEffect(() => { connect(); }, []);

  return (
    <div className="app">
      <Toolbar tick={state?.tick ?? 0} connected={connected}
               onPause={pause} onResume={resume} onSpeed={setSpeed} />
      <div className="main">
        <GameCanvas state={state} />
        <SidePanel panels={state?.panels} stats={state?.stats} />
      </div>
      <BottomBar stats={state?.stats} />
    </div>
  );
}
```

`client/src/App.css` (暗色主题):
```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0a0a0f; color: #c8c8d0; font-family: 'Courier New', monospace; }
.app { display: flex; flex-direction: column; height: 100vh; }
.main { display: flex; flex: 1; overflow: hidden; }
```

- [ ] **Step 3: 验证前端能启动**

```bash
cd ~/Documents/Claude/dao-genesis/client && npm run dev -- --host 2>&1 &
sleep 3 && curl -s http://localhost:5173 | head -5
```

- [ ] **Step 4: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add client/ && git commit -m "feat: add React + Vite + PixiJS frontend scaffold"
```

---

### Task 3: PixiJS Grid Rendering

**Files:**
- Write: `client/src/engine/PixiApp.ts`
- Modify: `client/src/components/GameCanvas.tsx`

- [ ] **Step 1: Write PixiApp.ts**

```typescript
import { Application, Graphics, Container } from 'pixi.js';

const TYPE_COLORS = [0xffffff, 0xff4444, 0x44ff44, 0x4488ff];
const TYPE_CHARS = ['·', '○', '◇', '□'];

export class PixiApp {
  app: Application;
  cellLayer: Container;
  remnantLayer: Container;
  gridLayer: Graphics;
  cellSize = 12;
  gap = 2;

  constructor(canvas: HTMLCanvasElement, width: number, height: number) {
    this.app = new Application();
    this.app.init({
      canvas,
      width: width * (this.cellSize + this.gap),
      height: height * (this.cellSize + this.gap),
      background: 0x0a0a1a,
      antialias: true,
    });

    this.gridLayer = new Graphics();
    this.remnantLayer = new Container();
    this.cellLayer = new Container();
    this.app.stage.addChild(this.gridLayer, this.remnantLayer, this.cellLayer);
    this.drawGrid(width, height);
  }

  drawGrid(w: number, h: number) {
    const g = this.gridLayer;
    g.clear();
    const step = this.cellSize + this.gap;
    // 太阳梯度
    const midY = (h * step) / 2;
    for (let y = 0; y < h; y++) {
      const alpha = y * step < midY ? 0.15 : 0.05;
      g.rect(0, y * step, w * step, step).fill({ color: y * step < midY ? 0xffaa00 : 0x0044aa, alpha });
    }
    // 网格线
    g.setStrokeStyle({ width: 0.5, color: 0x1a1a2e, alpha: 0.3 });
    for (let x = 0; x <= w; x++) g.moveTo(x * step, 0).lineTo(x * step, h * step).stroke();
    for (let y = 0; y <= h; y++) g.moveTo(0, y * step).lineTo(w * step, y * step).stroke();
  }

  update(grid: { cells: any[]; remnants: any[] }) {
    const step = this.cellSize + this.gap;
    this.cellLayer.removeChildren();
    this.remnantLayer.removeChildren();

    // 残骸
    for (const r of grid.remnants) {
      const g = new Graphics();
      g.circle(r.x * step + step / 2, r.y * step + step / 2, 3)
       .fill({ color: 0x666666, alpha: 0.5 });
      this.remnantLayer.addChild(g);
    }

    // 细胞
    for (const c of grid.cells) {
      const g = new Graphics();
      const cx = c.x * step + step / 2;
      const cy = c.y * step + step / 2;
      const color = TYPE_COLORS[c.type] ?? 0xffffff;
      const r = 5 + c.energy * 0.2;

      g.circle(cx, cy, r).fill({ color, alpha: 0.9 });
      if (r > 6) {
        g.circle(cx, cy, r + 2).fill({ color, alpha: 0.15 });
      }
      this.cellLayer.addChild(g);
    }
  }
}
```

- [ ] **Step 2: Update GameCanvas.tsx**

```tsx
import { useRef, useEffect } from 'react';
import { PixiApp } from '../engine/PixiApp';

export default function GameCanvas({ state }: { state: any }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const appRef = useRef<PixiApp | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const w = state?.grid?.width ?? 80;
    const h = state?.grid?.height ?? 40;
    appRef.current = new PixiApp(canvasRef.current, w, h);
    return () => { appRef.current?.app.destroy(); };
  }, []);

  useEffect(() => {
    if (state?.grid && appRef.current) {
      appRef.current.update(state.grid);
    }
  }, [state]);

  return <canvas ref={canvasRef} className="game-canvas" />;
}
```

- [ ] **Step 3: Verify compilation**

```bash
cd ~/Documents/Claude/dao-genesis/client && npx tsc --noEmit 2>&1 | head -5
```

- [ ] **Step 4: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add client/ && git commit -m "feat: add PixiJS grid rendering with solar gradient"
```

---

### Task 4: Side Panels + Toolbar + BottomBar

**Files:**
- Write: `client/src/components/SidePanel.tsx`, `PanelSection.tsx`, `Toolbar.tsx`, `BottomBar.tsx`

- [ ] **Step 1: Write all 4 components**

`Toolbar.tsx`:
```tsx
export default function Toolbar({ tick, connected, onPause, onResume, onSpeed }:
  { tick: number; connected: boolean; onPause: () => void; onResume: () => void; onSpeed: (t: number) => void }) {
  return (
    <div className="toolbar">
      <span className="title">DAO 创世纪</span>
      <span className="tick">Tick: {tick}</span>
      <span className={`status ${connected ? 'green' : 'red'}`}>{connected ? '已连接' : '断开'}</span>
      <button onClick={onPause}>⏸ 暂停</button>
      <button onClick={onResume}>▶ 恢复</button>
      <button onClick={() => onSpeed(30)}>1x</button>
      <button onClick={() => onSpeed(120)}>4x</button>
      <button onClick={() => onSpeed(600)}>20x</button>
    </div>
  );
}
```

`PanelSection.tsx`:
```tsx
import { useState } from 'react';

export default function PanelSection({ title, defaultOpen = false, children }:
  { title: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="panel-section">
      <div className="panel-header" onClick={() => setOpen(!open)}>
        {open ? '▼' : '▶'} {title}
      </div>
      {open && <div className="panel-body">{children}</div>}
    </div>
  );
}
```

`SidePanel.tsx`:
```tsx
import PanelSection from './PanelSection';

export default function SidePanel({ panels, stats }: { panels: any; stats: any }) {
  const e = panels?.entropy;
  const lb = panels?.leaderboard;
  const life = panels?.life;
  const cog = panels?.cognition;

  return (
    <div className="side-panel">
      <PanelSection title="熵" defaultOpen>
        {e && <div className="panel-content">
          <div>全局熵: {e.global} bit</div>
          <div>局部熵: {e.local_mean} ± {e.local_std}</div>
          <div>结构熵: {e.structure} bit</div>
          <div>趋势: {e.trend}</div>
        </div>}
      </PanelSection>

      <PanelSection title="排行榜" defaultOpen>
        {lb && <div className="panel-content">
          {lb.map((r: any, i: number) => (
            <div key={i}>{i+1}. {r.id} age={r.age} sz={r.size} score={r.score}</div>
          ))}
        </div>}
      </PanelSection>

      <PanelSection title="生命">
        {life && <div className="panel-content">
          <div>准生命: {life.proto}  真生命: {life.true_count}</div>
          {life.top?.map((lf: any, i: number) => (
            <div key={i}>{i+1}. {lf.id} score={lf.score}</div>
          ))}
        </div>}
      </PanelSection>

      <PanelSection title="认知">
        {cog && <div className="panel-content">
          <div>符号: {cog.symbols}  信号: {cog.signals}</div>
        </div>}
      </PanelSection>

      <PanelSection title="统计">
        {stats && <div className="panel-content">
          <div>存活: {stats.alive}  能量: {stats.energy}</div>
          <div>结构: {stats.structures} ({stats.stable} 稳定)</div>
          <div>生命体: {stats.lifeforms}</div>
        </div>}
      </PanelSection>
    </div>
  );
}
```

`BottomBar.tsx`:
```tsx
export default function BottomBar({ stats }: { stats: any }) {
  if (!stats) return <div className="bottombar">等待连接...</div>;
  return (
    <div className="bottombar">
      存活: {stats.alive} | 能量: {stats.energy} | 结构: {stats.structures} ({stats.stable} 稳定) | 生命体: {stats.lifeforms}
    </div>
  );
}
```

- [ ] **Step 2: Update App.css with panel styles**

```css
.toolbar {
  display: flex; align-items: center; gap: 12px; padding: 8px 16px;
  background: #12121f; border-bottom: 1px solid #1a1a2e;
}
.toolbar .title { font-size: 16px; font-weight: bold; color: #44aaff; }
.toolbar .tick { color: #aaa; font-size: 14px; }
.toolbar .status { font-size: 12px; }
.toolbar .status.green { color: #44ff44; }
.toolbar .status.red { color: #ff4444; }
.toolbar button {
  background: #1a1a2e; color: #c8c8d0; border: 1px solid #2a2a3e;
  padding: 4px 12px; border-radius: 4px; cursor: pointer; font-family: inherit;
}
.toolbar button:hover { background: #2a2a4e; }

.side-panel {
  width: 280px; background: #0d0d18; border-left: 1px solid #1a1a2e;
  overflow-y: auto; padding: 8px;
}
.panel-section { margin-bottom: 4px; }
.panel-header {
  padding: 6px 8px; cursor: pointer; font-size: 13px;
  color: #88aacc; border-radius: 4px;
}
.panel-header:hover { background: #1a1a2e; }
.panel-body { padding: 6px 12px; font-size: 12px; line-height: 1.6; }
.panel-content div { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.bottombar {
  padding: 6px 16px; background: #12121f; border-top: 1px solid #1a1a2e;
  font-size: 13px; color: #888;
}

.game-canvas { display: block; flex: 1; }
```

- [ ] **Step 3: Verify compilation**

```bash
cd ~/Documents/Claude/dao-genesis/client && npx tsc --noEmit 2>&1 | tail -3
```

- [ ] **Step 4: Commit**

```bash
cd ~/Documents/Claude/dao-genesis && git add client/ && git commit -m "feat: add SidePanel, Toolbar, BottomBar with dark theme"
```

---

### Task 5: Integration + End-to-End Test

- [ ] **Step 1: Build frontend**

```bash
cd ~/Documents/Claude/dao-genesis/client && npm run build 2>&1 | tail -5
```

- [ ] **Step 2: Start server and test WebSocket**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -c "
import asyncio, json
from server.main import session
session.init('experiments/highspeed.yaml')
session.running = True
for i in range(5):
    state = session.step()
    print(f'Tick {state[\"tick\"]}: {state[\"stats\"][\"alive\"]} cells, {len(state[\"grid\"][\"cells\"])} cell objs')
print('Server E2E OK')
"
```

- [ ] **Step 3: Full test suite**

```bash
cd ~/Documents/Claude/dao-genesis && python3 -m pytest tests/ -q
```

- [ ] **Step 4: Final commit & push**

```bash
cd ~/Documents/Claude/dao-genesis && git add -A && git commit -m "feat: Phase 8 Web UI complete — DAO Genesis Web Edition"
git push origin main
```
