import { useEffect, Component } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import Toolbar from './components/Toolbar';
import GameCanvas from './components/GameCanvas';
import SidePanel from './components/SidePanel';
import BottomBar from './components/BottomBar';

class ErrorBoundary extends Component<{children: React.ReactNode}, {error: string | null}> {
  state = { error: null };
  static getDerivedStateFromError(e: Error) { return { error: e.message + ' | ' + e.stack?.slice(0,300) }; }
  render() {
    if (this.state.error) {
      return <div style={{padding:40,color:'red',background:'#111',height:'100vh',whiteSpace:'pre-wrap',fontFamily:'monospace'}}>
        <h2>渲染错误</h2>{this.state.error}</div>;
    }
    return this.props.children;
  }
}

export default function App() {
  const { state, connected, error, connect, pause, resume, setSpeed } = useWebSocket();

  useEffect(() => { connect(); }, []);

  return (
    <ErrorBoundary>
      <div style={{ display:'flex', flexDirection:'column', height:'100vh', background:'#0a0a0f', color:'#c8c8d0', fontFamily:'monospace' }}>
        <Toolbar tick={state?.tick ?? 0} connected={connected}
                 onPause={pause} onResume={resume} onSpeed={setSpeed} />
        {error && (
          <div style={{ padding: '12px 16px', background: '#331111', color: '#ff6666', fontSize: 13, textAlign: 'center' }}>
            {error} —— 请先运行 <code>python3 run_web.py</code>
          </div>
        )}
        <div style={{ display:'flex', flex:1, overflow:'hidden' }}>
          <GameCanvas state={state} />
          <SidePanel panels={state?.panels} stats={state?.stats} />
        </div>
        <BottomBar stats={state?.stats} />
      </div>
    </ErrorBoundary>
  );
}
