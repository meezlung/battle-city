import pyxel
from dataclasses import dataclass
import pyxelgrid # type: ignore
from random import randint, choice
from typing import Literal, cast
import json

@dataclass
class Bullet:
    x: int
    y: int
    direction: Literal['left', 'right', 'up', 'down']
    is_shoot: bool
    label: str

@dataclass
class Tank:
    x: int
    y: int
    direction: Literal['left', 'right', 'up', 'down']
    speed: int
    hp: int
    is_shoot: bool
    bullet: Bullet

@dataclass
class EnemyTank(Tank):
    label: str

@dataclass
class Stone:
    x: int
    y: int

@dataclass
class Brick(Stone):
    hp: int

@dataclass
class Mirror:
    x: int
    y: int
    orientation: Literal['NE', 'SE']

@dataclass
class Water:
    x: int
    y: int

@dataclass # Might not be needed because of my implementation?
class Forest:
    x: int
    y: int

class Game:
    def __init__(self):
        self.screen_width = 400
        self.screen_height = 272
        
        pyxel.init(self.screen_width, self.screen_height, fps=60)
        pyxel.load('assets/assets.pyxres')

        self.init_gamestate() 
        
        pyxel.run(self.update, self.draw)

# ------- Generator Functions -------
    def init_gamestate(self):
        with open('assets/levels/test.json') as self.map_file:
            self.map_load = json.load(self.map_file)

        self.is_gameover = False
        self.is_win = False
        self.undraw = False
        self.frames_before_starting = pyxel.frame_count + 200

        # A standard map is 25 x 16 cells
        self.map_database: list[list[Stone | Brick | Tank | EnemyTank | Bullet | Mirror | Water | Forest | int]] = [[0 for _ in range(self.screen_width // 16)] for _ in range(self.screen_height // 16)] # made this adaptable to screen size

        # Scans the map file and updates parameters
        self.map = self.map_load["map"] # self.map_loader: list[list[Stone | Brick | Tank | EnemyTank | Bullet | Mirror | int]] = self.map_load["map"] # Using this directly as map_database causes list mutation after restarting a game. TOO BAD.

        self.num_tanks: int = self.map_load["enemy_count"]
        self.rem_tanks = self.num_tanks # This has to be updated every time a new tank spawns in too

        # Enemy tank spawning
        self.concurrent_enem_spawn: int = 0
        self.dedicated_enem_spawn: list[tuple[int, int]] = []

        self.duplicate_map_database: list[list[Stone | Brick | Tank | EnemyTank | Bullet | Mirror | int]] = []
        self.forest_draw: list[tuple[int, int]] = [] # Overwriting purposes
        self.bullet_draw: list[tuple[int, int]] = []
        self.previous_bullet_positions: list[tuple[int, int]] = []

        # Helpful checks
        self.visited_enemy_tanks_so_far: set[str] = set() 
        self.visited_bullets_so_far: set[str] = set()

        # Some helpful bullet logic
        self.is_shoot_bullet = False
        self.should_overwrite_bullet = False

        # pyxel.playm(0, loop=True) # :3 

        self.generate_level()
        self.generate_enem_tank()

    # Main priority in generation is to ensure that the tanks and stones do not overlap each other
    def generate_level(self):
        for row in enumerate(self.map):
            for entity in enumerate(row[1]):
                if entity[1] == 1:
                    self.player_tank = Tank(entity[0], row[0], 'right', 1, 1, False, Bullet(0, 0, 'right', False, 'player')) # This should be based from the 
                    self.map_database[row[0]][entity[0]] = self.player_tank
                if entity[1] == 2:
                    self.dedicated_enem_spawn.append((entity[0],row[0]))
                if entity[1] == 3:
                    pass # player's home base not yet implemented
                if entity[1] == 4:
                    stone = Stone(entity[0], row[0])
                    self.map_database[row[0]][entity[0]] = stone
                if entity[1] == 5:
                    brick = Brick(entity[0], row[0], 2)
                    self.map_database[row[0]][entity[0]] = brick
                if entity[1] == 6:
                    mirror_ne = Mirror(entity[0], row[0], 'NE')
                    self.map_database[row[0]][entity[0]] = mirror_ne
                if entity[1] == 7:
                    mirror_se = Mirror(entity[0], row[0], 'SE')
                    self.map_database[row[0]][entity[0]] = mirror_se
                if entity[1] == 8:
                    water = Water(entity[0], row[0])
                    self.map_database[row[0]][entity[0]] = water
                if entity[1] == 9:
                    self.forest_draw.append((entity[0],row[0]))    
                    
    def generate_duplicate_map_database(self) -> list[list[Stone | Brick | Tank | EnemyTank | Bullet | Mirror | int]]: # This is for overwriting purposes
        return [[0 for _ in range(self.screen_width // 16)] for _ in range(self.screen_height // 16)]
    
    # ---- Random level generator mode (unused) ----
    def generate_stone_cells(self):
        num_stones: int = randint(5, 10)
        for _ in range(num_stones):
            x_i = randint(0, 24)
            y_i = randint(0, 15)

            if self.check_if_pos_is_unique(x_i, y_i):
                stone = Stone(x_i, y_i)
                self.map_database[y_i][x_i] = stone

    # -- Debugging Functions --
    def generate_mirrors_to_kill_player(self):
        x_i = 5
        y_i = 5

        if self.check_if_pos_is_unique(x_i, y_i):
            self.map_database[y_i][x_i] = Mirror(x_i, y_i, 'NE')

            if self.check_if_pos_is_unique(x_i + 8, y_i):
                self.map_database[y_i][x_i + 8] = Mirror(x_i + 8, y_i, 'SE')

                if self.check_if_pos_is_unique(x_i + 8, y_i + 4):
                    self.map_database[y_i + 4][x_i + 8] = Mirror(x_i + 8, y_i + 4, 'NE')

                    if self.check_if_pos_is_unique(x_i, y_i + 4):
                        self.map_database[y_i + 4][x_i] = Mirror(x_i, y_i + 4, 'SE')

    def generate_chained_mirrors(self):
        x_i = randint(0, 24)
        y_i = randint(0, 15)

        if self.check_if_pos_is_unique(x_i, y_i):
            self.map_database[y_i][x_i] = Mirror(x_i, y_i, 'NE')

            if self.check_if_pos_is_unique(x_i + 1, y_i):
                self.map_database[y_i][x_i + 1] = Mirror(x_i + 1, y_i, 'SE')   
                
                if self.check_if_pos_is_unique(x_i + 1, y_i + 1):
                    self.map_database[y_i + 1][x_i + 1] = Mirror(x_i + 1, y_i + 1, 'NE')     

    def generate_snake_mirrors(self):
        x_i = 5
        y_i = 5

        if self.check_if_pos_is_unique(x_i, y_i):
            self.map_database[y_i][x_i] = Mirror(x_i, y_i, 'NE')

            if self.check_if_pos_is_unique(x_i + 1, y_i):
                self.map_database[y_i][x_i + 1] = Mirror(x_i + 1, y_i, 'NE')

                if self.check_if_pos_is_unique(x_i + 1, y_i - 1):
                    self.map_database[y_i - 1][x_i + 1] = Mirror(x_i + 1, y_i - 1, 'NE')
                    
                    if self.check_if_pos_is_unique(x_i + 2, y_i - 1):
                        self.map_database[y_i - 1][x_i + 2] = Mirror(x_i + 2, y_i - 1, 'NE')
    
    def generate_two_self_enem_tank(self):
        enem_tank = EnemyTank(5, 5, 'right', 1, 1, False, Bullet(5, 5, 'up', False, 'enemy1'), 'enemy1')
        self.map_database[5][5] = enem_tank

        enem_tank = EnemyTank(10, 5, 'up', 1, 1, False, Bullet(10, 5, 'up', False, 'enemy2'), 'enemy2')
        self.map_database[5][10] = enem_tank
    # -- End of Debugging Functions --

    def generate_bricks(self):
        num_bricks: int = randint(5, 10)
        for _ in range(num_bricks):
            x_i = randint(0, 24)
            y_i = randint(0, 15)

            if self.check_if_pos_is_unique(x_i, y_i):
                brick = Brick(x_i, y_i, 2)
                self.map_database[y_i][x_i] = brick

    def generate_mirrors(self):
        num_mirrors: int = randint(5, 10)
        for _ in range(num_mirrors):
            x_i = randint(0, 24)
            y_i = randint(0, 15)
            orient = randint(0,1)

            if self.check_if_pos_is_unique(x_i, y_i):
                if orient:
                    mirror = Mirror(x_i, y_i, 'NE')
                else:
                    mirror = Mirror(x_i, y_i, 'SE')
                self.map_database[y_i][x_i] = mirror

    def generate_player_tank(self):
        self.player_tank = Tank(0, 0, 'right', 1, 1, False, Bullet(0, 0, 'right', False, 'player'))
        self.map_database[0][0] = self.player_tank

    def generate_enem_tank(self):
        #print(self.concurrent_enem_spawn)
        random_label = 33
        #if self.concurrent_enem_spawn < self.num_tanks: this is extremely broken atm
        for _ in range(self.num_tanks):
            pick = randint(0,len(self.dedicated_enem_spawn)-1)
            x_i, y_i = self.dedicated_enem_spawn[pick]

            if self.check_if_pos_is_unique(x_i, y_i):
                #print(x_i, y_i)
                enem_tank = EnemyTank(x_i, y_i, 'up', 1, 1, False, Bullet(x_i, y_i, 'up', False, chr(random_label)), chr(random_label)) # we should generate randomize labels infinitely to prevent bug in infinitely many tanks generation
                self.map_database[y_i][x_i] = enem_tank
                random_label += 1
                self.concurrent_enem_spawn += 1
            else:
                while not self.check_if_pos_is_unique(x_i, y_i):
                    pick = randint(0,len(self.dedicated_enem_spawn)-1)
                    x_i, y_i = self.dedicated_enem_spawn[pick]
                    
                    if self.check_if_pos_is_unique(x_i, y_i):
                        enem_tank = EnemyTank(x_i, y_i, 'up', 1, 1, False, Bullet(x_i, y_i, 'up', False, chr(random_label)), chr(random_label)) # we should generate randomize labels infinitely to prevent bug in infinitely many tanks generation
                        self.map_database[y_i][x_i] = enem_tank
                        break

                    random_label += 1
                    self.concurrent_enem_spawn += 1
    # ---- End of Random Level Generator Mode (unused) ----

# ------- Helper Functions -------
    def check_if_pos_is_unique(self, x: int, y: int) -> bool:
        return self.map_database[y][x] == 0

    # Check tank hp, remove tank if hp == 0
    def eliminate_no_hp_entity(self):
        for row in self.map_database:
            for entity in row:
                if isinstance(entity, (Tank, EnemyTank)):
                    if entity.hp <= 0:
                        destroyposrow = self.map_database.index(row)
                        destroypos = self.map_database[destroyposrow].index(entity)
                        self.map_database[destroyposrow][destroypos] = 0
                        # pyxel.play(1, 1)

                        if type(entity) == Tank and entity.hp == 0:
                            self.is_gameover = True
                            self.frames = pyxel.frame_count + 180
                        else:
                            self.rem_tanks -= 1
                            print(self.rem_tanks)

                elif isinstance(entity, (Brick)):
                    if entity.hp <= 0:
                        destroyposrow = self.map_database.index(row)
                        destroypos = self.map_database[destroyposrow].index(entity)
                        self.map_database[destroyposrow][destroypos] = 0
                        # pyxel.play(2, 2)

    def check_rem_tanks(self):
        if self.rem_tanks == 0 and not self.is_win:
            self.is_win = True
            self.frames = pyxel.frame_count + 180

    def is_bullet_from_dead_tank(self, bullet: Bullet) -> bool:
        for row in self.map_database:
            for tank in row:
                if type(tank) == Tank:
                    if bullet.label == 'player':
                        # print('Player still alive')
                        return False
                elif type(tank) == EnemyTank:
                    if bullet.label == tank.label:
                        # print('Enemy still alive')
                        return False
        return True

    # Check if bullet is still in the game, if it is, keep it moving. Note: This depends on the Bullet itself.
    def keep_bullet_shooting(self):
        for row in self.map_database:
            for bullet in row:
                if isinstance(bullet, Bullet):
                    if bullet.label not in self.visited_bullets_so_far:
                        if bullet.is_shoot:
                            if self.is_bullet_from_dead_tank(bullet): # We need to limit keep_bullet_shooting so that it only moves bullets that are from dead tanks
                                print('Coming from dead tank')
                                if pyxel.frame_count % 5 == 0:
                                    self.movement(bullet.direction, 'bullet', bullet.x, bullet.y, bullet)
                                    self.visited_bullets_so_far.add(bullet.label)
        self.visited_bullets_so_far.clear()

    def stop_shooting_if_bullet_collided_with_each_other(self, bullet1: Bullet, bullet2: Bullet):
        for row in self.map_database:
            for tank in row:
                if type(tank) == EnemyTank:
                    if bullet1.label == tank.label or bullet2.label == tank.label:
                        tank.bullet.is_shoot = False
                        tank.is_shoot = False

    def get_new_points(self, x: int, y: int, direction: Literal['left', 'right', 'up', 'down']) -> tuple[int, int]:
        return {'left': (x - 1, y), 'right': (x + 1, y), 'up': (x, y - 1), 'down': (x, y + 1)}.get(direction, (x, y))

    def get_mirror_points(self, x: int, y: int, direction: Literal['left', 'right', 'up', 'down'], orient: Literal['NE', 'SE']) -> tuple[int, int, Literal['left', 'right', 'up', 'down']]:
        if orient == 'NE':
            return {'left': (x - 1, y + 1, 'down'), 'right': (x + 1, y - 1, 'up'), 'up': (x + 1, y - 1, 'right'), 'down': (x - 1, y + 1, 'left')}.get(direction, (x, y, 'left'))
        else:
            return {'left': (x - 1, y - 1, 'up'), 'right': (x + 1, y + 1, 'down'), 'up': (x - 1, y - 1, 'left'), 'down': (x + 1, y + 1, 'right')}.get(direction, (x, y, 'left'))

    def change_direction_of_entity(self, direction: Literal['left', 'right', 'up', 'down'], entity_move: Tank | EnemyTank | Bullet):
        entity_move.direction = direction

    def handle_collision(self, direction: Literal['left', 'right', 'up', 'down'], entity: Literal['player', 'bullet', 'enemy'], curr_x: int, curr_y: int, is_from: Tank | EnemyTank | Bullet):
        entity_move = self.map_database[curr_y][curr_x]

        if entity == 'player' and isinstance(entity_move, Tank):
            self.change_direction_of_entity(direction, entity_move)

        elif entity == 'enemy' and isinstance(entity_move, EnemyTank):
            self.change_direction_of_entity(direction, entity_move)

        elif entity == 'bullet':
            if not isinstance(entity_move, (Tank, EnemyTank, Mirror, Water)):
                self.map_database[curr_y][curr_x] = 0
                # pyxel.play(2, 2)

            is_from.is_shoot = False # to keep the bullet moving/recursing from a tank or enemy tank

    def handle_bullet_to_bullet_collision(self, new_x: int, new_y: int, curr_x: int, curr_y: int):
        bullet1 = self.map_database[new_y][new_x]
        bullet2 = self.map_database[curr_y][curr_x]

        if type(bullet1) == type(bullet2) and isinstance(bullet1, Bullet) and isinstance(bullet2, Bullet):
            print("Bullet collision happened", bullet1, bullet2)      
            # pyxel.play(2, 2)
            bullet1.is_shoot = False
            bullet2.is_shoot = False
            print('Suspect')

            if bullet1.label == 'player' or bullet2.label == 'player': # If one of them is the player
                # Note: Same logic as when a bullet hits a stone

                # Stop player from shooting again first
                self.player_tank.bullet.is_shoot = False
                self.player_tank.is_shoot = False

                # Stop enemy tank from shooting again first
                self.stop_shooting_if_bullet_collided_with_each_other(bullet1, bullet2)
                
            else: # If both are enemy tanks (Proof by De Morgan's Law)
                # Stop both enemy tanks from shooting again first
                self.stop_shooting_if_bullet_collided_with_each_other(bullet1, bullet2)

            self.map_database[new_y][new_x] = 0
            self.map_database[curr_y][curr_x] = 0
            return
        
    def handle_bullet_overwrite_for_enemy_tanks(self, curr_x: int, curr_y: int, new_x: int, new_y: int, is_from: EnemyTank | Bullet):
        if isinstance(self.map_database[curr_y][curr_x], Bullet): # Edge case wherein the bullet is stuck in the screen before hitting the tank
            self.map_database[curr_y][curr_x] = 0

        self.duplicate_map_database = self.generate_duplicate_map_database()

        if type(is_from) == EnemyTank:
            self.duplicate_map_database[new_y][new_x] = Bullet(new_x, new_y, is_from.bullet.direction, True, is_from.bullet.label)
            self.movement(is_from.bullet.direction, 'bullet', new_x, new_y, is_from)

        if type(is_from) == Bullet:
            self.duplicate_map_database[new_y][new_x] = Bullet(new_x, new_y, is_from.direction, True, is_from.label)
            self.movement(is_from.direction, 'bullet', new_x, new_y, is_from)

        self.should_overwrite_bullet = True

    def handle_bullet_overwrite_for_water(self, curr_x: int, curr_y: int, new_x: int, new_y: int, is_from: Tank | EnemyTank | Bullet):
        if isinstance(self.map_database[curr_y][curr_x], Bullet): # Edge case wherein the bullet is stuck in the screen before hitting the tank
            self.map_database[curr_y][curr_x] = 0
        
        if type(is_from) == Tank:
            if (new_x, new_y) not in self.bullet_draw:
                self.bullet_draw.append((new_x, new_y))
            if pyxel.frame_count % 5 == 0:
                self.movement(is_from.bullet.direction, 'bullet', new_x, new_y, is_from)     

        if type(is_from) == EnemyTank:
            if (new_x, new_y) not in self.bullet_draw:
                self.bullet_draw.append((new_x, new_y))
            if pyxel.frame_count % 20 == 0:
                self.movement(is_from.bullet.direction, 'bullet', new_x, new_y, is_from)
        
        if type(is_from) == Bullet:
            if (new_x, new_y) not in self.bullet_draw:
                self.bullet_draw.append((new_x, new_y))
            if pyxel.frame_count % 5 == 0:    
                self.movement(is_from.direction, 'bullet', new_x, new_y, is_from)

    def handle_bullet_damage(self, curr_x: int, curr_y: int, new_x: int, new_y: int, is_from: Bullet | Tank | EnemyTank): # I can shorten this pa, but I just want to see each test cases
        entity_on_new_point = self.map_database[new_y][new_x]

        if type(entity_on_new_point) == Tank:
            if type(is_from) == EnemyTank and is_from.bullet.label != entity_on_new_point.bullet.label:
                print('Player tank hit by enemy tank bullet', is_from.label, entity_on_new_point.bullet.label)
                entity_on_new_point.hp -= 1
                self.handle_collision(is_from.bullet.direction, 'bullet', new_x, new_y, is_from)
                print(entity_on_new_point.hp)

            if type(is_from) == Tank and is_from.bullet.label == entity_on_new_point.bullet.label:
                print('Player tank hit by player tank bullet. Suicidal tank lmao.')
                entity_on_new_point.hp -= 1
                self.handle_collision(is_from.bullet.direction, 'bullet', curr_x, curr_y, is_from)

            # -- This is when the self.keep_bullet_shooting() is called, i.e. Bullets are moved from dead tanks --
            if type(is_from) == Bullet:
                if is_from.label == 'player':
                    print('Player tank hit by player tank bullet', is_from.label, entity_on_new_point.bullet.label)
                    entity_on_new_point.hp -= 1
                    self.handle_collision(is_from.direction, 'bullet', curr_x, curr_y, is_from)
                else:
                    print('Player tank hit by enemy tank bullet', is_from.label, entity_on_new_point.bullet.label)
                    entity_on_new_point.hp -= 1
                    self.handle_collision(is_from.direction, 'bullet', new_x, new_y, is_from)
            # -- End of self.keep_bullet_shooting() --

        elif type(entity_on_new_point) == EnemyTank:
            if type(is_from) == Tank and is_from.bullet.label != entity_on_new_point.label:
                print('Enemy tank hit by player tank bullet', is_from.bullet.label, entity_on_new_point.label)
                entity_on_new_point.hp -= 1
                self.handle_collision(is_from.bullet.direction, 'bullet', curr_x, curr_y, is_from)

            if type(is_from) == EnemyTank:
                print('Enemy tank hit by enemy tank bullet (should pass through)')
                self.handle_bullet_overwrite_for_enemy_tanks(curr_x, curr_y, new_x, new_y, is_from)

            # -- This is when the self.keep_bullet_shooting() is called, i.e. Bullets are moved from dead tanks --
            if type(is_from) == Bullet: 
                if is_from.label != 'player':
                    print('Enemy tank hit by enemy tank bullet', is_from.label, entity_on_new_point.label)
                    self.handle_bullet_overwrite_for_enemy_tanks(curr_x, curr_y, new_x, new_y, is_from)
                
                if is_from.label == 'player':
                    print('Enemy tank hit by player tank bullet', is_from.label, entity_on_new_point.label)
                    entity_on_new_point.hp -= 1
                    self.handle_collision(is_from.direction, 'bullet', curr_x, curr_y, is_from)
            # -- End of self.keep_bullet_shooting() --

        elif type(entity_on_new_point) == Brick:
            entity_on_new_point.hp -= 1
            self.handle_collision(is_from.direction, 'bullet', curr_x, curr_y, is_from)

        elif type(entity_on_new_point) == Water:
            self.handle_bullet_overwrite_for_water(curr_x, curr_y, new_x, new_y, is_from)

    def handle_bullet_to_mirror_result(self, direction: Literal['left', 'right', 'up', 'down'], curr_x: int, curr_y: int, new_x: int, new_y: int, is_from: Bullet | Tank | EnemyTank, how_many_times_is_mirror_called: int, prev_mirror_call_pos: tuple[int, int], last_bullet_pos_before_hitting_mirror: tuple[int, int]):
        mirror = self.map_database[new_y][new_x]

        if isinstance(mirror, (Mirror)) and how_many_times_is_mirror_called <= 0:
            orient = mirror.orientation
            prev_mirror_call_pos = (mirror.x, mirror.y)
            last_bullet_pos_before_hitting_mirror = (curr_x, curr_y)
            self.movement(direction, "bullet", curr_x, curr_y, is_from, True, orient, how_many_times_is_mirror_called + 1, prev_mirror_call_pos, last_bullet_pos_before_hitting_mirror)
        
        elif isinstance(mirror, Mirror) and how_many_times_is_mirror_called > 0: # Edge cases for chained mirrors
            orient = mirror.orientation
            if isinstance(self.map_database[last_bullet_pos_before_hitting_mirror[1]][last_bullet_pos_before_hitting_mirror[0]], Bullet):
                self.map_database[last_bullet_pos_before_hitting_mirror[1]][last_bullet_pos_before_hitting_mirror[0]] = 0
            self.movement(direction, "bullet", prev_mirror_call_pos[0], prev_mirror_call_pos[1], is_from, True, orient, how_many_times_is_mirror_called + 1, (mirror.x, mirror.y))

    def move_bullet(self, direction: Literal['left', 'right', 'up', 'down'], curr_x: int, curr_y: int, new_x: int, new_y: int, is_from: Tank | EnemyTank | Bullet):
        if isinstance(is_from, (Tank, EnemyTank)):
            self.map_database[new_y][new_x] = Bullet(new_x, new_y, direction, True, is_from.bullet.label)
            is_from.bullet.x, is_from.bullet.y, is_from.bullet.direction = (new_x, new_y, direction)
        
        if isinstance(is_from, Bullet):
            self.map_database[new_y][new_x] = Bullet(new_x, new_y, direction, True, is_from.label)
            is_from.x, is_from.y, is_from.direction = (new_x, new_y, direction)

        # Edge case: If the bullet just spawned, this will prevent setting the tank to 0
        if isinstance(self.map_database[curr_y][curr_x], Bullet):
            self.map_database[curr_y][curr_x] = 0

    def move_tanks(self, direction: Literal['left', 'right', 'up', 'down'], entity: Literal['player', 'enemy'], curr_x: int, curr_y: int, new_x: int, new_y: int):
        # If the new point is safe to move into, move the entity to the new point
        if self.map_database[new_y][new_x] == 0: 
            self.map_database[new_y][new_x] = self.map_database[curr_y][curr_x]
            entity_move = self.map_database[new_y][new_x]

            self.map_database[curr_y][curr_x] = 0

            if entity == 'player' or entity == 'enemy':
                if isinstance(entity_move, (Tank, EnemyTank)):
                    entity_move.x, entity_move.y, entity_move.direction = new_x, new_y, direction

    def is_in_bounds(self, new_x: int, new_y: int) -> bool:
        return not (0 <= new_x < self.screen_width // 16) or not (0 <= new_y < self.screen_height // 16)
# ------- Helper Functions -------

# ------- Main collision checker + Entity movement function -------
    def movement(self, direction: Literal['left', 'right', 'up', 'down'], entity: Literal['player', 'bullet', 'enemy'], curr_x: int, curr_y: int, is_from: Tank | EnemyTank | Bullet, mirror_move: bool = False, orient: Literal['NE','SE'] = 'NE', how_many_times_is_mirror_called: int = 0, prev_mirror_call_pos: tuple[int, int] = (0, 0), last_bullet_pos_before_hitting_mirror: tuple[int, int] = (0, 0)): #this last arguement really sucks but its the only way to tie the collision detection back to the mirror movement
        # --- Base Case for the Mirror function ---       
        if mirror_move: # If the movement function got called from the bullet-mirror collision check
            new_x, new_y, direction = self.get_mirror_points(curr_x, curr_y, direction, orient)

        else: # Maybe we could merge get_new_points and get_mirror_points?
            new_x, new_y = self.get_new_points(curr_x, curr_y, direction)
        # --- End of Base Case for the Mirror function ---       


        # --- Bounds checking ---
        if self.is_in_bounds(new_x, new_y):
            self.handle_collision(direction, entity, curr_x, curr_y, is_from)
        # --- End of Bounds checking ---


        # --- Check if there is an entity ahead of the entity trying to move. If there is one, do not move --- 
        elif isinstance(self.map_database[new_y][new_x], Stone):
            self.handle_collision(direction, entity, curr_x, curr_y, is_from)

            if isinstance(self.map_database[new_y][new_x], Brick): # Under the stone, since Brick inherits from Stone
                if entity == 'bullet': # If a bullet discovers a Brick in front of it, subtract hp of brick
                    self.handle_bullet_damage(curr_x, curr_y, new_x, new_y, is_from)

        elif isinstance(self.map_database[new_y][new_x], Mirror):
            if entity == 'bullet':
                self.handle_bullet_to_mirror_result(direction, curr_x, curr_y, new_x, new_y, is_from, how_many_times_is_mirror_called, prev_mirror_call_pos, last_bullet_pos_before_hitting_mirror)

            else: # For the tanks that want to rotate in the direction of the mirror
                self.handle_collision(direction, entity, curr_x, curr_y, is_from)

        elif isinstance(self.map_database[new_y][new_x], (EnemyTank, Tank)):
            if entity == 'enemy' or entity == 'player': # If a tank finds another tank, do not move
                self.handle_collision(direction, entity, curr_x, curr_y, is_from)
            if entity == 'bullet': # Bullet finds a tank, tank takes damage
                self.handle_bullet_damage(curr_x, curr_y, new_x, new_y, is_from) # This should handle the cases wherein bullets of EnemyTank should pass through fellow EnemyTank 

        elif isinstance(self.map_database[new_y][new_x], Water):
            if entity == 'enemy' or entity == 'player':
                self.handle_collision(direction, entity, curr_x, curr_y, is_from)
            if entity == 'bullet':
                if pyxel.frame_count % 5 == 0:
                    self.handle_bullet_damage(curr_x, curr_y, new_x, new_y, is_from)

        elif isinstance(self.map_database[new_y][new_x], Bullet):
            if entity == 'bullet': # Bullet finds another bullet, both bullets should disappear
                self.handle_bullet_to_bullet_collision(new_x, new_y, curr_x, curr_y) 
        # --- End of Check if there is an entity ahead of the entity trying to move. If there is one, do not move --- 


        # --- If there is no entity ahead, you can safely move ---
        else:
            # A bullet generates differently than any other entity, thus it must be treated as a separate case
            if entity == 'bullet': 
                self.move_bullet(direction, curr_x, curr_y, new_x, new_y, is_from)

            else:
                self.move_tanks(direction, entity, curr_x, curr_y, new_x, new_y)
        # --- End of If there is no entity ahead, you can safely move ---
# -- Main collision checker + Entity movement function --


    def ai_tanks_moves(self):
        directions = ['left', 'right', 'up', 'down']
        for row in self.map_database:
            for entity in row:
                if isinstance(entity, EnemyTank):
                    if entity.label not in self.visited_enemy_tanks_so_far: # Prevents the same tank from moving twice in one tick
                        random_time_interval_to_move = randint(50, 100)
                        if pyxel.frame_count % random_time_interval_to_move == 0:
                            entity.direction = cast(Literal['left', 'right', 'up', 'down'], directions[randint(0, 3)])  # Set random direction
                            self.movement(entity.direction, 'enemy', entity.x, entity.y, entity)   

                        if pyxel.frame_count > self.frames_before_starting: # Prevents the enemy tank from shooting before the game starts
                            random_time_interval_to_shoot = randint(30, 50)
                            if pyxel.frame_count % random_time_interval_to_shoot == 0:
                                should_shoot = choice([True, False])     
                                if should_shoot and not entity.is_shoot:
                                    # pyxel.play(0, 0)
                                    entity.bullet.x, entity.bullet.y, entity.bullet.direction = entity.x, entity.y, entity.direction
                                    entity.is_shoot = True
                                    entity.bullet.is_shoot = True

                            if entity.is_shoot and entity.bullet.is_shoot:
                                if pyxel.frame_count % 5 == 0:
                                    self.movement(entity.bullet.direction, 'bullet', entity.bullet.x, entity.bullet.y, entity)
                        
                        self.visited_enemy_tanks_so_far.add(entity.label)
        self.visited_enemy_tanks_so_far.clear()



    def update(self):
        #if pyxel.frame_count % 180 == 0: #enemy tank spawns in an interval of 3 seconds, maybe this can be configured in the map file for increasing difficulty
            #self.generate_enem_tank() #this code is extremely broken atm
        
        if self.is_gameover or self.is_win:
            if pyxel.frame_count > self.frames:
                self.undraw = True
                pyxel.stop() # stop music

            if pyxel.btnp(pyxel.KEY_R):
                self.init_gamestate()

        if not self.undraw:
            if pyxel.btnp(pyxel.KEY_Q):
                pyxel.quit()

            if pyxel.btnp(pyxel.KEY_F1): # debug key, instant game over
                print(self.map_database[self.player_tank.y][self.player_tank.x])
                tanko = self.map_database[self.player_tank.y][self.player_tank.x]
                print('BOOM', tanko)
                if isinstance(tanko, Tank):
                    tanko.hp = 0
            
            if pyxel.btnp(pyxel.KEY_T): # debug key, checks map state mid-game
                print(self.map_database)

            if self.player_tank.hp > 0 and not self.is_win and not self.is_gameover: # don't move if player tank dead already
                if pyxel.btn(pyxel.KEY_LEFT):
                    # print('left pressed!', self.player_tank)
                    if pyxel.frame_count % 4 == 0:
                        self.movement('left', 'player', self.player_tank.x, self.player_tank.y, self.player_tank)

                elif pyxel.btn(pyxel.KEY_RIGHT):
                    # print('right pressed!', self.player_tank)
                    if pyxel.frame_count % 4 == 0:
                        self.movement('right', 'player', self.player_tank.x, self.player_tank.y, self.player_tank)

                elif pyxel.btn(pyxel.KEY_UP):
                    # print('up pressed!', self.player_tank)
                    if pyxel.frame_count % 4 == 0:
                        self.movement('up', 'player', self.player_tank.x, self.player_tank.y, self.player_tank)

                elif pyxel.btn(pyxel.KEY_DOWN):
                    # print('down pressed!', self.player_tank)
                    if pyxel.frame_count % 4 == 0:
                        self.movement('down', 'player', self.player_tank.x, self.player_tank.y, self.player_tank)
                
                if pyxel.btnp(pyxel.KEY_SPACE) and not self.player_tank.is_shoot and pyxel.frame_count > self.frames_before_starting: #  # Uncomment this later. This prevents the player from shooting before the game starts
                    # pyxel.play(0, 0)
                    self.player_tank.bullet.x, self.player_tank.bullet.y, self.player_tank.bullet.direction = self.player_tank.x, self.player_tank.y, self.player_tank.direction
                    self.player_tank.is_shoot = True
                    self.player_tank.bullet.is_shoot = True

                if self.player_tank.is_shoot and self.player_tank.bullet.is_shoot:
                    self.movement(self.player_tank.bullet.direction, 'bullet', self.player_tank.bullet.x, self.player_tank.bullet.y, self.player_tank)
                
                self.ai_tanks_moves()

            self.keep_bullet_shooting()

            self.eliminate_no_hp_entity()
            
            self.check_rem_tanks()



    def draw(self):
        pyxel.cls(14)

        if not self.undraw:
            # Generate graphics based on map_database
            for row in self.map_database:
                for entity in row:
                    if type(entity) == Tank:
                        if entity.direction == 'up':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 0, 0, 16, 16, 0)
                        elif entity.direction == 'down':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 16, 0, 16, 16, 0)
                        elif entity.direction == 'right':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 32, 0, 16, 16, 0)
                        elif entity.direction == 'left':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 48, 0, 16, 16, 0)
                    elif type(entity) == Stone:
                        pyxel.blt(entity.x*16, entity.y*16, 0, 16, 16, 16, 16, 0)
                    elif type(entity) == Brick:
                        if entity.hp == 2:
                            pyxel.blt(entity.x*16, entity.y*16, 0, 0, 48, 16, 16, 0)
                        else:
                            pyxel.blt(entity.x*16, entity.y*16, 0, 16, 48, 16, 16, 0)
                    elif type(entity) == EnemyTank:
                        if entity.direction == 'up':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 0, 32, 16, 16, 0)
                        elif entity.direction == 'down':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 16, 32, 16, 16, 0)
                        elif entity.direction == 'right':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 32, 32, 16, 16, 0)
                        elif entity.direction == 'left':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 48, 32, 16, 16, 0)
                    elif type(entity) == Bullet:
                        pyxel.blt(entity.x*16, entity.y*16, 0, 0, 16, 16, 16, 0)
                    elif type(entity) == Mirror:
                        if entity.orientation == 'NE':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 32, 16, 16, 16, 0)
                        else:
                            pyxel.blt(entity.x*16, entity.y*16, 0, 48, 16, 16, 16, 0)
                    elif type(entity) == Water:
                        pyxel.blt(entity.x*16, entity.y*16, 0, 32, 48, 16, 16, 0)
                    
                    for forest in self.forest_draw: # Overwriting background with the bushes
                        pyxel.blt(forest[0]*16, forest[1]*16, 0, 48, 48, 16, 16, 0)

            # Overwriting water with bullets
            for bullet in self.previous_bullet_positions:
                pyxel.blt(bullet[0]*16, bullet[1]*16, 0, 32, 48, 16, 16, 0)

            for bullet in self.bullet_draw:
                pyxel.blt(bullet[0]*16, bullet[1]*16, 0, 0, 16, 16, 16, 0) 
                self.bullet_draw.remove(bullet)

            self.previous_bullet_positions = self.bullet_draw.copy()
                        
        else:
            if self.is_gameover:
                pyxel.text((self.screen_width // 2) - 20, (self.screen_height // 2) - 20, 'GAME OVER', 1) # Temporary values. might have to make a game over splash screen instead since the text is small
            elif self.is_win:
                pyxel.text((self.screen_width // 2) - 20, (self.screen_height // 2) - 20, 'YOU WIN!', 1)

        # Overwriting enemy tanks with their enemy tank bullets
        if self.should_overwrite_bullet:
            for row in self.duplicate_map_database:
                for entity in row:
                    if type(entity) == Bullet:
                        print(self.duplicate_map_database)
                        pyxel.blt(entity.x*16, entity.y*16, 0, 0, 16, 16, 16, 0)
                        self.should_overwrite_bullet = False

                        self.duplicate_map_database[entity.y][entity.x] = 0

        # Countdown timer before starting the game
        if self.frames_before_starting - pyxel.frame_count >= 0:
            countdown = self.frames_before_starting - pyxel.frame_count
            if countdown >= 180:
                pyxel.text((self.screen_width // 2), (self.screen_height // 2), '3', 1)
            elif countdown >= 120:
                pyxel.text((self.screen_width // 2), (self.screen_height // 2), '2', 1)
            elif countdown >= 60:
                pyxel.text((self.screen_width // 2), (self.screen_height // 2), '1', 1)
            else:
                pyxel.text((self.screen_width // 2), (self.screen_height // 2), 'GO!', 1)

        # The deeper the code here, the more it will be drawn on top of the other entities
                

Game()


    

