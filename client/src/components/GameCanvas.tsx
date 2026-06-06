import { useRef, useEffect } from 'react';
import { PixiApp } from '../engine/PixiApp';

export default function GameCanvas({ state }: { state: any }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const appRef = useRef<PixiApp | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const w = state?.grid?.width ?? 80;
    const h = state?.grid?.height ?? 40;
    if (!appRef.current) {
      appRef.current = new PixiApp(canvasRef.current, w, h);
    }
    return () => { appRef.current?.app.destroy(); };
  }, []);

  useEffect(() => {
    if (state?.player?.cell_id && appRef.current) {
      appRef.current.setPlayerCellId(state.player.cell_id);
    }
  }, [state?.player?.cell_id]);

  useEffect(() => {
    if (state?.grid?.cells && appRef.current && state?.player?.cell_id) {
      const playerCell = state.grid.cells.find((c: any) => c[4] === state.player.cell_id);
      if (playerCell && canvasRef.current) {
        const parent = canvasRef.current.parentElement;
        const pw = parent?.clientWidth ?? 800;
        const ph = parent?.clientHeight ?? 600;
        appRef.current.updateCamera(playerCell[0], playerCell[1], pw, ph);
      }
    }
  }, [state]);

  useEffect(() => {
    if (state?.grid?.cells && appRef.current) {
      appRef.current.update(state.grid);
    }
  }, [state]);

  useEffect(() => {
    if (containerRef.current && canvasRef.current) {
      canvasRef.current.width = containerRef.current.clientWidth;
      canvasRef.current.height = containerRef.current.clientHeight;
    }
  }, []);

  return (
    <div ref={containerRef} style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
      <canvas ref={canvasRef} style={{ display: 'block', width: '100%', height: '100%' }} />
    </div>
  );
}
