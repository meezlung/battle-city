import pyxel
from dataclasses import dataclass
import pyxelgrid # type: ignore
from random import randint, choice
from typing import Literal, cast

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

class Game:
    def __init__(self):
        self.map_database: list[list[Stone | Brick | Tank | EnemyTank | Bullet | int]] = [[0 for _ in range(25)] for _ in range(16)] #initialize the map

        self.screen_width = 400
        self.screen_height = 256

        self.is_shoot_bullet = False

        self.num_stones: int = 10
        self.num_tanks: int = 1

        self.visited_enemy_tanks_so_far: set[str] = set() 
        self.visited_bullets_so_far: set[str] = set()

        pyxel.init(self.screen_width, self.screen_height, fps=60)

        self.generate_player_tank()
        self.generate_stone_cells()
        self.generate_enem_tank()

        pyxel.load('assets/assets.pyxres')
        pyxel.run(self.update, self.draw)

    # -- Generator Functions --
    # Main priority in generation is to ensure that the tanks and stones do not overlap each other
    def generate_stone_cells(self):
        for _ in range(self.num_stones):
            x_i = randint(0, 24)
            y_i = randint(0, 15)

            if self.check_if_pos_is_unique(x_i, y_i):
                stone = Stone(x_i, y_i)
                self.map_database[y_i][x_i] = stone

    def generate_player_tank(self):
        self.player_tank = Tank(0, 0, 'right', 1, 1, False, Bullet(0, 0, 'right', False,'player'))
        self.map_database[0][0] = self.player_tank

    def generate_enem_tank(self):
        random_label = 33
        for _ in range(self.num_tanks):
            x_i = randint(0, 24)
            y_i = randint(0, 15)

            if self.check_if_pos_is_unique(x_i, y_i):
                print(x_i, y_i)
                enem_tank = EnemyTank(x_i, y_i, 'up', 1, 1, False, Bullet(x_i, y_i, 'up', False, chr(random_label)), chr(random_label)) # we should generate randomize labels infinitely to prevent bug in infinitely many tanks generation
                self.map_database[y_i][x_i] = enem_tank
                random_label += 1
            else:
                while not self.check_if_pos_is_unique(x_i, y_i):
                    x_i = randint(0, 24)
                    y_i = randint(0, 15)
                    
                    if self.check_if_pos_is_unique(x_i, y_i):
                        enem_tank = EnemyTank(x_i, y_i, 'up', 1, 1, False, Bullet(x_i, y_i, 'up', False, chr(random_label)), chr(random_label)) # we should generate randomize labels infinitely to prevent bug in infinitely many tanks generation
                        self.map_database[y_i][x_i] = enem_tank
                        break

                    random_label += 1

    # -- End of Generator Functions --


    def check_if_pos_is_unique(self, x: int, y: int) -> bool:
        return self.map_database[y][x] == 0

    # check tank hp, remove tank if hp == 0
    def eliminate_no_tankhp(self):
         for row in self.map_database:
             for tank in row:
                if isinstance(tank, (Tank, EnemyTank)):
                    if tank.hp == 0:
                        destroyposrow = self.map_database.index(row)
                        destroypos = self.map_database[destroyposrow].index(tank)
                        self.map_database[destroyposrow][destroypos] = 0

    def keep_bullet_shooting(self):
        for row in self.map_database:
            for bullet in row:
                if isinstance(bullet, Bullet):
                    if bullet.is_shoot:
                        self.movement(bullet.direction, 'bullet', bullet.x, bullet.y, bullet)
                        self.visited_bullets_so_far.add(bullet.label)
        self.visited_bullets_so_far.clear()

    # main collision checker + entity movement function
    def movement(self, direction: Literal['left', 'right', 'up', 'down'], entity: Literal['player', 'bullet', 'enemy'], x: int, y: int, is_from: Tank | EnemyTank | Bullet):
        current_point = (x, y)
        point = {'left': (x - 1, y), 'right': (x + 1, y), 'up': (x, y - 1), 'down': (x, y + 1)}.get(direction, (x, y))

        # bounds checking:
        if not (0 <= point[0] < self.screen_width//16) or not (0 <= point[1] < self.screen_height//16):
            print('YOU SHALL NOT PASS!!, wall', current_point)
            if entity == 'player':
                entity_move = self.map_database[current_point[1]][current_point[0]] 
                if isinstance(entity_move, Tank):
                    entity_move.direction = direction
                    entity_move.bullet.direction = direction
            if entity == 'enemy':
                entity_move = self.map_database[current_point[1]][current_point[0]] 
                if isinstance(entity_move, EnemyTank):
                    entity_move.direction = direction
                    entity_move.bullet.direction = direction
            if entity == 'bullet':
                if type(self.map_database[current_point[1]][current_point[0]]) not in (Tank, EnemyTank):
                    self.map_database[current_point[1]][current_point[0]] = 0
                is_from.is_shoot = False

        # check if there is an entity ahead of the entity trying to move, if there is one, do not move
        elif isinstance(self.map_database[point[1]][point[0]], Stone):
            if entity == 'player':
                entity_move = self.map_database[current_point[1]][current_point[0]] 
                if isinstance(entity_move, Tank):
                    entity_move.direction = direction
                    entity_move.bullet.direction = direction
            if entity == 'enemy':
                entity_move = self.map_database[current_point[1]][current_point[0]] 
                if isinstance(entity_move, EnemyTank):
                    entity_move.direction = direction
                    entity_move.bullet.direction = direction
            print('YOU SHALL NOT PASS!!, stone')
            # might need to refactor this code some time...
            if entity == 'bullet':
                if type(self.map_database[current_point[1]][current_point[0]]) not in (Tank, EnemyTank):
                    self.map_database[current_point[1]][current_point[0]] = 0
                is_from.is_shoot = False

        elif isinstance(self.map_database[point[1]][point[0]], EnemyTank):
            print('YOU SHALL NOT PASS!!, enem')
            if entity == 'player':
                entity_move = self.map_database[current_point[1]][current_point[0]] 
                if isinstance(entity_move, Tank):
                    entity_move.direction = direction
                    entity_move.bullet.direction = direction
            if entity == 'enemy':
                entity_move = self.map_database[current_point[1]][current_point[0]] 
                if isinstance(entity_move, EnemyTank):
                    entity_move.direction = direction
                    entity_move.bullet.direction = direction
            if entity == 'bullet':
                if type(self.map_database[current_point[1]][current_point[0]]) not in (Tank, EnemyTank):
                    self.map_database[current_point[1]][current_point[0]] = 0
                is_from.is_shoot = False
                chk_entity = self.map_database[point[1]][point[0]]
                if isinstance(chk_entity, (EnemyTank)):
                    chk_entity.hp -= 1

        # reflect changes into map_database
        else:
            # a bullet generates differently than any other entity, thus it must be treated as a separate case
            if entity == 'bullet': 
                if isinstance(is_from, (Tank, EnemyTank)):
                    self.map_database[point[1]][point[0]] = Bullet(point[0], point[1], direction, True, is_from.bullet.label)
                    is_from.bullet.x, is_from.bullet.y, is_from.bullet.direction = (point[0], point[1], direction)
                
                if isinstance(is_from, Bullet):
                    self.map_database[point[1]][point[0]] = Bullet(point[0], point[1], direction, True, is_from.label)
                    is_from.x, is_from.y, is_from.direction = (point[0], point[1], direction)

                # edge case - if the bullet just spawned, this will prevent setting the tank to 0
                if isinstance(self.map_database[current_point[1]][current_point[0]], Bullet):
                    self.map_database[current_point[1]][current_point[0]] = 0

            else:
                if self.map_database[point[1]][point[0]] == 0:
                    self.map_database[point[1]][point[0]] = self.map_database[current_point[1]][current_point[0]]

                    entity_move = self.map_database[point[1]][point[0]]

                    self.map_database[current_point[1]][current_point[0]] = 0

                    if entity == 'player':
                        self.player_tank_pos = (point[0], point[1], direction)
                        if isinstance(entity_move, Tank):
                            entity_move.x = point[0]
                            entity_move.y = point[1]
                            entity_move.direction = direction

                    elif entity == 'enemy':
                        if isinstance(entity_move, EnemyTank):
                            entity_move.x = point[0]
                            entity_move.y = point[1]
                            entity_move.direction = direction

                            print('next enemy move', entity_move)


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

                        random_time_interval_to_shoot = randint(3, 5)
                        if pyxel.frame_count % random_time_interval_to_shoot == 0:
                            should_shoot = choice([True, False])     
                            if should_shoot and not entity.is_shoot:
                                entity.bullet.x = entity.x
                                entity.bullet.y = entity.y
                                entity.bullet.direction = entity.direction
                                entity.is_shoot = True

                            if entity.is_shoot:
                                self.movement(entity.bullet.direction, 'bullet', entity.bullet.x, entity.bullet.y, entity)
                        
                        self.visited_enemy_tanks_so_far.add(entity.label)

        self.visited_enemy_tanks_so_far.clear()


    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        if pyxel.btnp(pyxel.KEY_T): # debug key, checks map state mid-game
            print(self.map_database)

        if pyxel.btn(pyxel.KEY_LEFT):
            print('left pressed!', self.player_tank)
            if pyxel.frame_count % 4 == 0:
                self.movement('left', 'player', self.player_tank.x, self.player_tank.y, self.player_tank)

        elif pyxel.btn(pyxel.KEY_RIGHT):
            print('right pressed!', self.player_tank)
            if pyxel.frame_count % 4 == 0:
                self.movement('right', 'player', self.player_tank.x, self.player_tank.y, self.player_tank)

        elif pyxel.btn(pyxel.KEY_UP):
            print('up pressed!', self.player_tank)
            if pyxel.frame_count % 4 == 0:
                self.movement('up', 'player', self.player_tank.x, self.player_tank.y, self.player_tank)

        elif pyxel.btn(pyxel.KEY_DOWN):
            print('down pressed!', self.player_tank)
            if pyxel.frame_count % 4 == 0:
                self.movement('down', 'player', self.player_tank.x, self.player_tank.y, self.player_tank)


        self.eliminate_no_tankhp()
        
        self.ai_tanks_moves()

        # self.keep_bullet_shooting() # this works i think


        if pyxel.btnp(pyxel.KEY_SPACE) and not self.player_tank.is_shoot:
            self.player_tank.bullet.x = self.player_tank.x
            self.player_tank.bullet.y = self.player_tank.y
            self.player_tank.bullet.direction = self.player_tank.direction
            self.player_tank.is_shoot = True

        if self.player_tank.is_shoot:
            print('shooting!', self.player_tank)
            self.movement(self.player_tank.bullet.direction, 'bullet', self.player_tank.bullet.x, self.player_tank.bullet.y, self.player_tank)
        


    def draw(self):
        pyxel.cls(4)

        #generate graphics based on map_database
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


                

Game()


    

