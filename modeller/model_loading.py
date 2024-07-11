# GitHub - PyGameExamplesAndAnswers - PyGame and OpenGL immediate mode (Legacy OpenGL) - Primitive and Mesh
# https://github.com/Rabbid76/PyGameExamplesAndAnswers/blob/master/documentation/pygame_opengl/immediate_mode/pygame_opengl_immediate_mode.md
#
# GL_LINES not showing up on top of cube?
# https://stackoverflow.com/questions/56624147/gl-lines-not-showing-up-on-top-of-cube/56624975#56624975

import pygame
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_FILL,
    GL_FRONT_AND_BACK,
    GL_LINE,
    GL_MODELVIEW,
    GL_PROJECTION,
    glClear,
    glMatrixMode,
    glPolygonMode,
    glPopMatrix,
    glPushMatrix,
    glRotate,
    glScale,
    glTranslate,
    glTranslatef,
)
from OpenGL.GLU import gluPerspective

from objloader import WavefrontObj

pygame.init()
display = (640, 480)

pygame.display.set_mode(display, pygame.DOUBLEBUF | pygame.OPENGL)
clock = pygame.time.Clock()

model = WavefrontObj("models/cheburashka.obj")
model.compile()
box = model.box()
center = [(box[0][i] + box[1][i]) / 2 for i in range(3)]
size = [box[1][i] - box[0][i] for i in range(3)]
max_size = max(size)
distance = 10
scale = distance / max_size
angle = 0

glMatrixMode(GL_PROJECTION)
gluPerspective(90, (display[0] / display[1]), 0.1, distance * 2)

glMatrixMode(GL_MODELVIEW)
glTranslatef(0.0, 0, -distance)

run = True
while run:
    clock.tick(100)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glPushMatrix()
    glRotate(angle, 0, 1, 0)
    glScale(scale, scale, scale)
    glTranslate(-center[0], -center[1], -center[2])
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    model.render()

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    model.render()
    glPopMatrix()
    angle += 1

    pygame.display.flip()

pygame.quit()
quit()
