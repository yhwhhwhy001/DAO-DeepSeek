import { useEffect } from 'react';
type KeyHandler = Record<string, () => void>;

export function useKeyboard(handlers: KeyHandler) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      const h = handlers[e.key.toLowerCase()] || handlers[e.key];
      if (h) { e.preventDefault(); h(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [handlers]);
}
