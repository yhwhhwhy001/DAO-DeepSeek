import { useState, useRef, useCallback } from 'react';

export interface SimulationState {
  tick: number;
  grid: { width: number; height: number; cells: {x:number;y:number;type:number;energy:number;id:string}[]; remnants: {x:number;y:number;energy:number;type:number}[] };
  stats: { alive: number; energy: number; structures: number; stable: number; lifeforms: number };
  panels: { entropy: any; leaderboard: any; life: any; cognition: any };
}

export function useWebSocket() {
  const [state, setState] = useState<SimulationState | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const host = window.location.hostname;
    const ws = new WebSocket(`ws://${host}:8000/ws`);
    wsRef.current = ws;
    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: 'start', config: 'experiments/highspeed.yaml' }));
    };
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'tick') setState(data);
    };
    ws.onclose = () => setConnected(false);
  }, []);

  const pause = () => wsRef.current?.send(JSON.stringify({ type: 'pause' }));
  const resume = () => wsRef.current?.send(JSON.stringify({ type: 'resume' }));
  const setSpeed = (tps: number) => wsRef.current?.send(JSON.stringify({ type: 'set_speed', tps }));

  return { state, connected, connect, pause, resume, setSpeed };
}
