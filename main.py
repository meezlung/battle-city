import pyxel
from dataclasses import dataclass
import pyxelgrid # type: ignore
from random import randint

@dataclass
class Bullet:
    x: int
    y: int
    direction: str

@dataclass
class Tank:
    x: int
    y: int
    direction: str
    speed: int
    hp: int

@dataclass
class EnemyTank(Tank):
    pass

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
        self.num_tanks: int = 5

        pyxel.init(self.screen_width, self.screen_height, fps=60, )

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
        tank = Tank(0, 0, 'right', 1, 1)
        self.player_tank_pos: tuple[int, int, str] = (0, 0, 'right')
        self.player_bullet_pos: tuple[int, int, str] = (0, 0, 'right')
        self.map_database[0][0] = tank

    def generate_enem_tank(self):
        for _ in range(self.num_tanks):
            x_i = randint(0, 24)
            y_i = randint(0, 15)

            if self.check_if_pos_is_unique(x_i, y_i):
                enem_tank = EnemyTank(x_i, y_i, 'up', 1, 1) # randomize direction soon
                self.map_database[y_i][x_i] = enem_tank

    def generate_static_bullet_pos(self):
        self.player_bullet_pos = (self.player_tank_pos[0], self.player_tank_pos[1], self.player_tank_pos[2])
        ...
    # -- End of Generator Functions --


    def check_if_pos_is_unique(self, x: int, y: int) -> bool:
        return self.map_database[y][x] == 0

    # check tank hp, remove tank if hp == 0
    def tankhp(self):
         for row in self.map_database:
             for tank in row:
                if isinstance(tank, (Tank, EnemyTank)):
                    if tank.hp == 0:
                        destroyposrow = self.map_database.index(row)
                        destroypos = self.map_database[destroyposrow].index(tank)
                        self.map_database[destroyposrow][destroypos] = 0

    # main collision checker + entity movement function
    def movement(self, direction: str, entity: str, x: int, y: int):
        current_point = (x, y)
        point = (0, 0)
        dirvector: dict[str, tuple[int, int]] = {
            'left': (x - 1, y),
            'right': (x + 1, y),
            'up': (x, y - 1),
            'down': (x, y + 1)
        }

        # checks which input was made in order to use the correct dirvector tuple
        if direction in dirvector:
            point = dirvector[direction]

        # bounds checking:
        if not (0 <= point[0] < self.screen_width//16) or not (0 <= point[1] < self.screen_height//16):
            print('YOU SHALL NOT PASS!!')
            if entity == 'player':
                entity_move = self.map_database[current_point[1]][current_point[0]] 
                if isinstance(entity_move, Tank):
                    entity_move.direction = direction
            if entity == 'bullet':
                if type(self.map_database[current_point[1]][current_point[0]]) != Tank:
                    self.map_database[current_point[1]][current_point[0]] = 0
                self.is_shoot_bullet = False

        # check if there is an entity ahead of the entity trying to move, if there is one, do not move
        elif isinstance(self.map_database[point[1]][point[0]], Stone):
            if entity == 'player':
                entity_move = self.map_database[current_point[1]][current_point[0]] 
                if isinstance(entity_move, Tank):
                    entity_move.direction = direction
            print('YOU SHALL NOT PASS!!')
            # might need to refactor this code some time...
            if entity == 'bullet':
                if type(self.map_database[current_point[1]][current_point[0]]) != Tank:
                    self.map_database[current_point[1]][current_point[0]] = 0
                self.is_shoot_bullet = False

        elif isinstance(self.map_database[point[1]][point[0]], EnemyTank):
            print('YOU SHALL NOT PASS!!')
            if entity == 'player':
                entity_move = self.map_database[current_point[1]][current_point[0]] 
                if isinstance(entity_move, Tank):
                    entity_move.direction = direction
            if entity == 'bullet':
                if type(self.map_database[current_point[1]][current_point[0]]) != Tank:
                    self.map_database[current_point[1]][current_point[0]] = 0
                self.is_shoot_bullet = False
                chk_entity = self.map_database[point[1]][point[0]]
                if isinstance(chk_entity, (EnemyTank)):
                    chk_entity.hp -= 1

        # reflect changes into map_database
        else:
            # a bullet generates differently than any other entity, thus it must be treated as a separate case
            if entity == 'bullet': 
                self.map_database[point[1]][point[0]] = Bullet(point[0], point[1], direction)
                self.player_bullet_pos = (point[0], point[1], direction)

                # edge case - if the bullet just spawned, this will prevent setting the tank to 0
                if isinstance(self.map_database[current_point[1]][current_point[0]], Bullet):
                    self.map_database[current_point[1]][current_point[0]] = 0

            else:
                self.map_database[point[1]][point[0]] = self.map_database[current_point[1]][current_point[0]]

                entity_move = self.map_database[point[1]][point[0]]

                if isinstance(entity_move, (Tank)):
                    entity_move.x = point[0]
                    entity_move.y = point[1]
            
                self.map_database[current_point[1]][current_point[0]] = 0

                if entity == 'player':
                    self.player_tank_pos = (point[0], point[1], direction)
                    if isinstance(entity_move, Tank):
                        entity_move.direction = direction


    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        if pyxel.btnp(pyxel.KEY_T): # debug key, checks map state mid-game
            print(self.map_database)

        if pyxel.btn(pyxel.KEY_LEFT):
            print('left pressed!')
            if pyxel.frame_count % 4 == 0:
                self.movement('left', 'player', self.player_tank_pos[0], self.player_tank_pos[1])

        elif pyxel.btn(pyxel.KEY_RIGHT):
            print('right pressed!')
            if pyxel.frame_count % 4 == 0:
                self.movement('right', 'player', self.player_tank_pos[0], self.player_tank_pos[1])

        elif pyxel.btn(pyxel.KEY_UP):
            print('up pressed!')
            if pyxel.frame_count % 4 == 0:
                self.movement('up', 'player', self.player_tank_pos[0], self.player_tank_pos[1])

        elif pyxel.btn(pyxel.KEY_DOWN):
            print('down pressed!')
            if pyxel.frame_count % 4 == 0:
                self.movement('down', 'player', self.player_tank_pos[0], self.player_tank_pos[1])

        self.tankhp()

        if pyxel.btnp(pyxel.KEY_SPACE) and not self.is_shoot_bullet:
            self.is_shoot_bullet = True
            self.generate_static_bullet_pos()

        if self.is_shoot_bullet:
            print('shooting!', self.player_bullet_pos)
            self.movement(self.player_bullet_pos[2], 'bullet', self.player_bullet_pos[0], self.player_bullet_pos[1])



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
                    pyxel.blt(entity.x*16, entity.y*16, 0, 0, 32, 16, 16, 0)
                elif type(entity) == Bullet:
                    pyxel.blt(entity.x*16, entity.y*16, 0, 0, 16, 16, 16, 0)


                

Game()


    

