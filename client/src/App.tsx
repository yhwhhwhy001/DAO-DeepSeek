import { useEffect, useState } from 'react';
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
  const { player, deadStats, updateFromTick, moveTo, castSpell, reincarnate } = useCultivator(sendMsg);
  const [hudMode, setHudMode] = useState(true);

  useEffect(() => { connect(); }, []);
  useEffect(() => { if (state) updateFromTick(state); }, [state]);

  useKeyboard({
    w: () => moveTo(0, -1), s: () => moveTo(0, 1),
    a: () => moveTo(-1, 0), d: () => moveTo(1, 0),
    '1': () => castSpell('吐纳术'), '2': () => castSpell('护体罡气'),
    '3': () => castSpell('神念探查'), '4': () => castSpell('血遁术'),
    '5': () => castSpell('夺舍术'), '6': () => castSpell('聚灵丹'),
    '7': () => castSpell('悟道丹'),
    'tab': () => setHudMode(m => !m),
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
        {hudMode && <HUDOverlay player={player} />}
        {hudMode && <SpellBar castSpell={castSpell} player={player} />}
        {!hudMode && <SidePanel panels={state?.panels} stats={state?.stats} />}
      </div>
      {!hudMode && <BottomBar stats={state?.stats} />}
      <ReincarnationModal stats={deadStats} onReincarnate={reincarnate} />
    </div>
  );
}
