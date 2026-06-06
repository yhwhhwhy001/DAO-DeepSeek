import { Application, Graphics, Container } from 'pixi.js';

const TYPE_COLORS = [0xffffff, 0xff4444, 0x44ff44, 0x4488ff];

export class PixiApp {
  app: Application;
  cellLayer: Container;
  remnantLayer: Container;
  gridLayer: Graphics;
  cellSize = 12;
  gap = 2;
  step: number;

  constructor(canvas: HTMLCanvasElement, width: number, height: number) {
    this.step = this.cellSize + this.gap;
    this.app = new Application();

    this.app.init({
      canvas,
      width: width * this.step,
      height: height * this.step,
      background: 0x0a0a1a,
      antialias: true,
    }).then(() => {
      this.gridLayer = new Graphics();
      this.remnantLayer = new Container();
      this.cellLayer = new Container();
      this.app.stage.addChild(this.gridLayer, this.remnantLayer, this.cellLayer);
      this.drawGrid(width, height);
    });

    this.cellLayer = new Container();
    this.remnantLayer = new Container();
    this.gridLayer = new Graphics();
    this.app.stage.addChild(this.gridLayer, this.remnantLayer, this.cellLayer);
    this.drawGrid(width, height);
  }

  drawGrid(w: number, h: number) {
    const g = this.gridLayer;
    g.clear();
    const midY = (h * this.step) / 2;
    for (let y = 0; y < h; y++) {
      g.rect(0, y * this.step, w * this.step, this.step)
       .fill({ color: y * this.step < midY ? 0xffaa00 : 0x0044aa, alpha: y * this.step < midY ? 0.08 : 0.03 });
    }
    g.setStrokeStyle({ width: 0.5, color: 0x1a1a2e, alpha: 0.2 });
    for (let x = 0; x <= w; x++) g.moveTo(x * this.step, 0).lineTo(x * this.step, h * this.step).stroke();
    for (let y = 0; y <= h; y++) g.moveTo(0, y * this.step).lineTo(w * this.step, y * this.step).stroke();
  }

  update(grid: { cells: any[]; remnants: any[] }) {
    this.cellLayer.removeChildren();
    this.remnantLayer.removeChildren();

    for (const r of grid.remnants) {
      const g = new Graphics();
      g.circle(r.x * this.step + this.step / 2, r.y * this.step + this.step / 2, 2)
       .fill({ color: 0x666666, alpha: 0.4 });
      this.remnantLayer.addChild(g);
    }

    for (const c of grid.cells) {
      const g = new Graphics();
      const cx = c.x * this.step + this.step / 2;
      const cy = c.y * this.step + this.step / 2;
      const color = TYPE_COLORS[c.type] ?? 0xffffff;
      const r = Math.min(4 + c.energy * 0.15, 8);

      g.circle(cx, cy, r).fill({ color, alpha: 0.85 });
      if (r > 5) g.circle(cx, cy, r + 2).fill({ color, alpha: 0.12 });
      this.cellLayer.addChild(g);
    }
  }
}
