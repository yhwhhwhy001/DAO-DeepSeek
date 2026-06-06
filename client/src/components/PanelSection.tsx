import { useState } from 'react';

export default function PanelSection({ title, defaultOpen = false, children }:
  { title: string; defaultOpen?: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ marginBottom: 4 }}>
      <div onClick={() => setOpen(!open)}
           style={{ padding:'6px 8px', cursor:'pointer', fontSize:13, color:'#88aacc', borderRadius:4 }}>
        {open ? '▼' : '▶'} {title}
      </div>
      {open && <div style={{ padding:'6px 12px', fontSize:12, lineHeight:1.6 }}>{children}</div>}
    </div>
  );
}
