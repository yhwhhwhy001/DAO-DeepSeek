export default function HUDOverlay({ player, onEquipSkill }: { player: any; onEquipSkill: (name: string) => void }) {
  if (!player) return null;
  const realmColors: Record<string,string> = {"练气":"#aaa","筑基":"#44ff44","金丹":"#ffd700","元婴":"#ff44ff","化神":"#ff6644","渡劫":"#ff2222"};
  const color = realmColors[player.realm] || '#fff';
  const maxSlots = Math.min(1 + player.realm_index, 4);

  return (
    <div style={{ position:'absolute', top:0, left:0, right:0, padding:'6px 16px',
      background:'linear-gradient(180deg, rgba(0,0,0,0.88) 0%, transparent 100%)',
      color:'#fff', fontSize:12, fontFamily:'monospace', zIndex:10 }}>
      <div style={{ display:'flex', gap:16, alignItems:'center', flexWrap:'wrap', pointerEvents:'none' }}>
        <span style={{ color, fontSize:15 }}>✦ {player.realm}期</span>
        <span>灵力: {player.energy}/{player.max_energy}</span>
        <span>劫难: {Math.round(player.realm_index * 10)}%</span>
        <span>丹药: {player.herbs}</span>
        {player.shield_ticks > 0 && <span style={{color:'#44aaff'}}>护体: {player.shield_ticks}t</span>}
        <span style={{color:'#888'}}>#{player.reincarnation}</span>
      </div>
      <div style={{ display:'flex', gap:6, marginTop:3, alignItems:'center' }}>
        <span style={{color:'#888', fontSize:11, pointerEvents:'none'}}>功法:</span>
        {Array.from({length: maxSlots}).map((_, i) => {
          const skill = player.skills?.[i];
          return (
            <span key={i} style={{
              padding:'1px 8px', borderRadius:3, fontSize:11,
              background: skill ? '#2a2a4e' : '#111122',
              border: skill ? '1px solid #5a5a8e' : '1px dashed #333',
              color: skill ? '#ffd700' : '#444',
            }}>{skill || '空'}</span>
          );
        })}
        {player.discovered_skills?.filter((s: string) => !player.skills?.includes(s)).map((s: string) => (
          <button key={s} onClick={(e) => { e.stopPropagation(); onEquipSkill(s); }}
            style={{ padding:'1px 8px', borderRadius:3, fontSize:11, cursor:'pointer',
              background:'#1a3a1a', border:'1px solid #3a6a3a', color:'#88ff88',
              fontFamily:'monospace' }}>
            +{s}
          </button>
        ))}
      </div>
    </div>
  );
}
