export default function Toolbar({ tick, connected, onPause, onResume, onSpeed }:
  { tick: number; connected: boolean; onPause: () => void; onResume: () => void; onSpeed: (t: number) => void }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:12, padding:'8px 16px', background:'#12121f', borderBottom:'1px solid #1a1a2e' }}>
      <span style={{ fontSize:16, fontWeight:'bold', color:'#44aaff' }}>DAO 创世纪</span>
      <span style={{ color:'#aaa', fontSize:14 }}>Tick: {tick}</span>
      <span style={{ fontSize:12, color: connected ? '#44ff44' : '#ff4444' }}>{connected ? '已连接' : '断开'}</span>
      <button onClick={onPause} style={btnStyle}>⏸ 暂停</button>
      <button onClick={onResume} style={btnStyle}>▶ 恢复</button>
      <button onClick={() => onSpeed(30)} style={btnStyle}>1x</button>
      <button onClick={() => onSpeed(120)} style={btnStyle}>4x</button>
      <button onClick={() => onSpeed(600)} style={btnStyle}>20x</button>
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  background:'#1a1a2e', color:'#c8c8d0', border:'1px solid #2a2a3e',
  padding:'4px 12px', borderRadius:4, cursor:'pointer', fontFamily:'inherit'
};
