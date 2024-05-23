import pyxel
from dataclasses import dataclass
# from time import sleep
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

@dataclass
class Stone:
    x: int
    y: int

class Game:
    def __init__(self):
        self.tank = Tank(0, 0, 'right', 16)
        self.bullet = Bullet(self.tank.x, self.tank.y, self.tank.direction)


        self.screen_width = 400
        self.screen_height = 256

        self.is_shoot_bullet = False

        self.num_stones: int = 10
        self.stone_cells_location: list[Stone] = []

        pyxel.init(self.screen_width, self.screen_height, fps=24)

        self.generate_stone_cells()

        pyxel.load('assets/assets.pyxres')
        pyxel.run(self.update, self.draw)



    def shoot_bullets(self):
        print('Bullet position:', self.bullet.x, self.bullet.y)
        if self.bullet.x < 0 or self.bullet.y < 0 or self.bullet.x > self.screen_width or self.bullet.y > self.screen_height:
            
            self.is_shoot_bullet = False
            print(self.is_shoot_bullet)

        if self.bullet.direction == 'up':
            if not self.collision('up', self.bullet.x, self.bullet.y):
                self.is_shoot_bullet = False
            self.bullet.y -= 16
        
        if self.bullet.direction == 'down':
            if not self.collision('down', self.bullet.x, self.bullet.y):
                self.is_shoot_bullet = False
            self.bullet.y += 16

        if self.bullet.direction == 'left':
            if not self.collision('left', self.bullet.x, self.bullet.y):
                self.is_shoot_bullet = False
            self.bullet.x -= 16

        if self.bullet.direction == 'right':
            if not self.collision('right', self.bullet.x, self.bullet.y):
                self.is_shoot_bullet = False
            self.bullet.x += 16

            

    def generate_stone_cells(self):
        
        for _ in range(self.num_stones):
            stone = Stone(x=16 * randint(1, 24), y=16 * randint(1, 15))

            self.stone_cells_location.append(stone)

        print(self.stone_cells_location)

        

    def collision(self, direction: str, x: int, y: int):
        if direction == 'left':
            left_x = x - 16
            left_y = y
            point = Stone(left_x, left_y)

            if point in self.stone_cells_location:
                return False
            return True

        if direction == 'right':
            right_x = x + 16
            right_y = y
            point = Stone(right_x, right_y)
            
            if point in self.stone_cells_location:
                return False
            return True
        
        if direction == 'up':
            up_x = x
            up_y = y - 16
            point = Stone(up_x, up_y)

            if point in self.stone_cells_location:
                return False
            return True
        
        if direction == 'down':
            down_x = x
            down_y = y + 16
            point = Stone(down_x, down_y)

            if point in self.stone_cells_location:
                return False
            return True
        

    def update(self):

        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()


        if pyxel.btn(pyxel.KEY_LEFT) and self.tank.x > 0 and self.collision('left', self.tank.x, self.tank.y):
            self.tank.x -= self.tank.speed
            self.tank.direction = 'left'
            

        elif pyxel.btn(pyxel.KEY_RIGHT) and self.tank.x + 16 < self.screen_width and self.collision('right', self.tank.x, self.tank.y):
            self.tank.x += self.tank.speed
            self.tank.direction = 'right'


        elif pyxel.btn(pyxel.KEY_UP) and self.tank.y > 0 and self.collision('up', self.tank.x, self.tank.y):
            self.tank.y -= self.tank.speed
            self.tank.direction = 'up'


        elif pyxel.btn(pyxel.KEY_DOWN) and self.tank.y + 16 < self.screen_height and self.collision('down', self.tank.x, self.tank.y):
            self.tank.y += self.tank.speed
            self.tank.direction = 'down'


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
        if self.tank.direction == 'up':
            pyxel.blt(self.tank.x, self.tank.y, 0, 0, 0, 16, 16, 0)
        elif self.tank.direction == 'down':
            pyxel.blt(self.tank.x, self.tank.y, 0, 16, 0, 16, 16, 0)
        elif self.tank.direction == 'right':
            pyxel.blt(self.tank.x, self.tank.y, 0, 32, 0, 16, 16, 0)
        elif self.tank.direction == 'left':
            pyxel.blt(self.tank.x, self.tank.y, 0, 48, 0, 16, 16, 0)


        # bullet
        if self.is_shoot_bullet:
            pyxel.blt(self.bullet.x, self.bullet.y, 0, 0, 16, 16, 16, 0)

        
        # stone cells
        for point in self.stone_cells_location:
            pyxel.blt(point.x, point.y, 0, 16, 16, 16, 16, 0)
        
            
        

            

Game()


    

