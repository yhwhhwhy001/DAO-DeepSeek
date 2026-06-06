# Phase 8: Web UI Design Spec

> **Status:** Draft | **Date:** 2026-06-07

## 1. Overview

**Goal:** 将 DAO Genesis 从终端 Rich Live 渲染迁移到 Web 界面，通过浏览器观察宇宙运行。不改变任何引擎逻辑，不添加游戏交互。

**Approach:** FastAPI + WebSocket 后端封装 WorldEngine，React + PixiJS 前端渲染网格和面板。WebSocket 每 tick 推送完整状态快照。

---

## 2. 后端

### 2.1 FastAPI 入口

```
GET  /                 → 返回 index.html (React 构建产物)
GET  /ws               → WebSocket 升级
```

### 2.2 WebSocket 协议

```
客户端 → 服务端:
  {"type": "start", "config": "phase1_optimized.yaml"}  # 启动仿真
  {"type": "pause"}                                       # 暂停
  {"type": "resume"}                                      # 恢复
  {"type": "set_speed", "tps": 10}                        # 设置 tick/s
  {"type": "get_status"}                                  # 请求当前状态

服务端 → 客户端 (每 tick):
  {
    "type": "tick",
    "tick": 500,
    "grid": {
      "width": 80, "height": 40,
      "cells": [{"x": 5, "y": 10, "type": 1, "energy": 5.0, "id": "abc"}],
      "remnants": [{"x": 3, "y": 7, "energy": 2.0, "type": 0}]
    },
    "stats": {
      "alive_count": 110,
      "total_energy": 215.3,
      "structure_count": 115,
      "stable_count": 5
    },
    "panels": {
      "entropy": {...},
      "leaderboard": {...},
      "decision": {...},
      "life": {...},
      "ecology": {...},
      "cognition": {...},
      "civilization": {...},
      "lineage": {...}
    }
  }
```

### 2.3 服务端架构

```python
# server/main.py
class GameSession:
    world: WorldEngine
    detector, memory, decision, ...  # 所有引擎
    running: bool
    tps: int = 15

    async def loop(self, websocket):
        while True:
            msg = await websocket.receive_json()
            if msg["type"] == "start":
                self._init_world(msg["config"])
                asyncio.create_task(self._run_loop(websocket))
            elif msg["type"] == "pause":
                self.running = False
            elif msg["type"] == "resume":
                self.running = True
            elif msg["type"] == "set_speed":
                self.tps = msg["tps"]

    async def _run_loop(self, websocket):
        while True:
            if self.running:
                self.world.time_engine.step()
                state = self._collect_state()
                await websocket.send_json(state)
            await asyncio.sleep(1 / self.tps)
```

---

## 3. 前端

### 3.1 技术栈

```
React 18 + TypeScript + Vite + PixiJS 8
```

### 3.2 布局

```
┌──────────────────────────────────────────────────────────────┐
│  DAO Genesis — Phase 7                    Tick: 500  ▶ ⏸ ⏩  │
├────────────────────────────────┬─────────────────────────────┤
│                                │  熵                          │
│                                │  全局熵: 1.82 bit             │
│       PixiJS Canvas            │  局部熵: 0.72 ± 0.18          │
│       (80×40 网格)             │  结构熵: 2.15 bit             │
│                                │  趋势: 稳态                   │
│      细胞: 彩色符号            │                              │
│      残骸: + 灰色标记          │  排行榜                      │
│      太阳梯度: 暖/冷背景        │  1. tick42_3 age=156         │
│                                │  2. tick51_1 age=87          │
│                                │                              │
│                                │  决策 / 生命                 │
│                                │  生态 / 认知 / 文明 / 谱系    │
│                                │  事件日志                    │
├────────────────────────────────┴─────────────────────────────┤
│  存活: 110  |  能量: 215.3  |  结构: 115 (5 稳定)  |  文明: 1  │
└──────────────────────────────────────────────────────────────┘
```

### 3.3 右侧面板 — 折叠式

```
每个面板 = 标题栏(可点击折叠) + 内容区

默认展开: 熵、排行榜
默认折叠: 决策、生命、生态、认知、文明、谱系
```

---

## 4. PixiJS 渲染

```
细胞符号:
  type=0 → 白色圆点 · (radius=4)
  type=1 → 红色圆点 ○ (radius=5, glow)
  type=2 → 绿色菱形 ◇ (size=6, glow)
  type=3 → 蓝色方块 □ (size=5, glow)

残骸:
  灰色半透明 + 小 (radius=3)

网格背景:
  上半部: 暖金色渐变 (太阳梯度富饶区)
  下半部: 暗蓝色渐变 (贫瘠区)
  网格线: 浅色虚线

动画:
  细胞呼吸效果 (scale 微动, 1s 周期)
  新细胞出生闪光
  细胞死亡淡出

性能:
  80×40 = 3200 cells max
  PixiJS batch rendering, 60fps 无压力
```

---

## 5. 文件结构

```
dao-genesis/
├── server/
│   ├── main.py              # FastAPI + WebSocket + GameSession
│   └── requirements.txt     # fastapi, uvicorn, websockets
├── client/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx          # React 入口
│       ├── App.tsx           # 主布局
│       ├── App.css           # 全局样式
│       ├── components/
│       │   ├── Toolbar.tsx        # 顶部控制栏
│       │   ├── GameCanvas.tsx     # PixiJS 画布封装
│       │   ├── SidePanel.tsx      # 右侧面板容器
│       │   ├── PanelSection.tsx   # 单个可折叠面板
│       │   └── BottomBar.tsx      # 底部状态栏
│       ├── engine/
│       │   └── PixiApp.ts         # PixiJS Application + 渲染循环
│       └── hooks/
│           └── useWebSocket.ts    # WebSocket 连接管理
└── run_web.py               # 启动脚本: uvicorn server.main:app
```

---

## 6. 运行方式

```bash
# 安装后端依赖
pip install fastapi uvicorn websockets

# 安装前端依赖
cd client && npm install && cd ..

# 开发模式 (两个终端)
# 终端1: 启动后端
python run_web.py
# 终端2: 启动前端
cd client && npm run dev

# 浏览器打开 http://localhost:5173

# 生产模式
cd client && npm run build
python run_web.py
# 浏览器打开 http://localhost:8000
```

---

## 7. 不在本阶段的范围

- 鼠标点击注入/选择/拖拽 → 后续
- 键盘快捷键 → 后续
- 灾难/能量爆发等干预 → 后续
- 结构/文明详情弹窗 → 后续
- 移动端适配 → 后续

本阶段唯一交互：播放/暂停/加减速。
