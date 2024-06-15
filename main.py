import os
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

@dataclass
class HomeBase(Brick):
    pass

@dataclass # TODO: add debug stuff here. This is for checking what kind of debug message will be shown in the console. Each set of debug messages can be toggled using the number keys when debug mode is on
class DebugValues:
    pass

class Game:
    def __init__(self):
        self.screen_width = 464
        self.screen_height = 272
        self.internal_level = 1
        self.hp = 2
        self.map_loaded = False
        self.isdebug = False
        self.debug_msg = DebugValues 
        self.level_list = [f for f in os.listdir('assets/levels') if os.path.isfile('assets/levels/'+f) and f.endswith('.json')]
        pyxel.init(self.screen_width, self.screen_height, fps=60)
        pyxel.load('assets/assets.pyxres')

        self.load() 
        
        print(self.level_list)
        pyxel.run(self.update, self.draw)

# ------- Generator Functions -------
    def load(self):
        try:
            with open('assets/levels/' + self.level_list[self.internal_level-1]) as self.map_file:
                print(f'loaded! {self.level_list[self.internal_level-1]}')
                self.map_load = json.load(self.map_file)
                self.map_loaded = True
                self.init_gamestate() 
        except:
            print(f'ERROR! Map {self.level_list[self.internal_level-1]} is an invalid file!')
            self.internal_level += 1

    def init_gamestate(self):
        self.level = self.map_load["level"]
        self.stage_name = self.map_load["stage_name"]
        self.tutorial = self.map_load["tutorial"]
        self.powerup_time_limit = self.map_load["powerup_req"]
        self.is_gameover = False
        self.is_win = False
        self.undraw = False
        self.powerup_can_get = True
        self.powerup_got = False
        self.time = 0
        self.frames_before_starting = pyxel.frame_count + 200

        # A standard map is 25 x 16 cells
        self.map_database: list[list[Stone | Brick | Tank | EnemyTank | Bullet | Mirror | Water | Forest | int]] = [[0 for _ in range((self.screen_width // 16)-4)] for _ in range(self.screen_height // 16)] # made this adaptable to screen size

        # Scans the map file and updates parameters
        self.map = self.map_load["map"] # self.map_loader: list[list[Stone | Brick | Tank | EnemyTank | Bullet | Mirror | int]] = self.map_load["map"] # Using this directly as map_database causes list mutation after restarting a game. TOO BAD.

        self.num_tanks: int = self.map_load["enemy_count"]
        self.rem_tanks = self.num_tanks # This has to be updated every time a new tank spawns in too

        self.spawnpoint: tuple[int,int]
        
        # Enemy tank spawning
        self.random_label = 33
        self.concurrent_enem_spawn: int = 0
        self.dedicated_enem_spawn: list[tuple[int, int]] = []

        self.duplicate_map_database: list[list[Stone | Brick | Tank | EnemyTank | Bullet | Mirror | Water | Forest | int]] = [[0 for _ in range(self.screen_width // 16)] for _ in range(self.screen_height // 16)] # Overwriting objects with bullets
        self.forest_draw: list[tuple[int, int]] = [] # Overwriting purposes

        # Helpful checks
        self.visited_enemy_tanks_so_far: set[str] = set() 
        self.visited_bullets_so_far: set[str] = set()
        self.duplicate_visited_bullets_so_far: set[str] = set()

        # Some helpful bullet logic
        self.is_shoot_bullet = False
        self.should_overwrite_bullet = False

        #pyxel.playm(0, loop=True) # :3 
        self.cheat_input: list[str] = []
        self.debug_input = 0
        self.generate_level()

    # Main priority in generation is to ensure that the tanks and stones do not overlap each other
    def generate_level(self):
        for row in enumerate(self.map):
            for entity in enumerate(row[1]):
                if entity[1] == 1:
                    self.player_tank = Tank(entity[0], row[0], 'right', 1, 1, False, Bullet(0, 0, 'right', False, 'player'))
                    self.map_database[row[0]][entity[0]] = self.player_tank
                    self.spawnpoint = (entity[0], row[0])
                if entity[1] == 2:
                    self.dedicated_enem_spawn.append((entity[0],row[0]))
                if entity[1] == 3:
                    homebase = HomeBase(entity[0], row[0], 1)
                    self.map_database[row[0]][entity[0]] = homebase
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

        self.map_file.close()
    # ------- End of Generator Functions -------

    # ------- Random level generator mode (unused) -------
    def generate_stone_cells(self):
        num_stones: int = randint(5, 10)
        for _ in range(num_stones):
            x_i = randint(0, 24)
            y_i = randint(0, 15)

            if self.check_if_pos_is_unique(x_i, y_i):
                stone = Stone(x_i, y_i)
                self.map_database[y_i][x_i] = stone

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
        print(self.concurrent_enem_spawn)
        if self.concurrent_enem_spawn < self.num_tanks:
            pick = randint(0,len(self.dedicated_enem_spawn)-1)
            x_i, y_i = self.dedicated_enem_spawn[pick]

            if self.check_if_pos_is_unique(x_i, y_i):
                tank_choice = choice(['regular', 'regular', 'buff'])
                if tank_choice == 'regular':
                    regular_enem_tank = EnemyTank(x_i, y_i, 'up', 1, 1, False, Bullet(x_i, y_i, 'up', False, f'regular_{chr(self.random_label)}'), f'regular_{chr(self.random_label)}') # we should generate randomize labels infinitely to prevent bug in infinitely many tanks generation
                    self.map_database[y_i][x_i] = regular_enem_tank
                    self.random_label += 1
                    self.concurrent_enem_spawn += 1

                else:
                    buff_enem_tank = EnemyTank(x_i, y_i, 'up', 1, 2, False, Bullet(x_i, y_i, 'up', False, f'buff_{chr(self.random_label)}'), f'buff_{chr(self.random_label)}')
                    self.map_database[y_i][x_i] = buff_enem_tank
                    self.random_label += 1
                    self.concurrent_enem_spawn += 1
                    
            else:
                self.generate_enem_tank() # Recursive call to generate another enemy tank instead of while loop again

        else:
            return
    # ------- End of Random Level Generator Mode (unused) -------

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
                        pyxel.play(3, 1)

                        if type(entity) == Tank and entity.hp == 0:
                            self.hp -= 1
                            if self.hp == 0:
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
                        if isinstance(entity, (HomeBase)):
                            self.is_gameover = True
                            self.frames = pyxel.frame_count + 180
                        
                        pyxel.play(3, 2)

    def check_rem_tanks(self):
        if self.rem_tanks == 0 and not self.is_win:
            self.is_win = True
            self.frames = pyxel.frame_count + 180

    def is_bullet_from_dead_tank(self, bullet: Bullet) -> bool:
        for row in self.map_database:
            for tank in row:
                if type(tank) == Tank:
                    if bullet.label == 'player':
                        #print('Player still alive')
                        return False
                elif type(tank) == EnemyTank:
                    if bullet.label == tank.label:
                        # print('Enemy still alive')
                        return False
        return True

    # Check if bullet is still in the game, if it is, keep it moving. Note: This depends on the Bullet itself.
    def keep_bullet_shooting(self, database: list[list[Stone | Brick | Tank | EnemyTank | Bullet | Mirror | Water | Forest | int]], visited_bullets: set[str]):
        for row in database:
            for bullet in row:
                if isinstance(bullet, Bullet):
                    if bullet.label not in visited_bullets:
                        if bullet.is_shoot:
                            if self.is_bullet_from_dead_tank(bullet): # We need to limit keep_bullet_shooting so that it only moves bullets that are from dead tanks
                                print('Coming from dead tank')
                                if pyxel.frame_count % 5 == 0:
                                    self.movement(bullet.direction, 'bullet', bullet.x, bullet.y, bullet)
                                    visited_bullets.add(bullet.label)
        visited_bullets.clear()

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
                pyxel.play(3, 2)
            
            self.duplicate_map_database[curr_y][curr_x] = 0 # Handle collisions for bullet overwrites. No need extra checks since this duplicate map_database is only for bullets

            is_from.is_shoot = False # to keep the bullet moving/recursing from a tank or enemy tank

    def handle_bullet_to_bullet_collision(self, new_x: int, new_y: int, curr_x: int, curr_y: int):
        bullet1 = self.map_database[new_y][new_x]
        bullet2 = self.map_database[curr_y][curr_x]

        if type(bullet1) == type(bullet2) and isinstance(bullet1, Bullet) and isinstance(bullet2, Bullet):
            print("Bullet collision happened", bullet1, bullet2)      
            pyxel.play(3, 2)
            bullet1.is_shoot = False
            bullet2.is_shoot = False

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
            self.duplicate_map_database[new_y][new_x] = 0
            self.duplicate_map_database[curr_y][curr_x] = 0

    def handle_bullet_damage(self, curr_x: int, curr_y: int, new_x: int, new_y: int, is_from: Bullet | Tank | EnemyTank): # I can shorten this pa, but I just want to see each test cases
        entity_on_new_point = self.map_database[new_y][new_x]

        if type(entity_on_new_point) == Tank:
            if type(is_from) == EnemyTank and is_from.bullet.label != entity_on_new_point.bullet.label:
                print('Player tank hit by enemy tank bullet', is_from.label, entity_on_new_point.bullet.label)
                entity_on_new_point.hp -= 1
                self.handle_collision(is_from.bullet.direction, 'bullet', curr_x, curr_y, is_from)
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
                    self.handle_collision(is_from.direction, 'bullet', curr_x, curr_y, is_from)
            # -- End of self.keep_bullet_shooting() --

        elif type(entity_on_new_point) == EnemyTank:
            if type(is_from) == Tank and is_from.bullet.label != entity_on_new_point.label:
                print('Enemy tank hit by player tank bullet', is_from.bullet.label, entity_on_new_point.label)
                entity_on_new_point.hp -= 1
                self.handle_collision(is_from.bullet.direction, 'bullet', curr_x, curr_y, is_from)

            if type(is_from) == EnemyTank:
                print('Enemy tank hit by enemy tank bullet (should pass through)')
                self.move_bullet(is_from.bullet.direction, curr_x, curr_y, new_x, new_y, is_from)

            # -- This is when the self.keep_bullet_shooting() is called, i.e. Bullets are moved from dead tanks --
            if type(is_from) == Bullet: 
                if is_from.label != 'player':
                    print('Enemy tank hit by enemy tank bullet', is_from.label, entity_on_new_point.label)
                    self.move_bullet(is_from.direction, curr_x, curr_y, new_x, new_y, is_from)

                if is_from.label == 'player':
                    print('Enemy tank hit by player tank bullet', is_from.label, entity_on_new_point.label)
                    entity_on_new_point.hp -= 1
                    self.handle_collision(is_from.direction, 'bullet', curr_x, curr_y, is_from)
            # -- End of self.keep_bullet_shooting() --

        elif type(entity_on_new_point) == Brick or type(entity_on_new_point) == HomeBase:
            entity_on_new_point.hp -= 1

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
        entity_move = self.map_database[new_y][new_x]
        
        # Bullets fired from alive tanks
        if isinstance(is_from, (Tank, EnemyTank)):
            if isinstance(entity_move, EnemyTank) and isinstance(is_from, EnemyTank): # Friendly fire enemy tanks case, should have bullet overwrite
                self.duplicate_map_database[new_y][new_x] = Bullet(new_x, new_y, direction, True, is_from.bullet.label)
            elif isinstance(entity_move, Water): # Water case, should have bullet overwrite
                self.duplicate_map_database[new_y][new_x] = Bullet(new_x, new_y, direction, True, is_from.bullet.label)
            else: # Normal movement
                self.map_database[new_y][new_x] = Bullet(new_x, new_y, direction, True, is_from.bullet.label)

            is_from.bullet.x, is_from.bullet.y, is_from.bullet.direction = (new_x, new_y, direction)
        
        # Bullets fired from dead tanks
        if isinstance(is_from, Bullet):
            if isinstance(entity_move, EnemyTank) and isinstance(is_from, EnemyTank): # Friendly fire enemy tanks case, should have bullet overwrite
                self.duplicate_map_database[new_y][new_x] = Bullet(new_x, new_y, direction, True, is_from.label)
            elif isinstance(entity_move, Water): # Water case, should have bullet overwrite
                self.duplicate_map_database[new_y][new_x] = Bullet(new_x, new_y, direction, True, is_from.label)
            else: # Normal movement
                self.map_database[new_y][new_x] = Bullet(new_x, new_y, direction, True, is_from.label)

            is_from.x, is_from.y, is_from.direction = (new_x, new_y, direction)

        # Edge case: If the bullet just spawned, this will prevent setting the tank to 0
        if isinstance(self.map_database[curr_y][curr_x], Bullet):
            self.map_database[curr_y][curr_x] = 0

        # Remove previous bullets that have been overwritten
        if isinstance(self.duplicate_map_database[curr_y][curr_x], Bullet):
            self.duplicate_map_database[curr_y][curr_x] = 0

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
        return not (0 <= new_x < (self.screen_width // 16)-4) or not (0 <= new_y < self.screen_height // 16)
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

            if isinstance(self.map_database[new_y][new_x], (Brick, HomeBase)): # Under the stone, since Brick inherits from Stone
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
                self.move_bullet(direction, curr_x, curr_y, new_x, new_y, is_from)

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
                                    pyxel.play(3, 0)
                                    entity.bullet.x, entity.bullet.y, entity.bullet.direction = entity.x, entity.y, entity.direction
                                    entity.is_shoot = True
                                    entity.bullet.is_shoot = True

                            if entity.is_shoot and entity.bullet.is_shoot:
                                if pyxel.frame_count % 5 == 0:
                                    self.movement(entity.bullet.direction, 'bullet', entity.bullet.x, entity.bullet.y, entity)
                        
                        self.visited_enemy_tanks_so_far.add(entity.label)
        self.visited_enemy_tanks_so_far.clear()

    def powerup(self):
        if self.rem_tanks == self.num_tanks//2 and self.time < self.powerup_time_limit and not self.powerup_got:
            self.hp += 1
            self.powerup_got = True
            pyxel.play(1, 3)
            print('GOTCHA! POWERUP GET!')

    def cheat(self):
        if not self.cheat_input:
            self.input_timer = pyxel.frame_count + 300

        if self.cheat_input == ['UP','UP','DOWN','DOWN','LEFT','RIGHT','LEFT','RIGHT','B','A','ENTER'] and pyxel.frame_count < self.input_timer:
            self.hp += 1
            self.input_timer = 0
            pyxel.play(1, 3)
            print('CHEATCODE ACTIVATED!, current lives:' + str(self.hp))
        elif self.debug_input == 5 and pyxel.frame_count < self.input_timer:
            self.internal_level = 1
            self.hp = 99
            self.level_list.clear()
            self.level_list = ['debug_levels/' + f for f in os.listdir('assets/levels/debug_levels') if os.path.isfile('assets/levels/debug_levels/'+f) and f.endswith('.json')]
            self.map_loaded = False
            self.isdebug = True
            print('DEBUG ENABLED!')
            self.load()
        elif pyxel.frame_count > self.input_timer:
            self.cheat_input.clear()
            self.debug_input = 0
        else:
            if pyxel.btnp(pyxel.KEY_UP):
                self.cheat_input.append('UP')
            elif pyxel.btnp(pyxel.KEY_DOWN):
                self.cheat_input.append('DOWN')
            elif pyxel.btnp(pyxel.KEY_LEFT):
                self.cheat_input.append('LEFT')
            elif pyxel.btnp(pyxel.KEY_RIGHT):
                self.cheat_input.append('RIGHT')
            elif pyxel.btnp(pyxel.KEY_B):
                self.cheat_input.append('B')
            elif pyxel.btnp(pyxel.KEY_A):
                self.cheat_input.append('A')
            elif pyxel.btnp(pyxel.KEY_RETURN):
                self.cheat_input.append('ENTER')
            elif pyxel.btnp(pyxel.KEY_DELETE):
                self.debug_input += 1

    def update(self):
        if not self.map_loaded:
            self.load()

        self.cheat()
        if pyxel.frame_count % 180 == 0 and self.concurrent_enem_spawn != self.num_tanks: #enemy tank spawns in an interval of 3 seconds, maybe this can be configured in the map file for increasing difficulty
            self.generate_enem_tank()

        if pyxel.btn(pyxel.KEY_CTRL) and pyxel.btn(pyxel.KEY_N): #restart game
            self.internal_level = 1
            self.hp = 2
            self.map_loaded = False
            self.load()

        if self.player_tank.hp == 0 and pyxel.btnp(pyxel.KEY_R) and not self.is_gameover:
            self.player_tank = Tank(self.spawnpoint[0], self.spawnpoint[1], 'right', 1, 1, False, Bullet(0, 0, 'right', False, 'player'))
            self.map_database[self.spawnpoint[1]][self.spawnpoint[0]] = self.player_tank
            
        if self.is_gameover or self.is_win:
            if pyxel.frame_count > self.frames:
                self.undraw = True
                pyxel.stop() # stop music

            if self.is_gameover and self.undraw and pyxel.btnp(pyxel.KEY_R):
                self.internal_level = 1
                self.hp = 2
                self.map_loaded = False
                self.load()
            elif self.is_win and self.undraw and pyxel.btnp(pyxel.KEY_RETURN):
                self.internal_level += 1
                self.map_loaded = False
                self.load()

        if not self.undraw:
            self.time += 1
            if pyxel.btnp(pyxel.KEY_Q):
                pyxel.quit()

            if self.isdebug and pyxel.btnp(pyxel.KEY_F1): # debug key, instant tank death
                print(self.map_database[self.player_tank.y][self.player_tank.x])
                tanko = self.map_database[self.player_tank.y][self.player_tank.x]
                print('BOOM', tanko)
                if isinstance(tanko, Tank):
                    tanko.hp = 0
            
            if self.isdebug and pyxel.btnp(pyxel.KEY_T): # debug key, checks map state mid-game
                print(self.map_database)

            if pyxel.btn(pyxel.KEY_LEFT):
                print('left pressed!', self.player_tank) if self.isdebug else None
                if pyxel.frame_count % 4 == 0:
                    self.movement('left', 'player', self.player_tank.x, self.player_tank.y, self.player_tank)

            elif pyxel.btn(pyxel.KEY_RIGHT):
                print('right pressed!', self.player_tank) if self.isdebug else None
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
            
            if pyxel.btnp(pyxel.KEY_SPACE) and not self.player_tank.is_shoot and pyxel.frame_count > self.frames_before_starting and self.player_tank.hp != 0: #  # Uncomment this later. This prevents the player from shooting before the game starts
                pyxel.play(3, 0)
                self.player_tank.bullet.x, self.player_tank.bullet.y, self.player_tank.bullet.direction = self.player_tank.x, self.player_tank.y, self.player_tank.direction
                self.player_tank.is_shoot = True
                self.player_tank.bullet.is_shoot = True

            if self.player_tank.is_shoot and self.player_tank.bullet.is_shoot:
                self.movement(self.player_tank.bullet.direction, 'bullet', self.player_tank.bullet.x, self.player_tank.bullet.y, self.player_tank)
            
            self.ai_tanks_moves()

            self.keep_bullet_shooting(self.map_database, self.visited_bullets_so_far)
            self.keep_bullet_shooting(self.duplicate_map_database, self.duplicate_visited_bullets_so_far) # Keep updating overwritten bullets even from dead tanks

            self.eliminate_no_hp_entity()
            
            self.check_rem_tanks()

            self.powerup()

    #generate tutorial messages in sidebar
    def draw_tutorial(self):
        if self.tutorial == -1:
            pyxel.blt(416, 204, 0, 0, 112, 16, 16, 0)
            pyxel.blt(432, 204, 0, 32, 112, 16, 16, 0)
            pyxel.text(402, 222, 'Destroy half of', 7)
            pyxel.text(402, 230, 'the enemy tanks', 7)
            pyxel.text(402, 238, 'quickly to gain', 7)
            pyxel.text(404, 246, 'an extra life!', 7)

        elif self.tutorial == 1:
            pyxel.blt(424, 204, 0, 0, 64, 16, 16, 0)
            pyxel.text(414, 222, 'Do not let', 7)
            pyxel.text(403, 230, 'the enemy tanks', 7)
            pyxel.text(412, 238, 'destroy the', 7)
            pyxel.text(414, 246, 'home base!', 7)

        elif self.tutorial == 2:
            pyxel.blt(424, 204, 0, 16, 16, 16, 16, 0)
            pyxel.text(410, 222, 'TYPE: STONE', 7)
            pyxel.text(414, 230, 'Tanks and', 7)
            pyxel.text(404, 238, 'bullets cannot', 7)
            pyxel.text(408, 246, 'pass through', 7)
        
        elif self.tutorial == 3:
            pyxel.blt(416, 204, 0, 0, 48, 16, 16, 0)
            pyxel.blt(432, 204, 0, 16, 48, 16, 16, 0)
            pyxel.text(410, 222, 'TYPE: BRICK', 7)
            pyxel.text(402, 230, 'Tanks cant pass', 7)
            pyxel.text(402, 238, 'Hit with bullet', 7)
            pyxel.text(406, 246, 'to destroy it', 7)

        elif self.tutorial == 4:
            pyxel.blt(416, 204, 0, 32, 16, 16, 16, 0)
            pyxel.blt(432, 204, 0, 48, 16, 16, 16, 0)
            pyxel.text(409, 222, 'TYPE: MIRROR', 7)
            pyxel.text(402, 230, 'Tanks cant pass', 7)
            pyxel.text(406, 238, 'Changes bullet', 7)
            pyxel.text(414, 246, 'direction', 7)

        elif self.tutorial == 5:
            pyxel.blt(424, 204, 0, 32, 48, 16, 16, 0)
            pyxel.text(410, 222, 'TYPE: WATER', 7)
            pyxel.text(402, 230, 'Tanks cant pass', 7)
            pyxel.text(410, 238, 'Bullets can', 7)
            pyxel.text(409, 246, 'pass through', 7)
        
        elif self.tutorial == 6:
            pyxel.blt(424, 204, 0, 48, 48, 16, 16, 0)
            pyxel.text(410, 222, 'TYPE: FOREST', 7)
            pyxel.text(410, 230, 'Covers Tanks', 7)

        elif self.tutorial == 999:
            pyxel.blt(424, 204, 0, 224, 48, 16, 16, 0)
            pyxel.text(412, 222, 'DEBUG MODE', 7)
            pyxel.text(409, 230, 'Restart game', 7)
            pyxel.text(409, 238, 'to return to', 7)
            pyxel.text(410, 246, 'normal maps', 7)


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
                    elif type(entity) == EnemyTank and entity.label[:7] == 'regular':
                        if entity.direction == 'up':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 0, 32, 16, 16, 0)
                        elif entity.direction == 'down':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 16, 32, 16, 16, 0)
                        elif entity.direction == 'right':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 32, 32, 16, 16, 0)
                        elif entity.direction == 'left':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 48, 32, 16, 16, 0)
                    elif type(entity) == EnemyTank and entity.label[:4] == 'buff':
                        if entity.direction == 'up':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 0, 96-16*(entity.hp-1), 16, 16, 0)
                        elif entity.direction == 'down':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 16, 96-16*(entity.hp-1), 16, 16, 0)
                        elif entity.direction == 'right':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 32, 96-16*(entity.hp-1), 16, 16, 0)
                        elif entity.direction == 'left':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 48, 96-16*(entity.hp-1), 16, 16, 0)
                    elif type(entity) == Bullet:
                        pyxel.blt(entity.x*16, entity.y*16, 0, 0, 16, 16, 16, 0)
                    elif type(entity) == Mirror:
                        if entity.orientation == 'NE':
                            pyxel.blt(entity.x*16, entity.y*16, 0, 32, 16, 16, 16, 0)
                        else:
                            pyxel.blt(entity.x*16, entity.y*16, 0, 48, 16, 16, 16, 0)
                    elif type(entity) == Water:
                        pyxel.blt(entity.x*16, entity.y*16, 0, 32, 48, 16, 16, 0)
                    elif type(entity) == HomeBase:
                        pyxel.blt(entity.x*16, entity.y*16, 0, 0, 64, 16, 16, 0)
                    
            for forest in self.forest_draw: # Overwriting background with the bushes
                pyxel.blt(forest[0]*16, forest[1]*16, 0, 48, 48, 16, 16, 0)
                        
        else:
            if self.is_gameover:
                #pyxel.text((self.screen_width // 2) - 20, (self.screen_height // 2) - 20, 'GAME OVER', 7) # Temporary values. might have to make a game over splash screen instead since the text is small
                pyxel.blt((self.screen_width // 2) - 104, (self.screen_height // 2) - 8, 0, 208, 48, 16, 16)
                pyxel.blt((self.screen_width // 2) - 88, (self.screen_height // 2) - 8, 0, 176, 0, 16, 16)
                pyxel.blt((self.screen_width // 2) - 72, (self.screen_height // 2) - 8, 0, 176, 16, 16, 16)
                pyxel.blt((self.screen_width // 2) - 56, (self.screen_height // 2) - 8, 0, 176, 32, 16, 16)
                pyxel.blt((self.screen_width // 2) - 40, (self.screen_height // 2) - 8, 0, 224, 64, 16, 16)
                pyxel.blt((self.screen_width // 2) - 24, (self.screen_height // 2) - 8, 0, 208, 64, 16, 16)
                pyxel.blt((self.screen_width // 2) - 8, (self.screen_height // 2) - 8, 0, 176, 48, 16, 16)
                pyxel.blt((self.screen_width // 2) + 8, (self.screen_height // 2) - 8, 0, 176, 32, 16, 16)
                pyxel.blt((self.screen_width // 2) + 24, (self.screen_height // 2) - 8, 0, 176, 64, 16, 16)
                pyxel.rect((self.screen_width // 2) - 68, (self.screen_height // 2) + 18, 76, 10, 0)
                pyxel.text((self.screen_width // 2) - 66, (self.screen_height // 2) + 20, 'Press R to Restart', 10)
            elif self.is_win:
                #pyxel.text((self.screen_width // 2) - 20, (self.screen_height // 2) - 20, 'YOU WIN!', 7)
                pyxel.blt((self.screen_width // 2) - 88, (self.screen_height // 2) - 8, 0, 192, 0, 16, 16)
                pyxel.blt((self.screen_width // 2) - 72, (self.screen_height // 2) - 8, 0, 208, 64, 16, 16)
                pyxel.blt((self.screen_width // 2) - 56, (self.screen_height // 2) - 8, 0, 192, 16, 16, 16)
                pyxel.blt((self.screen_width // 2) - 40, (self.screen_height // 2) - 8, 0, 224, 64, 16, 16)
                pyxel.blt((self.screen_width // 2) - 24, (self.screen_height // 2) - 8, 0, 192, 32, 16, 16)
                pyxel.blt((self.screen_width // 2) - 8, (self.screen_height // 2) - 8, 0, 192, 48, 16, 16)
                pyxel.blt((self.screen_width // 2) + 8, (self.screen_height // 2) - 8, 0, 192, 64, 16, 16)
                pyxel.rect((self.screen_width // 2) - 82, (self.screen_height // 2) + 18, 98, 10, 0)
                pyxel.text((self.screen_width // 2) - 78, (self.screen_height // 2) + 20, 'Press Enter to continue', 10)


        # Overwriting enemy tanks with their enemy tank bullets
        for row in self.duplicate_map_database:
            for entity in row:
                if type(entity) == Bullet:
                    pyxel.blt(entity.x*16, entity.y*16, 0, 0, 16, 16, 16, 0)

        # Countdown timer before starting the game
        if self.frames_before_starting - pyxel.frame_count >= 0:
            countdown = self.frames_before_starting - pyxel.frame_count
            if countdown >= 180:
                #pyxel.text((self.screen_width // 2) - 30, (self.screen_height // 2) - 1, '3', 0)
                pyxel.blt((self.screen_width // 2) - 40, (self.screen_height // 2) - 8, 0, 208, 0, 16, 16)
            elif countdown >= 120:
                #pyxel.text((self.screen_width // 2) - 30, (self.screen_height // 2) - 1, '2', 0)
                pyxel.blt((self.screen_width // 2) - 40, (self.screen_height // 2) - 8, 0, 208, 16, 16, 16)
            elif countdown >= 60:
                #pyxel.text((self.screen_width // 2) - 30, (self.screen_height // 2) - 1, '1', 0)
                pyxel.blt((self.screen_width // 2) - 40, (self.screen_height // 2) - 8, 0, 208, 32, 16, 16)
            else:
                #pyxel.text((self.screen_width // 2) - 30, (self.screen_height // 2) - 1, 'GO!', 0)
                pyxel.blt((self.screen_width // 2) - 56, (self.screen_height // 2) - 8, 0, 208, 48, 16, 16)
                pyxel.blt((self.screen_width // 2) - 40, (self.screen_height // 2) - 8, 0, 208, 64, 16, 16)
                pyxel.blt((self.screen_width // 2) - 24, (self.screen_height // 2) - 8, 0, 208, 80, 16, 16)

        #Sidebar UI elements
        pyxel.rect(400, 0, 64, self.screen_height, 0)
        pyxel.text(410, 4, 'Battle City', 7)
        pyxel.text(410, 12, f'Level: {self.level}', 7)
        pyxel.text(410, 20, self.stage_name, 7) #level names must be restricted to 12 characters (including whitespace)
        pyxel.text(410, 28, f'Time: {self.time}', 7)
        pyxel.line(400, 38, 464, 38, 7)

        #lives remaining
        pyxel.blt(416, 46, 0, 0, 112, 16, 16, 0)
        if self.hp < 10:
            pyxel.blt(432, 46, 0, 240, self.hp*16, 16, 16, 0)
        else:
            pyxel.blt(429, 46, 0, 240, (self.hp//10)*16, 16, 16, 0)
            pyxel.blt(436, 46, 0, 240, (self.hp - (self.hp//10)*10)*16, 16, 16, 0)

        #tanks remaining
        pyxel.blt(416, 62, 0, 0, 32, 16, 16, 0)
        if self.rem_tanks < 10:
            pyxel.blt(432, 62, 0, 240, self.rem_tanks*16, 16, 16, 0) # single digit tanks remaining
        else:
            pyxel.blt(429, 62, 0, 240, (self.rem_tanks//10)*16, 16, 16, 0)
            pyxel.blt(436, 62, 0, 240, (self.rem_tanks - (self.rem_tanks//10)*10)*16, 16, 16, 0) # 2 digits

        pyxel.line(400, 87, 464, 87, 7)

        #how to play
        pyxel.text(410, 96, 'HOW TO PLAY', 7)

        pyxel.blt(424, 100, 0, 224, 16, 16, 16, 0)
        pyxel.text(406, 116, 'Use the arrow', 7)
        pyxel.text(408, 124, 'keys to move', 7)

        pyxel.blt(424, 132, 0, 224, 32, 16, 16, 0)
        pyxel.text(406, 148, 'Use space bar', 7)
        pyxel.text(416, 156, 'to shoot', 7)

        pyxel.blt(416, 164, 0, 0, 32, 16, 16, 0)
        pyxel.blt(432, 164, 0, 0, 80, 16, 16, 0)
        pyxel.text(410, 184, 'Destroy the', 7)
        pyxel.text(410, 192, 'enemy tanks', 7)

        if self.player_tank.hp == 0:
            pyxel.blt(424, 204, 0, 48, 112, 16, 16, 0)
            pyxel.text(416, 222, 'YOU DIED!', 7)
            pyxel.text(403, 230, '', 7)
            pyxel.text(414, 238, 'Press R to', 7)
            pyxel.text(418, 246, 'Respawn!', 7)
        else:
            self.draw_tutorial()

        pyxel.line(400, 256, 464, 256, 7)

        pyxel.text(402, 262, f'Powerup({self.powerup_time_limit})', 7)
        if not self.powerup_got and (self.time < self.powerup_time_limit - 120):
            pyxel.blt(454, 260, 0, 24, 112, 8, 8, 0)
        elif not self.powerup_got and (self.time < self.powerup_time_limit):
            if self.time % 5 == 0:
                pyxel.blt(454, 260, 0, 24, 112, 8, 8, 0)
        else:
            pyxel.blt(454, 260, 0, 24, 120, 8, 8, 0)

        if self.powerup_got:
            pyxel.blt(454, 260, 0, 16, 112, 8, 8, 0)

        # The deeper the code here, the more it will be drawn on top of the other entities
                

Game()


    

