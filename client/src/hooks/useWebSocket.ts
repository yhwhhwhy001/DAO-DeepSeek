import { useState, useRef, useCallback } from 'react';

export interface SimulationState {
  tick: number;
  grid: { width: number; height: number; cells: number[][]; remnants: number[][] };
  stats: { alive: number; energy: number; structures: number; stable: number; lifeforms: number };
  panels: { entropy: any; leaderboard: any; life: any; cognition: any };
}

export function useWebSocket() {
  const [state, setState] = useState<SimulationState | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const host = window.location.hostname;
    const url = `ws://${host}:8000/ws`;
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = () => {
        setConnected(true);
        setError(null);
        ws.send(JSON.stringify({ type: 'start', config: 'experiments/web.yaml' }));
      };
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'tick') {
          setState(prev => {
            // 如果新数据没有网格，复用旧网格
            if (!data.grid?.cells?.length && prev?.grid) {
              return { ...data, grid: prev.grid };
            }
            return data;
          });
        }
      };
      ws.onclose = () => {
        setConnected(false);
        if (!wsRef.current) return;
        // 5 秒后自动重连
        setTimeout(() => {
          if (wsRef.current?.readyState === WebSocket.CLOSED) connect();
        }, 5000);
      };
      ws.onerror = () => setError('无法连接到后端服务 (端口 8000)');
    } catch {
      setError('WebSocket 连接失败');
    }
  }, []);

  const pause = () => { console.log('[btn] pause'); wsRef.current?.send(JSON.stringify({ type: 'pause' })); };
  const resume = () => { console.log('[btn] resume'); wsRef.current?.send(JSON.stringify({ type: 'resume' })); };
  const setSpeed = (tps: number) => { console.log('[btn] speed', tps); wsRef.current?.send(JSON.stringify({ type: 'set_speed', tps })); };

  return { state, connected, error, connect, pause, resume, setSpeed };
}
