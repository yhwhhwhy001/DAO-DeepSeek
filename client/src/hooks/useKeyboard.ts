import { useEffect } from 'react';
type KeyHandler = Record<string, (e?: KeyboardEvent) => void>;

export function useKeyboard(handlers: KeyHandler) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      const key = e.key === 'Tab' ? 'tab' : e.key.toLowerCase();
      const h = handlers[key];
      if (h) {
        e.preventDefault();
        e.stopPropagation();
        h(e);
      }
    };
    window.addEventListener('keydown', onKey, { capture: true });
    return () => window.removeEventListener('keydown', onKey, { capture: true });
  }, [handlers]);
}
