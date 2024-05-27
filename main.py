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

        #self.tank = Tank(0, 0, 'right', 1, 1)
        #self.bullet = Bullet(self.tank.x, self.tank.y, self.tank.direction)

        self.screen_width = 400
        self.screen_height = 256

        self.is_shoot_bullet = False

        self.num_stones: int = 10
        self.num_tanks: int = 5

        #self.stone_cells_location: list[Stone] = []
        #self.enem_tank: list[Tank] = []

        pyxel.init(self.screen_width, self.screen_height, fps=60)

        self.generate_player_tank()
        self.generate_stone_cells()
        self.generate_enem_tank()
        print(self.map_database) # just to check what it looks like after generating

        pyxel.load('assets/assets.pyxres')
        pyxel.run(self.update, self.draw)

    # -- Generator Functions --
    # Main priority in generation is to ensure that the tanks and stones do not overlap each other
    def generate_stone_cells(self):
        for _ in range(self.num_stones):
            x_i = randint(0, 24)
            y_i = randint(0, 15)

            if self.check_if_pos_is_unique(x_i, y_i):
                stone = Stone(x_i,y_i)
                self.map_database[y_i][x_i] = stone
                #self.stone_cells_location.append(stone)

    def generate_player_tank(self):
        tank = Tank(0, 0, 'right', 1, 1)
        self.player_tank_pos = (0,0)
        self.map_database[0][0] = tank

    def generate_enem_tank(self):
        for _ in range(self.num_tanks):
            x_i = randint(0, 24)
            y_i = randint(0, 15)

            if self.check_if_pos_is_unique(x_i, y_i):
                enem_tank = EnemyTank(x_i, y_i, 'up', 1, 1)
                self.map_database[y_i][x_i] = enem_tank
                #self.enem_tank.append(enem_tank)

    # -- End of Generator Functions --

    
    def check_if_pos_is_unique(self, x: int, y: int) -> bool:
        return self.map_database[y][x] == 0

    # def shoot_bullets(self):
    #     print('Bullet position:', self.bullet.x, self.bullet.y)
    #     if self.bullet.x < 0 or self.bullet.y < 0 or self.bullet.x > self.screen_width or self.bullet.y > self.screen_height:
    #         self.is_shoot_bullet = False
    #         print(self.is_shoot_bullet)

    #     if self.bullet.direction == 'up':
    #         if not self.collision('up', self.bullet.x, self.bullet.y):
    #             self.bulletcollision('up', self.bullet.x, self.bullet.y)
    #             self.is_shoot_bullet = False
    #         self.bullet.y -= 16
        
    #     if self.bullet.direction == 'down':
    #         if not self.collision('down', self.bullet.x, self.bullet.y):
    #             self.bulletcollision('down', self.bullet.x, self.bullet.y)
    #             self.is_shoot_bullet = False
    #         self.bullet.y += 16

    #     if self.bullet.direction == 'left':
    #         if not self.collision('left', self.bullet.x, self.bullet.y):
    #             self.bulletcollision('left', self.bullet.x, self.bullet.y)
    #             self.is_shoot_bullet = False
    #         self.bullet.x -= 16

    #     if self.bullet.direction == 'right':
    #         if not self.collision('right', self.bullet.x, self.bullet.y):
    #             self.bulletcollision('right', self.bullet.x, self.bullet.y)
    #             self.is_shoot_bullet = False
    #         self.bullet.x += 16

    # def tankhp(self):
    #     for tank in self.enem_tank:
    #         if tank.hp == 0:
    #             self.enem_tank.remove(tank)

# generate objects in environment
# TODO Make collision checks so that the tanks and stones do not overlap each other in generation
# sidenote: this check might only have to be applied on tanks once we implement the map loading feature
#-------------------------------------------------------------------------------------

# main collision checker + entity movement function
    def movement(self, direction: str, entity: str, x: int, y: int):
        current_point = (x,y)
        point = (0,0)
        dirvector = [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]

        #checks which input was made in order to use the correct dirvector tuple
        if direction == 'left':
            point = dirvector[0]
            
        if direction == 'right':
            point = dirvector[1]
        
        if direction == 'up':
            point = dirvector[2]
        
        if direction == 'down':
            point = dirvector[3]


        #check if there is an entity ahead of the entity trying to move, if there is one, do not move
        if type(self.map_database[point[1]][point[0]]) == Stone:
            print('YOU SHALL NOT PASS!!')
            pass
        elif isinstance(self.map_database[point[1]][point[0]], EnemyTank):
            print('YOU SHALL NOT PASS!!')
            pass
        
        #reflect changes into map_database
        else:
            self.map_database[point[1]][point[0]] = self.map_database[current_point[1]][current_point[0]]
            entity_move = self.map_database[point[1]][point[0]]

            print(self.map_database[point[1]][point[0]])

            if isinstance(entity_move, (Stone, Brick, Tank, Bullet)):
                entity_move.x = point[0]
                entity_move.y = point[1]
            
            self.map_database[current_point[1]][current_point[0]] = 0

            if entity == 'player':
                
                self.player_tank_pos = (point[0],point[1])
                if isinstance(entity_move, Tank):
                    entity_move.direction = direction

            if entity == 'bullet': #not yet implemented
                pass

        #s_point = Stone(point[0],point[1])

        #if s_point in self.stone_cells_location:
            #return False
            
        #for tank in self.enem_tank:
           #if point == (tank.x,tank.y):
                #return False
            
        #return True

    def bulletcollision(self, direction: str, x: int, y: int):
        point = (0,0)
        dirvector = [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]

        if direction == 'left':
            point = dirvector[0]
            
        if direction == 'right':
            point = dirvector[1]
        
        if direction == 'up':
            point = dirvector[2]
        
        if direction == 'down':
            point = dirvector[3]

        #s_point = Stone(point[0],point[1])

        #if s_point in self.stone_cells_location:
            #return None
            
        for tank in self.enem_tank:
            if point == (tank.x,tank.y):
                tank.hp = 0
            
        #return True
        
    # potential idea for code optimization:
    # what if instead of having multiple functions defined for each type of collision (stone, wall, tank, bullet)
    # we push everything into one function

    # that is, we only need to get the coordinates of the next position that the object needs to travel to
    # then, using those coordinates, we can check in each list (stone, tanks, out of bounds area)
    # then if something matches there, we can apply the respective collision logic

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        if pyxel.btnp(pyxel.KEY_T): # debug key, checks map state mid-game
            print(self.map_database)

        if pyxel.btn(pyxel.KEY_LEFT) and self.player_tank_pos[0] > 0:
            print('left pressed!')
            if pyxel.frame_count % 4 == 0:
                self.movement('left', 'player', self.player_tank_pos[0], self.player_tank_pos[1])
            # if pyxel.frame_count % 4 == 0:
            #     self.tank.x -= self.tank.speed
            #     self.tank.direction = 'left'
            

        elif pyxel.btn(pyxel.KEY_RIGHT) and self.player_tank_pos[0] + 1 < self.screen_width//16:
            print('right pressed!')
            if pyxel.frame_count % 4 == 0:
                self.movement('right', 'player', self.player_tank_pos[0], self.player_tank_pos[1])
            # if pyxel.frame_count % 4 == 0:
            #     self.tank.x += self.tank.speed
            #     self.tank.direction = 'right'


        elif pyxel.btn(pyxel.KEY_UP) and self.player_tank_pos[1] > 0:
            print('up pressed!')
            if pyxel.frame_count % 4 == 0:
                self.movement('up', 'player', self.player_tank_pos[0], self.player_tank_pos[1])
            # if pyxel.frame_count % 4 == 0:
            #     self.tank.y -= self.tank.speed
            #     self.tank.direction = 'up'


        elif pyxel.btn(pyxel.KEY_DOWN) and self.player_tank_pos[1] + 1 < self.screen_height//16:
            print('down pressed!')
            if pyxel.frame_count % 4 == 0:
                self.movement('down', 'player', self.player_tank_pos[0], self.player_tank_pos[1])
            # if pyxel.frame_count % 4 == 0:
            #     self.tank.y += self.tank.speed
            #     self.tank.direction = 'down'

        #self.tankhp()

        if self.is_shoot_bullet:
            self.shoot_bullets()

        if pyxel.btnp(pyxel.KEY_SPACE) and not self.is_shoot_bullet:
            self.is_shoot_bullet = True
            self.bullet.direction = self.tank.direction
            self.bullet.x = self.tank.x
            self.bullet.y = self.tank.y
        ...


    def draw(self):
        pyxel.cls(0)

        # tank



        # bullet
        #if self.is_shoot_bullet:
            #pyxel.blt(self.bullet.x, self.bullet.y, 0, 0, 16, 16, 16, 0)

        
        # stone cells
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

        # enemy tanks
        #for tan in self.enem_tank:
            #if tan.hp != 0:
                

Game()


    

