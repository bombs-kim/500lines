from OpenGL.GL import (
    glBegin,
    glColor3f,
    glEnd,
    glEndList,
    glLineWidth,
    glNewList,
    glNormal3f,
    glVertex3f,
    GL_COMPILE,
    GL_LINES,
    GL_QUADS,
)
from OpenGL.GLU import gluDeleteQuadric, gluNewQuadric, gluSphere

G_OBJ_PLANE = 1
G_OBJ_BOARD = 2
G_OBJ_SPHERE = 3
G_OBJ_CUBE = 4


def make_plane():
    glNewList(G_OBJ_PLANE, GL_COMPILE)
    glBegin(GL_LINES)
    glColor3f(0, 0, 0)
    for i in range(41):
        glVertex3f(-10.0 + 0.5 * i, 0, -10)
        glVertex3f(-10.0 + 0.5 * i, 0, 10)
        glVertex3f(-10.0, 0, -10 + 0.5 * i)
        glVertex3f(10.0, 0, -10 + 0.5 * i)

    # Axes
    glEnd()
    glLineWidth(5)

    glBegin(GL_LINES)
    glColor3f(0.5, 0.7, 0.5)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(5, 0.0, 0.0)
    glEnd()

    glBegin(GL_LINES)
    glColor3f(0.5, 0.7, 0.5)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 5, 0.0)
    glEnd()

    glBegin(GL_LINES)
    glColor3f(0.5, 0.7, 0.5)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 0.0, 5)
    glEnd()

    # Draw the Y.
    glBegin(GL_LINES)
    glColor3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 5.0, 0.0)
    glVertex3f(0.0, 5.5, 0.0)
    glVertex3f(0.0, 5.5, 0.0)
    glVertex3f(-0.5, 6.0, 0.0)
    glVertex3f(0.0, 5.5, 0.0)
    glVertex3f(0.5, 6.0, 0.0)

    # Draw the Z.
    glVertex3f(-0.5, 0.0, 5.0)
    glVertex3f(0.5, 0.0, 5.0)
    glVertex3f(0.5, 0.0, 5.0)
    glVertex3f(-0.5, 0.0, 6.0)
    glVertex3f(-0.5, 0.0, 6.0)
    glVertex3f(0.5, 0.0, 6.0)

    # Draw the X.
    glVertex3f(5.0, 0.0, 0.5)
    glVertex3f(6.0, 0.0, -0.5)
    glVertex3f(5.0, 0.0, -0.5)
    glVertex3f(6.0, 0.0, 0.5)

    glEnd()
    glLineWidth(1)
    glEndList()


def make_board():
    glNewList(G_OBJ_BOARD, GL_COMPILE)

    cell_size = 0.5
    board_size = 20
    offset = -(cell_size * board_size / 2)

    magenta = (1.0, 0.0, 1.0)  # Magenta color
    cyan = (0.0, 1.0, 1.0)  # Cyan color

    for i in range(board_size):
        for j in range(board_size):
            # Alternate colors
            if (i + j) % 2 == 0:
                glColor3f(*magenta)
            else:
                glColor3f(*cyan)

            # Draw the filled quad for each cell
            glBegin(GL_QUADS)
            glVertex3f(offset + cell_size * (i + 0), 0, offset + cell_size * (j + 1))
            glVertex3f(offset + cell_size * (i + 1), 0, offset + cell_size * (j + 1))
            glVertex3f(offset + cell_size * (i + 1), 0, offset + cell_size * (j + 0))
            glVertex3f(offset + cell_size * (i + 0), 0, offset + cell_size * (j + 0))
            glEnd()

    glEndList()


def make_sphere():
    glNewList(G_OBJ_SPHERE, GL_COMPILE)
    quad = gluNewQuadric()
    gluSphere(quad, 0.5, 30, 30)
    gluDeleteQuadric(quad)
    glEndList()


def make_cube():
    glNewList(G_OBJ_CUBE, GL_COMPILE)
    vertices = [
        ((-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, 0.5, -0.5)),
        ((-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5)),
        ((0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.5, -0.5, 0.5)),
        ((-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)),
        ((-0.5, -0.5, 0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5)),
        ((-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5)),
    ]
    normals = [
        (-1.0, 0.0, 0.0),
        (0.0, 0.0, -1.0),
        (1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.0, -1.0, 0.0),
        (0.0, 1.0, 0.0),
    ]

    glBegin(GL_QUADS)
    for i in range(6):
        glNormal3f(normals[i][0], normals[i][1], normals[i][2])
        for j in range(4):
            glVertex3f(vertices[i][j][0], vertices[i][j][1], vertices[i][j][2])
    glEnd()
    glEndList()


def init_primitives():
    make_plane()
    make_board()
    make_sphere()
    make_cube()
