import { useRef, useEffect } from 'react';
import { PixiApp } from '../engine/PixiApp';

export default function GameCanvas({ state }: { state: any }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const appRef = useRef<PixiApp | null>(null);
  const dims = useRef<{ w: number; h: number } | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const w = state?.grid?.width ?? 80;
    const h = state?.grid?.height ?? 40;
    if (!appRef.current || dims.current?.w !== w || dims.current?.h !== h) {
      appRef.current?.app.destroy();
      appRef.current = new PixiApp(canvasRef.current, w, h);
      dims.current = { w, h };
    }
    return () => { appRef.current?.app.destroy(); };
  }, [state?.grid?.width, state?.grid?.height]);

  useEffect(() => {
    if (state?.grid && appRef.current) appRef.current.update(state.grid);
  }, [state]);

  return <canvas ref={canvasRef} style={{ display:'block', flex:1 }} />;
}
