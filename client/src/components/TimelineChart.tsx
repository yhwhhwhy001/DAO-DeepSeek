export default function TimelineChart({ history }: { history: {tick:number;active:number;fallen:number}[] }) {
  if (!history || history.length < 2) return null;
  const w = 260; const h = 80; const pad = 10;
  const maxVal = Math.max(...history.map(d => d.active + d.fallen), 1);
  const minTick = history[0].tick;
  const maxTick = history[history.length-1].tick;
  const xScale = (t: number) => pad + ((t - minTick) / Math.max(maxTick - minTick, 1)) * (w - pad*2);
  const yScale = (v: number) => h - pad - (v / maxVal) * (h - pad*2);

  const activePath = history.map((d,i) => `${i===0?'M':'L'}${xScale(d.tick)},${yScale(d.active)}`).join(' ');
  const fallenPath = history.map((d,i) => `${i===0?'M':'L'}${xScale(d.tick)},${yScale(d.fallen)}`).join(' ');

  return (
    <svg width={w} height={h} style={{ display:'block', margin:'4px 0' }}>
      {/* 基线 */}
      <line x1={pad} y1={h-pad} x2={w-pad} y2={h-pad} stroke="#333" strokeWidth={0.5} />
      {/* 活跃文明 */}
      <path d={activePath} fill="none" stroke="#44ff44" strokeWidth={1.5} />
      {/* 灭亡文明 */}
      <path d={fallenPath} fill="none" stroke="#ff4444" strokeWidth={1} strokeDasharray="2,2" />
      {/* 标签 */}
      <text x={w-60} y={12} fill="#44ff44" fontSize={9} fontFamily="monospace">活跃</text>
      <text x={w-60} y={24} fill="#ff4444" fontSize={9} fontFamily="monospace">灭亡</text>
    </svg>
  );
}
