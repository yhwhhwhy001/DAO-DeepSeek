import { Application, Graphics } from 'pixi.js';

const TYPE_COLORS = [0xffffff, 0xff4444, 0x44ff44, 0x4488ff];
const TYPE_COLORS_DARK = [0xaaaaaa, 0x882222, 0x228822, 0x224488];
const TYPE_COLORS_GLOW = [0xffffff, 0xff8888, 0x88ff88, 0x88aaff];

export class PixiApp {
  app!: Application;
  gridLayer!: Graphics;
  drawLayer!: Graphics;
  playerLayer!: Graphics;
  cellSize = 18;
  gap = 3;
  step: number;
  ready: Promise<void>;
  _lastGridData: any = null;
  _needsRedraw = false;
  playerCellId: string | null = null;
  cameraX = 0; cameraY = 0;
  _targetCX = 0; _targetCY = 0;
  _pulseTick = 0;

  setPlayerCellId(id: string | null) { this.playerCellId = id; }

  updateCamera(px: number, py: number, canvasW: number, canvasH: number) {
    this._targetCX = Math.max(0, Math.min(px * this.step - canvasW / 2, 80 * this.step - canvasW));
    this._targetCY = Math.max(0, Math.min(py * this.step - canvasH / 2, 40 * this.step - canvasH));
  }

  _lerpCamera() {
    this.cameraX += (this._targetCX - this.cameraX) * 0.15;
    this.cameraY += (this._targetCY - this.cameraY) * 0.15;
  }

  constructor(canvas: HTMLCanvasElement, width: number, height: number) {
    this.step = this.cellSize + this.gap;
    this.app = new Application();

    this.ready = this.app.init({
      canvas,
      width: width * this.step,
      height: height * this.step,
      background: 0x080812,
      antialias: true,
      resolution: 2,
      autoDensity: true,
    }).then(() => {
      this.gridLayer = new Graphics();
      this.drawLayer = new Graphics();
      this.playerLayer = new Graphics();
      this.app.stage.addChild(this.gridLayer, this.drawLayer, this.playerLayer);
      this.drawGrid(width, height);
      this.app.ticker.maxFPS = 30;
      this.app.ticker.add(() => {
        this._lerpCamera();
        this._pulseTick++;
        if (this._needsRedraw && this._lastGridData) {
          this._drawCells(this._lastGridData);
          this._needsRedraw = false;
        }
        if (this.playerCellId) {
          this._drawPlayerHighlight(this._lastGridData);
        }
      });
    });
  }

  drawGrid(w: number, h: number) {
    const g = this.gridLayer;
    const midY = (h * this.step) / 2;
    // 太阳梯度背景
    for (let y = 0; y < h; y++) {
      const baseColor = y * this.step < midY ? 0x332211 : 0x111122;
      g.rect(0, y * this.step, w * this.step, this.step)
       .fill({ color: baseColor, alpha: y * this.step < midY ? 0.12 : 0.06 });
    }
    // 细网格线
    g.setStrokeStyle({ width: 0.3, color: 0x222244, alpha: 0.25 });
    for (let x = 0; x <= w; x++) g.moveTo(x * this.step, 0).lineTo(x * this.step, h * this.step).stroke();
    for (let y = 0; y <= h; y++) g.moveTo(0, y * this.step).lineTo(w * this.step, y * this.step).stroke();
  }

  update(grid: { cells: number[][]; remnants: number[][] }) {
    this._lastGridData = grid;
    this._needsRedraw = true;
  }

  _drawPlayerHighlight(grid: any) {
    if (!grid?.cells || !this.playerCellId) return;
    const g = this.playerLayer;
    g.clear();
    for (const c of grid.cells) {
      const [x, y, _type, _energy, cellId] = c;
      if (!cellId || String(cellId) !== this.playerCellId) continue;
      const sx = x * this.step + this.step / 2 - this.cameraX;
      const sy = y * this.step + this.step / 2 - this.cameraY;
      const pulse = Math.sin(this._pulseTick * 0.1) * 0.2 + 0.6;
      g.circle(sx, sy, 20).fill({ color: 0xffd700, alpha: pulse * 0.2 });
      g.circle(sx, sy, 13).fill({ color: 0xffd700, alpha: pulse * 0.4 });
      g.circle(sx, sy, 7).fill({ color: 0xffffff, alpha: 0.85 });
    }
  }

  _drawCells(grid: { cells: number[][]; remnants: number[][] }) {
    const g = this.drawLayer;
    g.clear();

    // 残骸：小碎片
    for (const r of grid.remnants) {
      const [x, y] = r;
      const cx = x * this.step + this.step / 2 - this.cameraX;
      const cy = y * this.step + this.step / 2 - this.cameraY;
      // 十字碎片
      g.moveTo(cx - 2, cy).lineTo(cx + 2, cy).stroke({ width: 0.8, color: 0x666666, alpha: 0.3 });
      g.moveTo(cx, cy - 2).lineTo(cx, cy + 2).stroke({ width: 0.8, color: 0x666666, alpha: 0.3 });
    }

    for (const c of grid.cells) {
      const [x, y, type, energy, cellId] = c;
      const isPlayer = cellId && String(cellId) === this.playerCellId;
      const cx = x * this.step + this.step / 2 - this.cameraX;
      const cy = y * this.step + this.step / 2 - this.cameraY;
      const baseColor = TYPE_COLORS[type] ?? 0xffffff;
      const darkColor = TYPE_COLORS_DARK[type] ?? 0x888888;
      const glowColor = TYPE_COLORS_GLOW[type] ?? 0xffffff;
      const size = Math.min(5 + energy * 0.15, 10);
      const r = isPlayer ? 10 : size;

      if (isPlayer) {
        // 玩家：金色大圆
        g.circle(cx, cy, r + 1).fill({ color: 0xffd700, alpha: 0.9 });
        g.circle(cx, cy - 2, r * 0.4).fill({ color: 0xffffff, alpha: 0.3 });
      } else if (type === 0) {
        // 晶体：菱形
        const verts = [cx, cy - r, cx + r * 0.7, cy, cx, cy + r, cx - r * 0.7, cy];
        g.poly(verts).fill({ color: baseColor, alpha: 0.85 });
        g.poly(verts).stroke({ width: 0.5, color: glowColor, alpha: 0.3 });
      } else if (type === 1) {
        // 液态：椭圆 + 内部高光
        g.ellipse(cx, cy, r, r * 0.7).fill({ color: baseColor, alpha: 0.85 });
        g.ellipse(cx - 1, cy - 1, r * 0.35, r * 0.25).fill({ color: 0xffffff, alpha: 0.2 });
      } else if (type === 2) {
        // 星形：5角
        const pts: number[] = [];
        for (let i = 0; i < 10; i++) {
          const angle = (i * Math.PI) / 5 - Math.PI / 2;
          const rad = i % 2 === 0 ? r : r * 0.5;
          pts.push(cx + Math.cos(angle) * rad, cy + Math.sin(angle) * rad);
        }
        g.poly(pts).fill({ color: baseColor, alpha: 0.85 });
      } else {
        // 六边形 + 光点
        const verts: number[] = [];
        for (let i = 0; i < 6; i++) {
          const angle = (i * Math.PI) / 3 - Math.PI / 6;
          verts.push(cx + Math.cos(angle) * r, cy + Math.sin(angle) * r);
        }
        g.poly(verts).fill({ color: baseColor, alpha: 0.85 });
        g.poly(verts).stroke({ width: 0.8, color: glowColor, alpha: 0.4 });
        g.circle(cx, cy, 1.5).fill({ color: 0xffffff, alpha: 0.3 });
      }
    }
  }
}
