import { useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import Toolbar from './components/Toolbar';
import GameCanvas from './components/GameCanvas';
import SidePanel from './components/SidePanel';
import BottomBar from './components/BottomBar';

export default function App() {
  const { state, connected, connect, pause, resume, setSpeed } = useWebSocket();

  useEffect(() => { connect(); }, []);

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100vh', background:'#0a0a0f', color:'#c8c8d0', fontFamily:'monospace' }}>
      <Toolbar tick={state?.tick ?? 0} connected={connected}
               onPause={pause} onResume={resume} onSpeed={setSpeed} />
      <div style={{ display:'flex', flex:1, overflow:'hidden' }}>
        <GameCanvas state={state} />
        <SidePanel panels={state?.panels} stats={state?.stats} />
      </div>
      <BottomBar stats={state?.stats} />
    </div>
  );
}
