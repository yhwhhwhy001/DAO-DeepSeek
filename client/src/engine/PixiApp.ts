import { Application, Graphics } from 'pixi.js';

const TYPE_COLORS = [0xffffff, 0xff4444, 0x44ff44, 0x4488ff];

export class PixiApp {
  app!: Application;
  gridLayer!: Graphics;
  drawLayer!: Graphics;
  cellSize = 12;
  gap = 2;
  step: number;
  ready: Promise<void>;
  _lastGridData: any = null;
  _needsRedraw = false;
  playerCellId: string | null = null;
  cameraX = 0; cameraY = 0;

  setPlayerCellId(id: string | null) { this.playerCellId = id; }

  updateCamera(px: number, py: number, canvasW: number, canvasH: number) {
    this.cameraX = Math.max(0, Math.min(px * this.step - canvasW / 2, 80 * this.step - canvasW));
    this.cameraY = Math.max(0, Math.min(py * this.step - canvasH / 2, 40 * this.step - canvasH));
  }

  constructor(canvas: HTMLCanvasElement, width: number, height: number) {
    this.step = this.cellSize + this.gap;
    this.app = new Application();

    this.ready = this.app.init({
      canvas,
      width: width * this.step,
      height: height * this.step,
      background: 0x0a0a1a,
      antialias: false,  // 关闭抗锯齿提升性能
    }).then(() => {
      this.gridLayer = new Graphics();
      this.drawLayer = new Graphics();
      this.app.stage.addChild(this.gridLayer, this.drawLayer);
      this.drawGrid(width, height);
      this.app.ticker.maxFPS = 30;  // 限制 30fps
      this.app.ticker.add(() => {
        if (this._needsRedraw && this._lastGridData) {
          this._drawCells(this._lastGridData);
          this._needsRedraw = false;
        }
      });
    });
  }

  drawGrid(w: number, h: number) {
    const g = this.gridLayer;
    const midY = (h * this.step) / 2;
    for (let y = 0; y < h; y++) {
      g.rect(0, y * this.step, w * this.step, this.step)
       .fill({ color: y * this.step < midY ? 0xffaa00 : 0x0044aa, alpha: y * this.step < midY ? 0.08 : 0.03 });
    }
    g.setStrokeStyle({ width: 0.5, color: 0x1a1a2e, alpha: 0.2 });
    for (let x = 0; x <= w; x++) g.moveTo(x * this.step, 0).lineTo(x * this.step, h * this.step).stroke();
    for (let y = 0; y <= h; y++) g.moveTo(0, y * this.step).lineTo(w * this.step, y * this.step).stroke();
  }

  update(grid: { cells: number[][]; remnants: number[][] }) {
    this._lastGridData = grid;
    this._needsRedraw = true;
  }

  _drawCells(grid: { cells: number[][]; remnants: number[][] }) {
    const g = this.drawLayer;
    g.clear();

    for (const r of grid.remnants) {
      const [x, y] = r;
      g.circle(x * this.step + this.step/2 - this.cameraX, y * this.step + this.step/2 - this.cameraY, 1.5)
       .fill({ color: 0x666666, alpha: 0.3 });
    }

    for (const c of grid.cells) {
      const [x, y, type, energy, cellId] = c;
      const sx = x * this.step + this.step/2 - this.cameraX;
      const sy = y * this.step + this.step/2 - this.cameraY;
      const color = TYPE_COLORS[type] ?? 0xffffff;
      const r = Math.min(3 + energy * 0.15, 7);

      if (cellId !== undefined && String(cellId) === this.playerCellId) {
        // 金色光晕
        g.circle(sx, sy, 10).fill({ color: 0xffd700, alpha: 0.3 });
        g.circle(sx, sy, 6).fill({ color: 0xffd700, alpha: 0.7 });
      }
      g.circle(sx, sy, r).fill({ color, alpha: 0.85 });
    }
  }
}
