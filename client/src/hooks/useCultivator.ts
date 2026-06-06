import { useState, useCallback } from 'react';

export interface PlayerState {
  energy: number; max_energy: number; realm: string; realm_index: number;
  skills: string[]; herbs: number; shield_ticks: number; reincarnation: number; cell_id: string;
}

export function useCultivator(sendMsg: (msg: object) => void) {
  const [player, setPlayer] = useState<PlayerState | null>(null);
  const [deadStats, setDeadStats] = useState<any>(null);

  const updateFromTick = useCallback((data: any) => {
    if (data.player) {
      setPlayer(data.player);
      setDeadStats(null);
    } else if (player && !data.player) {
      // Player just died
      setDeadStats({ ...player, energy_kept: player.energy * 0.3 });
      setPlayer(null);
    }
  }, [player]);

  const moveTo = useCallback((dx: number, dy: number) => {
    sendMsg({ type: 'player_move', dx, dy });
  }, [sendMsg]);

  const castSpell = useCallback((spell: string) => {
    sendMsg({ type: 'player_spell', spell });
  }, [sendMsg]);

  const reincarnate = useCallback(() => {
    sendMsg({ type: 'player_reincarnate' });
    setDeadStats(null);
  }, [sendMsg]);

  return { player, deadStats, updateFromTick, moveTo, castSpell, reincarnate };
}
