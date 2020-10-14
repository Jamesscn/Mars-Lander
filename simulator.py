import pygame, math, os
import externalCode

#Parameters for the simulator

#Set this to map_a1.txt for the Mars Lander 1 map
#Set this to map_b1.txt, map_b2.txt ... map_b5.txt for the Mars Lander 2 maps
#Set this to map_c1.txt or map_c2.txt for the Mars Lander 3 maps
#You can create your own maps, just make the initial inputs and place them in a .txt file in the maps folder
mapName = "map_c1.txt"

#Set this to true if you would like to see the game as it plays
#This will negatively impact the run performance, so set this to false if you are planning on training a neural network
showGame = True

#The simulator exits with code -2 if the ship left the boundaries of the game.
#The simulator exits with code -1 if the ship crashed against the surface.
#The simulator exits with a code >= 0 if it landed successfully. The code is the amount of remaining fuel the ship landed with.

#Simulator code

EPS = 0.000000001

def CCW(a, b, c):
    ba = [b[0] - a[0], b[1] - a[1]]
    bc = [b[0] - c[0], b[1] - c[1]]
    return ba[0] * bc[1] - ba[1] * bc[0] > -EPS

def Angle(a, b, c):
    ba = [b[0] - a[0], b[1] - a[1]]
    bc = [b[0] - c[0], b[1] - c[1]]
    dotProduct = ba[0] * bc[0] + ba[1] * bc[1]
    baMagnitude = math.sqrt(ba[0] * ba[0] + ba[1] * ba[1])
    bcMagnitude = math.sqrt(bc[0] * bc[0] + bc[1] * bc[1])
    return math.acos(dotProduct / (baMagnitude * bcMagnitude))

class Lander:
    def __init__(self, inputs):
        self.x, self.y, self.vx, self.vy, self.fuel, self.rotation, self.power = inputs
        self.turn = 1

    def collisionCheck(self, gameWidth, ground):
        collisionPoly = [[0, 0]]
        for point in ground:
            collisionPoly.append(point)
        collisionPoly.append([gameWidth, 0])
        angleSum = 0
        for i in range(len(collisionPoly)):
            pointA = collisionPoly[i]
            pointB = [self.x, self.y]
            pointC = collisionPoly[(i + 1) % len(collisionPoly)]
            if CCW(pointA, pointB, pointC):
                angleSum += Angle(pointA, pointB, pointC)
            else:
                angleSum -= Angle(pointA, pointB, pointC)
        return abs(abs(angleSum) - 2 * math.pi) < EPS

    def simulateTurn(self, rotation, power, gameWidth, gameHeight, ground, flatSpots):
        self.rotation = max(min(max(self.rotation - 15, min(self.rotation + 15, rotation)), 90), -90)
        self.power = max(self.power - 1, min(self.power + 1, power))
        if self.fuel <= 0:
            self.fuel = 0
            self.power = 0
        self.fuel -= self.power
        self.ax = self.power * math.cos(math.radians(self.rotation + 90))
        self.ay = self.power * math.sin(math.radians(self.rotation + 90)) - 3.711
        self.x += self.vx + self.ax / 2
        self.y += self.vy + self.ay / 2
        self.vx += self.ax
        self.vy += self.ay
        self.turn += 1
        if self.x < 0 or self.x > gameWidth or self.y < 0 or self.y > gameHeight:
            return -2
        if self.collisionCheck(gameWidth, ground):
            if self.rotation == 0 and abs(self.vy) <= 40 and abs(self.vx) <= 20:
                for spot in flatSpots:
                    if spot[0] <= self.x <= spot[1] and abs(self.y - spot[2]) < 100:
                        return 1
            return -1
        return 0

mapFile = open("./maps/" + mapName, "r")
ground = []
flatSpots = []
surfacePoints = int(mapFile.readline().rstrip())
lastX = -1
lastY = -1
for point in range(surfacePoints):
    x, y = [*map(int, mapFile.readline().rstrip().split())]
    if lastY == y:
        flatSpots.append([min(lastX, x), max(lastX, x), y])
    ground.append([x, y])
    lastX = x
    lastY = y
lander = Lander([*map(int, mapFile.readline().rstrip().split())])
mapFile.close()
externalProgram = externalCode.Program(ground)
gameWidth = 7000
gameHeight = 3000

if showGame:
    compressFactor = 10
    width = gameWidth // compressFactor
    height = gameHeight // compressFactor
    speed = 5
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    pygame.init()
    screen = pygame.display.set_mode([width, height])
    clock = pygame.time.Clock()
    landerImage = pygame.image.load("./lander.png")
running = True
state = 0
while running:
    if showGame:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        clock.tick(speed)

        screen.fill([0, 0, 0])
        for i in range(len(ground) - 1):
            start = [j // compressFactor for j in ground[i]]
            end = [j // compressFactor for j in ground[i + 1]]
            start[1] = height - start[1]
            end[1] = height - end[1]
            pygame.draw.line(screen, [255, 0, 0], start, end)
        
        screen.blit(pygame.transform.rotate(landerImage, lander.rotation), [round(lander.x) // compressFactor, height - round(lander.y) // compressFactor - 14])

    programAngle, programPower = externalProgram.runTurn(list(map(round, [lander.x, lander.y, lander.vx, lander.vy, lander.fuel, lander.rotation, lander.power])))
    state = lander.simulateTurn(programAngle, programPower, gameWidth, gameHeight, ground, flatSpots)
    if state == -2:
        print("Mars Lander has been lost in space!")
        running = False
    if state == -1:
        print("Mars Lander crashed against the surface!")
        running = False
    if state == 1:
        print("Mars Lander has successfully landed with", lander.fuel, "fuel left!")
        state = lander.fuel
        running = False

    if showGame:
        pygame.display.flip()
if showGame:
    pygame.quit()
quit(state)