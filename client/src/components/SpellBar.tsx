export default function SpellBar({ castSpell, player }: { castSpell: (s: string) => void; player: any }) {
  const allSpells = ['吐纳术','护体罡气','神念探查','血遁术','夺舍术','聚灵丹','悟道丹'];
  const unlocked = player ? Math.min(2 + player.realm_index, allSpells.length) : 3;
  return (
    <div style={{ position:'absolute', bottom:0, left:0, right:0, padding:'8px 16px',
      background:'linear-gradient(0deg, rgba(0,0,0,0.85) 0%, transparent 100%)',
      display:'flex', gap:8, justifyContent:'center', zIndex:10, flexWrap:'wrap' }}>
      <span style={{ color:'#888', fontSize:12, alignSelf:'center' }}>WASD 移动</span>
      {allSpells.slice(0, unlocked).map((s, i) => (
        <button key={s} onClick={() => castSpell(allSpells[i])} style={{
          background:'#1a1a2e', color: i < 5 ? '#c8c8d0' : '#ffaa44', border:'1px solid #3a3a5e',
          padding:'4px 10px', borderRadius:4, cursor:'pointer', fontFamily:'monospace', fontSize:12 }}>
          [{i+1}] {s}
        </button>
      ))}
      <span style={{ color:'#888', fontSize:12, alignSelf:'center' }}>Tab 观察模式</span>
    </div>
  );
}
