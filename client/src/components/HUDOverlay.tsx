export default function HUDOverlay({ player }: { player: any }) {
  if (!player) return null;
  const realmColors: Record<string,string> = {"练气":"#aaa","筑基":"#44ff44","金丹":"#ffd700","元婴":"#ff44ff","化神":"#ff6644","渡劫":"#ff2222"};
  const color = realmColors[player.realm] || '#fff';
  return (
    <div style={{ position:'absolute', top:0, left:0, right:0, padding:'8px 16px',
      background:'linear-gradient(180deg, rgba(0,0,0,0.85) 0%, transparent 100%)',
      display:'flex', gap:16, alignItems:'center', color:'#fff', fontSize:13, fontFamily:'monospace', zIndex:10, pointerEvents:'none' }}>
      <span style={{ color, fontSize:16 }}>✦ {player.realm}期</span>
      <span>灵力: {player.energy}/{player.max_energy}</span>
      <span>劫难: {Math.round(player.realm_index * 10)}%</span>
      <span>丹药: {player.herbs}</span>
      {player.shield_ticks > 0 && <span style={{color:'#44aaff'}}>护体: {player.shield_ticks}t</span>}
      <span style={{color:'#888'}}>轮回: #{player.reincarnation}</span>
    </div>
  );
}
