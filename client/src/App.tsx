import { useEffect, useState, useCallback } from 'react';
import { useWebSocket, useCultivator, useKeyboard } from './hooks';
import Toolbar from './components/Toolbar';
import GameCanvas from './components/GameCanvas';
import SidePanel from './components/SidePanel';
import BottomBar from './components/BottomBar';
import HUDOverlay from './components/HUDOverlay';
import SpellBar from './components/SpellBar';
import ReincarnationModal from './components/ReincarnationModal';

export default function App() {
  const { state, connected, error, connect, pause, resume, setSpeed, sendMsg } = useWebSocket();
  const { player, deadStats, updateFromTick, moveTo, castSpell, equipSkill, reincarnate } = useCultivator(sendMsg);
  const [hudMode, setHudMode] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => { connect(); }, []);
  useEffect(() => { if (state) updateFromTick(state); }, [state]);

  const spellWithFeedback = useCallback((spell: string) => {
    const names: Record<string, string> = {
      '吐纳术': '吐纳术 —— 吸收周围灵气', '护体罡气': '护体罡气 —— 10tick 伤害减半',
      '神念探查': '神念探查 —— 灵识展开', '血遁术': '血遁术 —— 破空而去',
      '夺舍术': '夺舍术 —— 神魂转移', '聚灵丹': '聚灵丹 —— 灵力回复',
      '悟道丹': '悟道丹 —— 顿悟加速',
    };
    castSpell(spell);
    setToast(names[spell] || spell);
    setTimeout(() => setToast(null), 1200);
  }, [castSpell]);

  useKeyboard({
    w: () => moveTo(0, -1), s: () => moveTo(0, 1),
    a: () => moveTo(-1, 0), d: () => moveTo(1, 0),
    '1': () => spellWithFeedback('吐纳术'), '2': () => spellWithFeedback('护体罡气'),
    '3': () => spellWithFeedback('神念探查'), '4': () => spellWithFeedback('血遁术'),
    '5': () => spellWithFeedback('夺舍术'), '6': () => spellWithFeedback('聚灵丹'),
    '7': () => spellWithFeedback('悟道丹'),
    tab: () => setHudMode(m => !m),
  });

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100vh', background:'#0a0a0f', color:'#c8c8d0', fontFamily:'monospace' }}>
      <Toolbar tick={state?.tick ?? 0} connected={connected}
               onPause={pause} onResume={resume} onSpeed={setSpeed} />
      {error && (
        <div style={{ padding: '12px 16px', background: '#331111', color: '#ff6666', fontSize: 13, textAlign: 'center' }}>
          {error} —— 请先运行 <code>python3 run_web.py</code>
        </div>
      )}
      <div style={{ display:'flex', flex:1, overflow:'hidden', position:'relative' }}>
        <GameCanvas state={state} />
        {hudMode && <HUDOverlay player={player} onEquipSkill={equipSkill} />}
        {hudMode && <SpellBar castSpell={spellWithFeedback} player={player} />}
        {toast && (
          <div style={{ position:'absolute', top:'40%', left:'50%', transform:'translate(-50%,-50%)',
            color:'#ffd700', fontSize:18, fontFamily:'monospace', textShadow:'0 0 10px #ffd700',
            pointerEvents:'none', zIndex:20, animation:'fadeOut 1.2s ease-out' }}>
            {toast}
          </div>
        )}
        {!hudMode && <SidePanel panels={state?.panels} stats={state?.stats} />}
      </div>
      {!hudMode && <BottomBar stats={state?.stats} />}
      <ReincarnationModal stats={deadStats} onReincarnate={reincarnate} />
    </div>
  );
}
