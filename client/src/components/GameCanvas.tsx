import { useRef, useEffect } from 'react';
import { PixiApp } from '../engine/PixiApp';

export default function GameCanvas({ state }: { state: any }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const appRef = useRef<PixiApp | null>(null);

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
    if (state?.grid?.cells && appRef.current) {
      appRef.current.update(state.grid);
    }
  }, [state]);

  return <canvas ref={canvasRef} style={{ display:'block' }} />;
}
