export default function ReincarnationModal({ stats, onReincarnate }: { stats: any; onReincarnate: () => void }) {
  if (!stats) return null;
  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,0.85)', display:'flex',
      alignItems:'center', justifyContent:'center', zIndex:100 }}>
      <div style={{ background:'#1a1a2e', border:'1px solid #4a4a6e', borderRadius:8, padding:24,
        textAlign:'center', color:'#c8c8d0', fontFamily:'monospace', minWidth:300 }}>
        <div style={{ fontSize:24, color:'#ffd700', marginBottom:16 }}>✦ 魂归天地</div>
        <div>境界: {stats.realm}</div>
        <div>存活: {stats.tick_age ?? '?'} tick</div>
        <div>功法保留: {stats.skills?.join(', ') || '无'}</div>
        <div>灵力保留: {(stats.energy_kept ?? 0).toFixed(1)} (30%)</div>
        <div>轮回次数: #{stats.reincarnation}</div>
        <button onClick={onReincarnate} style={{ marginTop:20, padding:'10px 24px', fontSize:16,
          background:'#ffd700', color:'#000', border:'none', borderRadius:4, cursor:'pointer' }}>
          投胎转世
        </button>
      </div>
    </div>
  );
}
