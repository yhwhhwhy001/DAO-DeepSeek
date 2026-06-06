import { Application, Graphics } from 'pixi.js';

const TYPE_COLORS = [0xffffff, 0xff4444, 0x44ff44, 0x4488ff];
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
      canvas, width: width * this.step, height: height * this.step,
      background: 0x080812, antialias: true, resolution: 2, autoDensity: true,
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
        if (this.playerCellId) this._drawPlayerHighlight(this._lastGridData);
      });
    });
  }

  drawGrid(w: number, h: number) {
    const g = this.gridLayer;
    const midY = (h * this.step) / 2;
    for (let y = 0; y < h; y++) {
      g.rect(0, y * this.step, w * this.step, this.step)
       .fill({ color: y * this.step < midY ? 0x332211 : 0x111122, alpha: y * this.step < midY ? 0.12 : 0.06 });
    }
    g.setStrokeStyle({ width: 0.3, color: 0x222244, alpha: 0.25 });
    for (let x = 0; x <= w; x++) g.moveTo(x * this.step, 0).lineTo(x * this.step, h * this.step).stroke();
    for (let y = 0; y <= h; y++) g.moveTo(0, y * this.step).lineTo(w * this.step, y * this.step).stroke();
  }

  update(grid: { cells: number[][]; remnants: number[][]; beasts?: any[] }) {
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
      const r = 14;
      const pulse = Math.sin(this._pulseTick * 0.1) * 0.2 + 0.8;

      // 耳朵
      g.moveTo(sx - r * 0.6, sy - r * 0.4).lineTo(sx - r, sy - r * 1.2).lineTo(sx - r * 0.2, sy - r * 0.4).closePath()
       .fill({ color: 0xff8800, alpha: pulse });
      g.moveTo(sx + r * 0.6, sy - r * 0.4).lineTo(sx + r, sy - r * 1.2).lineTo(sx + r * 0.2, sy - r * 0.4).closePath()
       .fill({ color: 0xff8800, alpha: pulse });
      // 耳朵内粉
      g.moveTo(sx - r * 0.5, sy - r * 0.45).lineTo(sx - r * 0.8, sy - r * 1.0).lineTo(sx - r * 0.25, sy - r * 0.5).closePath()
       .fill({ color: 0xffccaa, alpha: pulse * 0.7 });
      g.moveTo(sx + r * 0.5, sy - r * 0.45).lineTo(sx + r * 0.8, sy - r * 1.0).lineTo(sx + r * 0.25, sy - r * 0.5).closePath()
       .fill({ color: 0xffccaa, alpha: pulse * 0.7 });

      // 脸
      g.circle(sx, sy, r).fill({ color: 0xff8800, alpha: pulse });

      // 王字
      g.moveTo(sx - 5, sy - r * 0.7).lineTo(sx + 5, sy - r * 0.7).stroke({ width: 1.8, color: 0x663300, alpha: 0.8 });
      g.moveTo(sx, sy - r * 0.9).lineTo(sx, sy - r * 0.5).stroke({ width: 1.8, color: 0x663300, alpha: 0.8 });
      g.moveTo(sx - 4, sy - r * 0.3).lineTo(sx + 4, sy - r * 0.3).stroke({ width: 1.2, color: 0x994400, alpha: 0.5 });
      g.moveTo(sx - 4, sy - r * 0.1).lineTo(sx + 4, sy - r * 0.1).stroke({ width: 1.2, color: 0x994400, alpha: 0.5 });

      // 白脸颊
      g.ellipse(sx - r * 0.35, sy + r * 0.1, r * 0.25, r * 0.2).fill({ color: 0xffeedd, alpha: 0.6 });
      g.ellipse(sx + r * 0.35, sy + r * 0.1, r * 0.25, r * 0.2).fill({ color: 0xffeedd, alpha: 0.6 });

      // 白口鼻
      g.ellipse(sx, sy + r * 0.2, r * 0.55, r * 0.4).fill({ color: 0xffffff, alpha: 0.85 });

      // 眼
      g.ellipse(sx - r * 0.32, sy - r * 0.1, 3.5, 4).fill({ color: 0xffffff, alpha: 1 });
      g.ellipse(sx + r * 0.32, sy - r * 0.1, 3.5, 4).fill({ color: 0xffffff, alpha: 1 });
      g.circle(sx - r * 0.32, sy - r * 0.1, 2).fill({ color: 0x111111, alpha: 1 });
      g.circle(sx + r * 0.32, sy - r * 0.1, 2).fill({ color: 0x111111, alpha: 1 });
      g.circle(sx - r * 0.35, sy - r * 0.15, 0.8).fill({ color: 0xffffff, alpha: 0.9 });
      g.circle(sx + r * 0.29, sy - r * 0.15, 0.8).fill({ color: 0xffffff, alpha: 0.9 });

      // 鼻
      g.moveTo(sx, sy + r * 0.15).lineTo(sx - 2.5, sy + r * 0.3).lineTo(sx + 2.5, sy + r * 0.3).closePath()
       .fill({ color: 0xff6688, alpha: 0.9 });

      // 嘴
      g.moveTo(sx, sy + r * 0.3).lineTo(sx, sy + r * 0.45).stroke({ width: 1, color: 0x886666, alpha: 0.6 });
      g.moveTo(sx - 3, sy + r * 0.42).lineTo(sx, sy + r * 0.45).lineTo(sx + 3, sy + r * 0.42).stroke({ width: 0.8, color: 0x886666, alpha: 0.5 });

      // 须
      g.moveTo(sx - r * 0.5, sy + r * 0.05).lineTo(sx - r * 0.8, sy).stroke({ width: 0.5, color: 0xcccccc, alpha: 0.4 });
      g.moveTo(sx - r * 0.5, sy + r * 0.15).lineTo(sx - r * 0.85, sy + r * 0.1).stroke({ width: 0.5, color: 0xcccccc, alpha: 0.4 });
      g.moveTo(sx + r * 0.5, sy + r * 0.05).lineTo(sx + r * 0.8, sy).stroke({ width: 0.5, color: 0xcccccc, alpha: 0.4 });
      g.moveTo(sx + r * 0.5, sy + r * 0.15).lineTo(sx + r * 0.85, sy + r * 0.1).stroke({ width: 0.5, color: 0xcccccc, alpha: 0.4 });

      // 外光环
      g.circle(sx, sy, r + 4).fill({ color: 0xffd700, alpha: 0.08 });
    }
  }

  _drawCells(grid: { cells: number[][]; remnants: number[][]; beasts?: any[] }) {
    const g = this.drawLayer;
    g.clear();

    for (const r of grid.remnants) {
      const [x, y] = r;
      const cx = x * this.step + this.step / 2 - this.cameraX;
      const cy = y * this.step + this.step / 2 - this.cameraY;
      g.moveTo(cx - 2, cy).lineTo(cx + 2, cy).stroke({ width: 0.8, color: 0x666666, alpha: 0.3 });
      g.moveTo(cx, cy - 2).lineTo(cx, cy + 2).stroke({ width: 0.8, color: 0x666666, alpha: 0.3 });
    }

    if (grid.beasts) {
      for (const b of grid.beasts) {
        const sx = b.x * this.step + this.step / 2 - this.cameraX;
        const sy = b.y * this.step + this.step / 2 - this.cameraY;
        const pulse = Math.sin(this._pulseTick * 0.15) * 0.3 + 0.7;
        g.circle(sx, sy, b.aggro_range * this.step * 0.5).fill({ color: 0xff0000, alpha: 0.04 });
        const br = 7;
        g.moveTo(sx, sy - br).lineTo(sx + br, sy + br * 0.6).lineTo(sx - br, sy + br * 0.6).closePath()
         .fill({ color: 0xff2222, alpha: pulse });
        g.circle(sx, sy - 1, 2).fill({ color: 0xffffff, alpha: 0.8 });
      }
    }

    for (const c of grid.cells) {
      const [x, y, type, energy, cellId] = c;
      const isPlayer = cellId && String(cellId) === this.playerCellId;
      const cx = x * this.step + this.step / 2 - this.cameraX;
      const cy = y * this.step + this.step / 2 - this.cameraY;
      const baseColor = TYPE_COLORS[type] ?? 0xffffff;
      const glowColor = TYPE_COLORS_GLOW[type] ?? 0xffffff;
      const size = Math.min(5 + energy * 0.15, 10);
      const r = isPlayer ? 0 : size; // 玩家由 playerLayer 渲染，此处跳过

      if (isPlayer) continue; // 玩家不在这里画

      if (type === 0) {
        const verts = [cx, cy - r, cx + r * 0.7, cy, cx, cy + r, cx - r * 0.7, cy];
        g.poly(verts).fill({ color: baseColor, alpha: 0.85 });
        g.poly(verts).stroke({ width: 0.5, color: glowColor, alpha: 0.3 });
      } else if (type === 1) {
        g.ellipse(cx, cy, r, r * 0.7).fill({ color: baseColor, alpha: 0.85 });
        g.ellipse(cx - 1, cy - 1, r * 0.35, r * 0.25).fill({ color: 0xffffff, alpha: 0.2 });
      } else if (type === 2) {
        const pts: number[] = [];
        for (let i = 0; i < 10; i++) {
          const angle = (i * Math.PI) / 5 - Math.PI / 2;
          const rad = i % 2 === 0 ? r : r * 0.5;
          pts.push(cx + Math.cos(angle) * rad, cy + Math.sin(angle) * rad);
        }
        g.poly(pts).fill({ color: baseColor, alpha: 0.85 });
      } else {
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
