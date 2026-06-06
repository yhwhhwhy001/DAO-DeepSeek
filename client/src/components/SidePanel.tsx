import PanelSection from './PanelSection';

export default function SidePanel({ panels, stats }: { panels: any; stats: any }) {
  const e = panels?.entropy;
  const lb = panels?.leaderboard;
  const life = panels?.life;
  const cog = panels?.cognition;

  return (
    <div style={{ width:280, background:'#0d0d18', borderLeft:'1px solid #1a1a2e', overflowY:'auto', padding:8, flexShrink:0 }}>
      <PanelSection title="熵" defaultOpen>
        {e && <>
          <div>全局熵: {e.global} bit</div>
          <div>局部熵: {e.local_mean} ± {e.local_std}</div>
          <div>结构熵: {e.structure} bit</div>
          <div>趋势: {e.trend}</div>
        </>}
      </PanelSection>

      <PanelSection title="排行榜" defaultOpen>
        {lb?.map((r: any, i: number) => (
          <div key={i}>{i+1}. {r.id} age={r.age} sz={r.size} 得分={r.score}</div>
        ))}
      </PanelSection>

      <PanelSection title="生命">
        {life && <>
          <div>准生命: {life.proto}  真生命: {life.true_count}</div>
          {life.top?.map((lf: any, i: number) => (
            <div key={i}>{i+1}. {lf.id} 得分={lf.score}</div>
          ))}
        </>}
      </PanelSection>

      <PanelSection title="认知">
        {cog && <>
          <div>符号: {cog.symbols}  信号: {cog.signals}</div>
        </>}
      </PanelSection>

      <PanelSection title="统计">
        {stats && <>
          <div>存活: {stats.alive}  能量: {stats.energy}</div>
          <div>结构: {stats.structures} ({stats.stable} 稳定)</div>
          <div>生命体: {stats.lifeforms}</div>
        </>}
      </PanelSection>
    </div>
  );
}
