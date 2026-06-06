import { useRef, useEffect, useState } from 'react';
import { PixiApp } from '../engine/PixiApp';

export default function GameCanvas({ state }: { state: any }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const appRef = useRef<PixiApp | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!canvasRef.current) return;
    const w = state?.grid?.width ?? 80;
    const h = state?.grid?.height ?? 40;
    if (!appRef.current) {
      const app = new PixiApp(canvasRef.current, w, h);
      appRef.current = app;
      app.ready.then(() => setReady(true));
    }
    return () => { appRef.current?.app.destroy(); };
  }, []);

  useEffect(() => {
    if (state?.grid && appRef.current && ready) {
      appRef.current.update(state.grid);
    }
  }, [state, ready]);

  return (
    <div style={{ flex: 1, position: 'relative', background: '#0a0a1a' }}>
      <canvas ref={canvasRef} style={{ display: 'block' }} />
      {!ready && (
        <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666', fontSize: 14 }}>
          加载中...
        </div>
      )}
    </div>
  );
}
