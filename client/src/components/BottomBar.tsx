export default function BottomBar({ stats }: { stats: any }) {
  if (!stats) return <div style={{ padding:'6px 16px', background:'#12121f', borderTop:'1px solid #1a1a2e', fontSize:13, color:'#888' }}>等待连接...</div>;
  return (
    <div style={{ padding:'6px 16px', background:'#12121f', borderTop:'1px solid #1a1a2e', fontSize:13, color:'#888' }}>
      存活: {stats.alive} | 能量: {stats.energy} | 结构: {stats.structures} ({stats.stable} 稳定) | 生命体: {stats.lifeforms}
    </div>
  );
}
