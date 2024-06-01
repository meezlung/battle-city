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

@dataclass
class Mirror:
    x: int
    y: int
    orientation: Literal['NE', 'SE']

class Game:
    def __init__(self):

        self.screen_width = 400
        self.screen_height = 256

        
        pyxel.init(self.screen_width, self.screen_height, fps=60)
        pyxel.load('assets/assets.pyxres')

        self.init_gamestate() # para maplay music even after gameover
        
        pyxel.run(self.update, self.draw)

# ------- Generator Functions -------
    def init_gamestate(self):
        self.is_gameover = False
        self.is_win = False
        self.undraw = False
        self.frames_before_starting = pyxel.frame_count + 200

        self.map_database: list[list[Stone | Brick | Tank | EnemyTank | Bullet | Mirror | int]] = [[0 for _ in range(self.screen_width // 16)] for _ in range(self.screen_height // 16)] # made this adaptable to screen size

        self.num_stones: int = 10 # removed in phase 2
        self.num_mirrors: int = 5 # removed in phase 2
        self.num_tanks: int = 1
        self.rem_tanks = self.num_tanks # this has to be updated every time a new tank spawns in too

        self.visited_enemy_tanks_so_far: set[str] = set() 
        self.visited_bullets_so_far: set[str] = set()

        self.is_shoot_bullet = False

        #pyxel.playm(0, loop=True) # :3

        self.generate_player_tank()
        self.generate_stone_cells()
        self.generate_mirrors()
        self.generate_enem_tank()
        

    # Main priority in generation is to ensure that the tanks and stones do not overlap each other
    def generate_stone_cells(self):
        for _ in range(self.num_stones):
            x_i = randint(0, 24)
            y_i = randint(0, 15)

            if self.check_if_pos_is_unique(x_i, y_i):
                stone = Stone(x_i, y_i)
                self.map_database[y_i][x_i] = stone
    def generate_mirrors(self):
        for _ in range(self.num_mirrors):
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
# ------- End of Generator Functions -------

# ------- Helper Functions -------
    def check_if_pos_is_unique(self, x: int, y: int) -> bool:
        return self.map_database[y][x] == 0

    # Check tank hp, remove tank if hp == 0
    def eliminate_no_tankhp(self):
        for row in self.map_database:
            for tank in row:
                if isinstance(tank, (Tank, EnemyTank)):
                    if tank.hp <= 0:
                        destroyposrow = self.map_database.index(row)
                        destroypos = self.map_database[destroyposrow].index(tank)
                        self.map_database[destroyposrow][destroypos] = 0

                        if type(tank) == Tank and tank.hp == 0:
                            self.is_gameover = True
                            self.frames = pyxel.frame_count + 180
                        else:
                            self.rem_tanks -= 1
                            print(self.rem_tanks)

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
        ...

    def change_direction_of_entity(self, direction: Literal['left', 'right', 'up', 'down'], entity_move: Tank | EnemyTank | Bullet):
        entity_move.direction = direction

    def handle_collision(self, direction: Literal['left', 'right', 'up', 'down'], entity: Literal['player', 'bullet', 'enemy'], curr_x: int, curr_y: int, is_from: Tank | EnemyTank | Bullet):
        entity_move = self.map_database[curr_y][curr_x]

        if entity == 'player' and isinstance(entity_move, Tank):
            self.change_direction_of_entity(direction, entity_move)

        elif entity == 'enemy' and isinstance(entity_move, EnemyTank):
            self.change_direction_of_entity(direction, entity_move)

        elif entity == 'bullet':
            if not isinstance(entity_move, (Tank, EnemyTank)):
                self.map_database[curr_y][curr_x] = 0

            is_from.is_shoot = False # to keep the bullet moving/recursing from a tank or enemy tank

    def handle_bullet_to_bullet_collision(self, new_x: int, new_y: int, curr_x: int, curr_y: int):
        bullet1 = self.map_database[new_y][new_x]
        bullet2 = self.map_database[curr_y][curr_x]

        if type(bullet1) == type(bullet2) and isinstance(bullet1, Bullet) and isinstance(bullet2, Bullet):
            print("Bullet collision happened", bullet1, bullet2)      

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
            return

    def handle_bullet_damage(self, new_x: int, new_y: int, is_from: Bullet | Tank | EnemyTank): # I can shorten this pa, but I just want to see each test cases
        entity_on_new_point = self.map_database[new_y][new_x]

        if type(entity_on_new_point) == Tank:
            if type(is_from) == EnemyTank and is_from.bullet.label != entity_on_new_point.bullet.label:
                print('Player tank hit by enemy tank bullet', is_from.label, entity_on_new_point.bullet.label)
                entity_on_new_point.hp -= 1
                print(entity_on_new_point.hp)

            if type(is_from) == Tank and is_from.bullet.label == entity_on_new_point.bullet.label:
                print('Player tank hit by player tank bullet. Suicidal tank lmao.')
                entity_on_new_point.hp -= 1
                return

            # -- This is when the self.keep_bullet_shooting() is called, i.e. Bullets are moved from dead tanks --
            if type(is_from) == Bullet:
                if is_from.label == 'player':
                    print('Player tank hit by player tank bullet', is_from.label, entity_on_new_point.bullet.label)
                    entity_on_new_point.hp -= 1
                else:
                    print('Player tank hit by enemy tank bullet', is_from.label, entity_on_new_point.bullet.label)
                    entity_on_new_point.hp -= 1
            # -- End of self.keep_bullet_shooting() --

        elif type(entity_on_new_point) == EnemyTank:
            if type(is_from) == Tank and is_from.bullet.label != entity_on_new_point.label:
                print('Enemy tank hit by player tank bullet', is_from.bullet.label, entity_on_new_point.label)
                entity_on_new_point.hp -= 1

            if type(is_from) == EnemyTank:
                print('Enemy tank hit by enemy tank bullet (should pass through)')
                return
             
            # -- This is when the self.keep_bullet_shooting() is called, i.e. Bullets are moved from dead tanks --
            if type(is_from) == Bullet: 
                if is_from.label != 'player':
                    print('Enemy tank hit by enemy tank bullet', is_from.label, entity_on_new_point.label)
                    return
                
                if is_from.label == 'player':
                    print('Enemy tank hit by player tank bullet', is_from.label, entity_on_new_point.label)
                    entity_on_new_point.hp -= 1
            # -- End of self.keep_bullet_shooting() --

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
# ------- Helper Functions -------

# ------- Main collision checker + Entity movement function -------
    def movement(self, direction: Literal['left', 'right', 'up', 'down'], entity: Literal['player', 'bullet', 'enemy'], curr_x: int, curr_y: int, is_from: Tank | EnemyTank | Bullet):
        new_x, new_y = self.get_new_points(curr_x, curr_y, direction)
        
        # Bounds checking
        if not (0 <= new_x < self.screen_width // 16) or not (0 <= new_y < self.screen_height // 16):
            self.handle_collision(direction, entity, curr_x, curr_y, is_from)

        # Check if there is an entity ahead of the entity trying to move, if there is one, do not move
        elif isinstance(self.map_database[new_y][new_x], Stone):
            self.handle_collision(direction, entity, curr_x, curr_y, is_from)

        #if entity ahead is a mirror, separate collision check
        elif entity == 'bullet' and isinstance(self.map_database[new_y][new_x], Mirror):
            mirror = self.map_database[new_y][new_x]
            if isinstance(mirror, (Mirror)):
                orient = mirror.orientation
                mir_x, mir_y, mir_dir = self.get_mirror_points(curr_x, curr_y, direction, orient)
                self.handle_collision(mir_dir,entity,mir_x,mir_y,is_from)
                self.move_bullet(mir_dir,curr_x,curr_y,mir_x,mir_y,is_from)

        elif isinstance(self.map_database[new_y][new_x], (EnemyTank, Tank)):
            self.handle_collision(direction, entity, curr_x, curr_y, is_from)
            if entity == 'bullet': # Bullet finds a tank, tank takes damage
                self.handle_bullet_damage(new_x, new_y, is_from) 

        elif isinstance(self.map_database[new_y][new_x], Bullet):
            if entity == 'bullet': # Bullet finds another bullet, both bullets should disappear
                self.handle_bullet_to_bullet_collision(new_x, new_y, curr_x, curr_y) 

        # Reflect changes into map_database
        else:
            # A bullet generates differently than any other entity, thus it must be treated as a separate case
            if entity == 'bullet': 
                print('Bullet moving')
                self.move_bullet(direction, curr_x, curr_y, new_x, new_y, is_from)

            else:
                self.move_tanks(direction, entity, curr_x, curr_y, new_x, new_y)
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
                                    entity.bullet.x, entity.bullet.y, entity.bullet.direction = entity.x, entity.y, entity.direction
                                    entity.is_shoot = True
                                    entity.bullet.is_shoot = True

                            if entity.is_shoot and entity.bullet.is_shoot:
                                if pyxel.frame_count % 5 == 0:
                                    self.movement(entity.bullet.direction, 'bullet', entity.bullet.x, entity.bullet.y, entity)
                        
                        self.visited_enemy_tanks_so_far.add(entity.label)
        self.visited_enemy_tanks_so_far.clear()



    def update(self):
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

            if self.player_tank.hp > 0: # don't move if player tank dead already
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
                    self.player_tank.bullet.x, self.player_tank.bullet.y, self.player_tank.bullet.direction = self.player_tank.x, self.player_tank.y, self.player_tank.direction
                    self.player_tank.is_shoot = True
                    self.player_tank.bullet.is_shoot = True

                if self.player_tank.is_shoot and self.player_tank.bullet.is_shoot:
                    self.movement(self.player_tank.bullet.direction, 'bullet', self.player_tank.bullet.x, self.player_tank.bullet.y, self.player_tank)
    
            self.eliminate_no_tankhp()
            
            self.ai_tanks_moves()

            self.keep_bullet_shooting()

            self.check_rem_tanks()



    def draw(self):
        pyxel.cls(4)

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
        else:
            if self.is_gameover:
                pyxel.text((self.screen_width // 2) - 20, (self.screen_height // 2) - 20, 'GAME OVER', 1) # Temporary values. might have to make a game over splash screen instead since the text is small
            elif self.is_win:
                pyxel.text((self.screen_width // 2) - 20, (self.screen_height // 2) - 20, 'YOU WIN!', 1)


                

Game()


    

