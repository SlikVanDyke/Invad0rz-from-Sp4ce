import pygame
import os
import time
import random

# globale inits
pygame.font.init()
pygame.mixer.init()
pygame.joystick.init()

WIDTH, HEIGHT = 800, 750
PLAYER_WIDTH, PLAYER_HEIGHT = 75, 60

WIN = pygame.display.set_mode( (WIDTH, HEIGHT) )
pygame.display.set_caption( "Invad0rz from Spa4ce" )

# Enemy Ship
RED_SPACE_SHIP = pygame.image.load( os.path.join( "assets", "pixel_ship_red_small.png" ) )
GREEN_SPACE_SHIP = pygame.image.load( os.path.join( "assets", "pixel_ship_green_small.png" ) )
BLUE_SPACE_SHIP = pygame.image.load( os.path.join( "assets", "pixel_ship_blue_small.png" ) )

# Player Ship
YELLOW_SPACE_SHIP = pygame.transform.scale(
    pygame.transform.rotate( 
        pygame.image.load( os.path.join( "assets", "spaceship_yellow.png" ) ), 180 ), (PLAYER_WIDTH, PLAYER_HEIGHT) )

# Laser
RED_LASER = pygame.image.load( os.path.join( "assets", "pixel_laser_red.png" ) )
GREEN_LASER = pygame.image.load( os.path.join( "assets", "pixel_laser_green.png" ) )
BLUE_LASER = pygame.image.load( os.path.join( "assets", "pixel_laser_blue.png" ) )
YELLOW_LASER = pygame.image.load( os.path.join( "assets", "pixel_laser_yellow.png" ) )

# Background
BG = pygame.transform.scale( 
    pygame.image.load( 
        os.path.join( "assets", "space_bg.png" ) ), (WIDTH, HEIGHT) )

# Soundeffekte
LASER_FIRE_SOUND = pygame.mixer.Sound( os.path.join( "assets", "Gun+Silencer.mp3" ) )
LASER_HIT_SOUND = pygame.mixer.Sound( os.path.join( "assets", "Grenade+1.mp3" ) )
GAME_OVER_SOUND = pygame.mixer.Sound( os.path.join( "assets", "You Died.mp3" ) )

#######################

# Schiff-Klasse
class Ship:
    COOLDOWN = 30

    def __init__( self, x, y, health = 100 ):
        self.x = x
        self.y = y
        self.health = health
        self.ship_image = None
        self.laser_image = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw( self, window ):
        window.blit( self.ship_image, (self.x, self.y) )
        for laser in self.lasers:
            laser.draw( window )

    def move_lasers( self, vel, obj ):
        self.cooldown()
        for laser in self.lasers:
            laser.move( vel )
            if laser.off_screen( HEIGHT ):
                self.lasers.remove( laser )
            elif laser.collision( obj ):
                obj.health -= 10
                LASER_HIT_SOUND.play()
                self.lasers.remove( laser )

    def cooldown( self ):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot( self, play_sound = False ):
        if self.cool_down_counter == 0:
            laser = Laser( self.x + ( ( self.get_width() - self.laser_image.get_width() ) // 2 ), self.y, self.laser_image )
            self.lasers.append( laser )
            self.cool_down_counter = 1
            if play_sound:
                LASER_FIRE_SOUND.play()

    def get_width( self ):
        return self.ship_image.get_width()

    def get_height( self ):
        return self.ship_image.get_height()


# Spieler
class Player( Ship ):
    def __init__( self, x, y, health = 100 ):
        super().__init__( x, y, health )
        self.ship_image = YELLOW_SPACE_SHIP
        self.laser_image = YELLOW_LASER
        self.mask = pygame.mask.from_surface( self.ship_image )
        self.max_health = health

    def move_lasers( self, vel, objs ):
        self.cooldown()
        for laser in self.lasers:
            laser.move( vel )
            if laser.off_screen( HEIGHT ):
                self.lasers.remove( laser )
            else:
                for obj in objs:
                    if laser.collision( obj ):
                        objs.remove( obj )
                        if laser in self.lasers:
                            LASER_HIT_SOUND.play()
                            self.lasers.remove( laser )

    def shoot( self ):
        super().shoot( True )

    def healthbar( self, window ):
        pygame.draw.rect( window, (255, 0, 0), (self.x, self.y + self.ship_image.get_height() + 10, self.ship_image.get_width(), 10) )
        pygame.draw.rect( window, (0, 255, 0), (self.x, self.y + self.ship_image.get_height() + 10, self.ship_image.get_width() * ( self.health / self.max_health ), 10) )
    
    def draw( self, window ):
        super().draw( window )
        self.healthbar( window )


# Gegner
class Enemy( Ship ):
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_LASER),    
        "blue": (BLUE_SPACE_SHIP, BLUE_LASER),    
        "green": (GREEN_SPACE_SHIP, GREEN_LASER)
    }

    def __init__( self, x, y, color, health = 100 ):
        super().__init__( x, y, health )
        self.ship_image, self.laser_image = self.COLOR_MAP[ color ]
        self.mask = pygame.mask.from_surface( self.ship_image )

    def move( self, vel ):
        self.y += vel

class Laser:
    def __init__( self, x, y, img ):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface( self.img )

    def draw( self, window ):
        window.blit( self.img, (self.x, self.y) )

    def move( self, vel ):
        self.y += vel

    def off_screen( self, height ):
        return not ( self.y <= height and self.y >= 0 )

    def collision( self, obj ):
        return collide( self, obj )


# main
def main():
    run = True
    fps = 60

    level = 0
    lives = 5

    main_font = pygame.font.SysFont( "arial", 50 )
    game_over_font = pygame.font.SysFont( "times new roman", 69 )

    enemy_vel = 1
    enemies = []
    wave_length = 5

    laser_vel = 5

    player_vel = 5
    player = Player( 300, 650 )

    game_over = False
    game_over_count = 0

    joysticks = []
    for i in range( pygame.joystick.get_count() ):
        joysticks.append( pygame.joystick.Joystick( i ) )
        joysticks[ -1 ].init()

    clock = pygame.time.Clock()

    def redraw_window():
        WIN.blit( BG, (0, 0) )
        level_label = main_font.render( f"Level: {level}", 1, (255, 255, 255) )
        lives_label = main_font.render( f"Leben: {lives}", 1, (255, 255, 255) )
        WIN.blit( lives_label, (10, 10) )
        WIN.blit( level_label, (WIDTH - lives_label.get_width() - 10, 10) )
        for enemy in enemies:
            enemy.draw( WIN )
        player.draw( WIN )
        
        if game_over:
            # #4F0001 -> 79,0,1
            game_over_label = game_over_font.render( "YOU DIED", 1, (179, 0, 1) )
            game_over_bg = pygame.Rect( 0,
                                        HEIGHT // 2 - game_over_label.get_height() // 2 - 10,
                                        WIDTH,
                                        game_over_label.get_height() + 20 )
            pygame.draw.rect( WIN, (10, 10, 10), game_over_bg )
            WIN.blit( game_over_label, (WIDTH // 2 - game_over_label.get_width() // 2, 
                                        HEIGHT // 2 - game_over_label.get_height() // 2) )

        pygame.display.update()


    while run:
        clock.tick( fps )
        redraw_window()

        if lives <= 0 or player.health <= 0:
            game_over = True
            game_over_count += 1
            GAME_OVER_SOUND.play()

        if game_over:
            if game_over_count > fps * 5:
                run = False
            else:
                continue

        if len( enemies ) == 0:
            level += 1
            wave_length += 5
            for i in range( wave_length ):
                enemy = Enemy( random.randrange( 50, WIDTH - 100 ), 
                               random.randrange( -1500, -100 ),
                               random.choice( [ "red", "blue", "green" ] ) )
                enemies.append( enemy )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        keys = pygame.key.get_pressed()
        if keys[ pygame.K_LEFT ] and player.x - player_vel > 0:
            player.x -= player_vel
        if keys[ pygame.K_RIGHT ] and player.x + player.get_width() + player_vel < WIDTH:
            player.x += player_vel
        if keys[ pygame.K_UP ] and player.y - player_vel > 0:
            player.y -= player_vel
        if keys[ pygame.K_DOWN ] and player.y + player.get_height() + player_vel < HEIGHT:
            player.y += player_vel
        if keys[ pygame.K_SPACE ]:
            player.shoot()

        for enemy in enemies:
            enemy.move( enemy_vel )
            enemy.move_lasers( laser_vel, player )

            if random.randrange( 0, fps * 2 ) == 1:
                enemy.shoot()

            if collide( enemy, player ):
                player.health -= 10
                LASER_HIT_SOUND.play()
                enemies.remove( enemy )
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove( enemy )

        player.move_lasers( -laser_vel, enemies )


# Hauptmenü
def main_menu():
    main_font = pygame.font.SysFont( "arial", 50 )
    run = True
    while run:
        WIN.blit( BG, (0, 0) )
        title_label = main_font.render( "Start drücken...", 1, (255, 255, 255) )
        WIN.blit( title_label, (WIDTH // 2 - title_label.get_width() // 2, 
                               HEIGHT // 2 - title_label.get_height() // 2) )
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()
    pygame.quit()


# Kollisionsabfrage
def collide( obj1, obj2 ):
    offset_x = obj2.x - obj1.x 
    offset_y = obj2.y - obj1.y   
    return obj1.mask.overlap( obj2.mask, (offset_x, offset_y) ) != None

# MAIN
main_menu()
