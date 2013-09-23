import math, os, pygame, random, time
import cProfile
from pygame.locals import *

#-------------------------------------------------------------------------------
# Globals, Groups, Constants
#-------------------------------------------------------------------------------

screen_size = screen_width,screen_height = 800,800
field = pygame.rect.Rect(0,0,screen_width,screen_height)

sprites = pygame.sprite.RenderUpdates()    

players = pygame.sprite.Group()
player_missles = pygame.sprite.Group()

enemies = pygame.sprite.Group()
enemy_missles = pygame.sprite.Group()

image_cache = {}

#-------------------------------------------------------------------------------
# Utility Functions
#-------------------------------------------------------------------------------

def load_image(name):

    if name not in image_cache:

        print "Loading image:", name
        fullname = os.path.join('data', name)

        try:
            image = pygame.image.load(fullname)
        except pygame.error, message:
            print 'Cannot load image:', fullname
            raise SystemExit, message

        image = image.convert()
        colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
        image_cache[name] = image
        
    else:
        image = image_cache[name]

    return image, image.get_rect()

#-------------------------------------------------------------------------------
# Cursor Sprite
#-------------------------------------------------------------------------------

class Cursor(pygame.sprite.Sprite):
    def __init__(self, image):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image(image)        
        sprites.add(self)

    def update(self):
        self.rect.center = pygame.mouse.get_pos()

#-------------------------------------------------------------------------------
# Player Sprite
#-------------------------------------------------------------------------------

class Player(pygame.sprite.Sprite):

    def __init__(self, image):
        pygame.sprite.Sprite.__init__(self)
        sprites.add(self)
        players.add(self)
        
        self.origonal, self.rect = load_image(image)
        self.rect.center = (screen_width/2, screen_height/2)

        self.t = [0,0]
        self.v = 3

        # this holds the mouse pointer pos
        # where the player is "looking"
        self.vec = [0,0]

        self.firing = False
        self.reload = 10

        self.invincible = True
        self.age = 0
        
    def move(self, imp):
        self.t[0] += imp[0]
        self.t[1] += imp[1]

    def stop(self, imp):
        self.t[0] *= imp[0]
        self.t[1] *= imp[1]

    def spin(self, vec):
        self.vec = vec        

    def fire(self):
        self.firing = True

    def cease_fire(self):
        self.firing = False
        
    def update(self):

        self.age += 1
        if self.age ==  100:
            self.invincible = False

        # rotate
        center = self.rect.center
        vx = self.vec[0] - center[0]
        vy = self.vec[1] - center[1]
        ang = -math.degrees(math.atan2(vy, vx))

        self.image = pygame.transform.rotate(self.origonal, ang)
        self.rect = self.image.get_rect(center=center)

        # translate
        x = self.rect.centerx + (self.v*self.t[0])
        y = self.rect.centery + (self.v*self.t[1])
        
        if x > 0 and x < screen_width:
            self.rect.centerx = x
            
        if y > 0 and y < screen_height:
            self.rect.centery = y

        # fire!
        if self.firing and self.reload > 5:
            self.reload = 0
            m = Missle('bullet.png', self.rect.center, self.vec, 2)
            player_missles.add(m)
        
        self.reload += 1
            

#-------------------------------------------------------------------------------
# Enemy Sprites
#-------------------------------------------------------------------------------

# Drones
#  drones wander around and fire off at players

class Drone(pygame.sprite.Sprite):
    def __init__(self, image):
        pygame.sprite.Sprite.__init__(self)
        sprites.add(self)
        self.image, self.rect = load_image(image)

        self.rect.center = (0,0)
        self.v = random.randint(1, 3)
        self.mode = self.run
        enemies.add(self)

    def run(self):
        self.target = (random.randint(0, screen_width),
                       random.randint(0, screen_height))
        self.v = random.randint(2, 3)
        self.mode = self.running
        
    def running(self):

        dx = self.target[0] - self.rect.centerx        
        dy = self.target[1] - self.rect.centery
        ang = math.atan2(dy, dx)
        
        a = round(self.v*math.cos(ang))
        b = round(self.v*math.sin(ang))

        if abs(dx) > self.v or abs(b) > self.v:
            self.rect.move_ip(a,b)
        else:
            self.mode = self.fire
            
    def fire(self):
        target = random.choice(players.sprites()).rect.center
        enemy_missles.add(Missle('enemy_bullet.png', self.rect.center,
                                 target, 2))
        self.mode = self.run

    def update(self):
        self.mode()

# Bouncers
#  bounce off the walls, nothing exciting

class Bouncer(pygame.sprite.Sprite):
    def __init__(self, image):
        pygame.sprite.Sprite.__init__(self)
        sprites.add(self)
        self.image, self.rect = load_image(image)
        self.vec = [random.randint(1,3), random.randint(1,3)]
        self.rect.center = [0,0]
        self.v = random.randint(1, 2)
        enemies.add(self)

    def update(self):
        dx = round(self.v*self.vec[0])
        dy = round(self.v*self.vec[1])

        if self.rect.centerx + dx < 0 or self.rect.centerx + dx > screen_width:
            dx = -dx
            self.vec[0] = -self.vec[0]
            
        if self.rect.centery + dy < 0 or self.rect.centery + dy > screen_height:
            dy = -dy
            self.vec[1] = -self.vec[1]

        self.rect.move_ip(dx, dy)

#-------------------------------------------------------------------------------
# Missle Sprite
#-------------------------------------------------------------------------------
                
class Missle(pygame.sprite.Sprite):

    def __init__(self, image, pos, target, v):
        pygame.sprite.Sprite.__init__(self)
        sprites.add(self)
        
        self.target = target
        
        dx = target[0] - pos[0]
        dy = target[1] - pos[1]
        ang = math.atan2(dy, dx)
        a = v*math.cos(ang)
        b = v*math.sin(ang)
        self.vec = (v*a, v*b)
        origonal, self.rect = load_image(image)
        center = self.rect.center
        self.image = pygame.transform.rotate(origonal, ang)
        self.rect = self.image.get_rect(center=center)        
        self.rect.center = pos
        
    def update(self):
        self.rect.move_ip(*self.vec)

#-------------------------------------------------------------------------------
# Main Routine
#-------------------------------------------------------------------------------

def spawn(min=5, max=20):

    starting_positions = ( (0,0),
                           (screen_width/2, 0),
                           (screen_width, 0),

                           (0, screen_height/2),
                           (screen_width, screen_height/2),

                           (0, screen_height),
                           (screen_width/2, screen_height),
                           (screen_width, screen_height) )

    count = {}
    enemy_classes = [ ('Drone', Drone), ('Bouncer', Bouncer) ]
    num = random.randint(min, max)
    pos = random.choice(starting_positions)
    
    for i in xrange(num):

        e = random.choice(enemy_classes)
        if e[0] not in count:
            count[e[0]] = 0

        count[e[0]] += 1
        e[1]('enemy.png').rect.center = pos

    print "Spawned", num, "enemies:"
    for k,v in count.items():
        print k, ':', v
        
def main():

    pygame.init()
    screen = pygame.display.set_mode(screen_size)

    pygame.display.set_caption('Crash')
    pygame.mouse.set_visible(0)

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    font = pygame.font.Font(None, 28)

    Cursor('cursor.png')

    clock = pygame.time.Clock()

    player = None
    lives = 0
    kills = 0
    waves = 0
    
    running = True
    while running:
        clock.tick(60)

        if len(players) == 0:
            player = Player('player.png')
            players.add(player)
            lives += 1

        if len(enemies) == 0:
            spawn()
            waves += 1

        for event in pygame.event.get():
            
            if event.type == QUIT:
                return
            
            elif event.type == KEYDOWN:
            
                if event.key == K_ESCAPE:
                    running = False
                    continue

                elif event.key == K_LEFT:
                    player.move((-1, 0))

                elif event.key == K_RIGHT:
                    player.move((1, 0))

                elif event.key == K_UP:
                    player.move((0, -1))

                elif event.key == K_DOWN:
                    player.move((0, 1))

            elif event.type == KEYUP:
                if event.key == K_LEFT:
                    player.stop((0, 1))

                elif event.key == K_RIGHT:
                    player.stop((0, 1))

                elif event.key == K_UP:
                    player.stop((1, 0))

                elif event.key == K_DOWN:
                    player.stop((1, 0))
                    
            elif event.type == MOUSEMOTION:
                player.spin(event.pos)

            elif event.type == MOUSEBUTTONDOWN:
                player.fire()

            elif event.type == MOUSEBUTTONUP:
                player.cease_fire()

        sprites.update()

        for d in pygame.sprite.groupcollide(enemies, player_missles,
                                            True, True).keys():
            kills += 1

        for s in player_missles.sprites() + enemy_missles.sprites():
            if not field.contains(s.rect):
                s.kill()

        if not player.invincible:
            if pygame.sprite.spritecollideany(player, enemy_missles) or \
                   pygame.sprite.spritecollideany(player, enemies):
                player.kill()

        text = font.render("Kills: %d / Lives: %d / Waves: %d" % (kills,
                        lives, waves), 1, (255, 255, 255), (0,0,0))
        textpos = text.get_rect(centerx=background.get_width()/2)

        screen.blit(text, textpos)

        sprites.clear(screen, background)
        deltas = sprites.draw(screen)
        pygame.display.update(deltas + [textpos])

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
