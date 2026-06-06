"""妖兽引擎 —— 敌对结构生成与 AI 追踪"""
import random
from dataclasses import dataclass, field


@dataclass
class Beast:
    id: str
    x: int
    y: int
    energy: float
    type: int = 0
    damage: float = 1.0
    speed: int = 1       # 每 tick 最大移动格数
    aggro_range: int = 15  # 索敌范围
    tick_age: int = 0
    total_kills: int = 0

    def move_toward(self, target_x: int, target_y: int, grid) -> bool:
        """向目标移动一步，返回是否到达相邻格"""
        dx = target_x - self.x
        dy = target_y - self.y
        dist = max(abs(dx), abs(dy))
        if dist == 0:
            return True
        if dist <= 1:
            return True  # 已在相邻格，可攻击

        # 移动一步
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        nx, ny = self.x + step_x, self.y + step_y

        # 边界处理
        if grid.boundary == "toroidal":
            nx %= grid.width
            ny %= grid.height
        elif not (0 <= nx < grid.width and 0 <= ny < grid.height):
            return False

        # 如果目标格被占，尝试绕路
        if not grid.is_empty(nx, ny):
            # 尝试对角移动
            if step_x != 0 and step_y != 0:
                if grid.is_empty(self.x + step_x, self.y):
                    nx, ny = self.x + step_x, self.y
                elif grid.is_empty(self.x, self.y + step_y):
                    nx, ny = self.x, self.y + step_y
                else:
                    return False  # 被堵住了
            else:
                return False

        if grid.boundary == "toroidal":
            nx %= grid.width
            ny %= grid.height

        self.x, self.y = nx, ny
        return dist <= 2  # 接近中


class BeastEngine:
    def __init__(self, grid, seed: int = 42):
        self.grid = grid
        self.beasts: list[Beast] = []
        self._rng = random.Random(seed)
        self._next_id = 0
        self._spawn_timer = 0
        self.spawn_interval = 80  # 每 N tick 生成一只

    def tick(self, player_x: int | None, player_y: int | None) -> list[dict]:
        """每 tick 运行妖兽 AI，返回事件列表"""
        events = []
        self._spawn_timer += 1

        # 生成新妖兽
        if self._spawn_timer >= self.spawn_interval and len(self.beasts) < 20:
            self._spawn_timer = 0
            pos = self.grid.random_empty_position()
            if pos:
                beast = Beast(
                    id=f"beast_{self._next_id}",
                    x=pos[0], y=pos[1],
                    energy=5 + self._rng.random() * 15,
                    type=self._rng.randint(0, 3),
                    damage=1 + self._rng.random() * 3,
                    speed=1 + self._rng.randint(0, 2),
                    aggro_range=10 + self._rng.randint(0, 20),
                )
                self.beasts.append(beast)
                self._next_id += 1
                events.append({"type": "beast_spawn", "beast": beast})

        # 妖兽移动 + 攻击
        for beast in self.beasts:
            beast.tick_age += 1
            if player_x is None:
                continue

            dist = max(abs(beast.x - player_x), abs(beast.y - player_y))
            if dist <= beast.aggro_range:
                # 追击玩家
                attacked = beast.move_toward(player_x, player_y, self.grid)
                events.append({"type": "beast_move", "id": beast.id, "x": beast.x, "y": beast.y})
                if attacked:
                    events.append({"type": "beast_attack", "id": beast.id, "damage": beast.damage})

        # 清理死亡妖兽
        self.beasts = [b for b in self.beasts if b.energy > 0]

        return events

    def damage_beast(self, beast_id: str, amount: float) -> bool:
        for b in self.beasts:
            if b.id == beast_id:
                b.energy -= amount
                if b.energy <= 0:
                    self.beasts.remove(b)
                    return True  # 击杀
                return False
        return False

    def get_nearby(self, x: int, y: int, radius: int = 3) -> list[Beast]:
        result = []
        for b in self.beasts:
            if max(abs(b.x - x), abs(b.y - y)) <= radius:
                result.append(b)
        return result

    def get_all_data(self) -> list[dict]:
        return [{"id": b.id, "x": b.x, "y": b.y, "energy": round(b.energy, 1),
                 "type": b.type, "aggro_range": b.aggro_range} for b in self.beasts]
