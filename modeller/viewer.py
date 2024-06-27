import math
from typing import Literal

import numpy
from interaction import Interaction
from node import Board
from numpy.linalg import inv, norm
from OpenGL.constants import GLfloat_3, GLfloat_4
from OpenGL.GL import (
    GL_AMBIENT_AND_DIFFUSE,
    GL_BACK,
    GL_COLOR_BUFFER_BIT,
    GL_COLOR_MATERIAL,
    GL_CULL_FACE,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FRONT_AND_BACK,
    GL_LESS,
    GL_LIGHT0,
    GL_LIGHTING,
    GL_MODELVIEW,
    GL_MODELVIEW_MATRIX,
    GL_POSITION,
    GL_PROJECTION,
    GL_SPOT_DIRECTION,
    glCallList,
    glClear,
    glClearColor,
    glColorMaterial,
    glCullFace,
    glDepthFunc,
    glDisable,
    glEnable,
    glFlush,
    glGetFloatv,
    glLightfv,
    glLoadIdentity,
    glMatrixMode,
    glMultMatrixf,
    glPopMatrix,
    glPushMatrix,
    glTranslated,
    glViewport,
)
from OpenGL.GLU import gluPerspective, gluUnProject
from OpenGL.GLUT import (
    GLUT_RGB,
    GLUT_SINGLE,
    GLUT_WINDOW_HEIGHT,
    GLUT_WINDOW_WIDTH,
    glutCreateWindow,
    glutDisplayFunc,
    glutGet,
    glutInit,
    glutInitDisplayMode,
    glutInitWindowSize,
    glutMainLoop,
    glutPostRedisplay,
    glutTimerFunc,
)
from primitive import G_OBJ_PLANE, init_primitives
from scene import Scene


class Viewer:
    def __init__(self):
        """Initialize the viewer."""
        self.init_interface()
        self.init_opengl()
        self.init_scene()
        self.init_interaction()
        init_primitives()

        self.target_translation = None
        self.animation_step = 0.1  # control the speed of the animation

    def init_interface(self):
        """initialize the window and register the render function"""
        glutInit()
        glutInitWindowSize(640, 480)
        glutCreateWindow("3D Modeller")
        glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
        glutDisplayFunc(self.render)

    def init_opengl(self):
        """initialize the opengl settings to render the scene"""
        self.inverse_model_view = numpy.identity(4)
        self.model_view = numpy.identity(4)

        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, GLfloat_4(0, 0, 1, 0))
        glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, GLfloat_3(0, 0, -1))

        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        glClearColor(0.4, 0.4, 0.4, 0.0)

    def init_scene(self):
        """initialize the scene object and initial scene"""
        self.scene = Scene()
        self.create_sample_scene()

    def create_sample_scene(self):
        board = Board()
        self.board = board
        self.scene.add_node(board)

    def init_interaction(self):
        """init user interaction and callbacks"""
        self.interaction = Interaction()
        self.interaction.register_callback("pick", self.pick)
        self.interaction.register_callback("move", self.move)
        self.interaction.register_callback("place", self.place)
        self.interaction.register_callback("move_board", self.move_board)
        self.interaction.register_callback("rotate_board", self.rotate_board)

    def main_loop(self):
        glutMainLoop()

    def render(self):
        """The render pass for the scene"""
        self.init_view()

        glEnable(GL_LIGHTING)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Load the modelview matrix from the current state of the trackball
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        loc = self.interaction.translation
        glTranslated(loc[0], loc[1], loc[2])
        glMultMatrixf(self.interaction.trackball.matrix)

        # store the inverse of the current modelview.
        current_model_view = numpy.array(glGetFloatv(GL_MODELVIEW_MATRIX))
        self.model_view = numpy.transpose(current_model_view)
        self.inverse_model_view = inv(numpy.transpose(current_model_view))

        # render the scene. This will call the render function for each object in the scene
        self.scene.render()

        # draw the grid
        glDisable(GL_LIGHTING)
        glCallList(G_OBJ_PLANE)
        glPopMatrix()

        # flush the buffers so that the scene can be drawn
        glFlush()

    def init_view(self):
        """initialize the projection matrix"""
        x_size, y_size = glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT)
        aspect_ratio = float(x_size) / float(y_size)

        # load the projection matrix. Always the same
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glViewport(0, 0, x_size, y_size)
        gluPerspective(70, aspect_ratio, 0.1, 1000.0)
        glTranslated(0, 0, -15)

    def get_ray(self, x, y):
        """Generate a ray beginning at the near plane, in the direction that the x, y coordinates are facing
        Consumes: x, y coordinates of mouse on screen
        Return: start, direction of the ray"""
        self.init_view()

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # get two points on the line.
        start = numpy.array(gluUnProject(x, y, 0.001))
        end = numpy.array(gluUnProject(x, y, 0.999))

        # convert those points into a ray
        direction = end - start
        direction = direction / norm(direction)

        return (start, direction)

    def pick(self, x, y):
        """Execute pick of an object. Selects an object in the scene."""
        start, direction = self.get_ray(x, y)
        self.scene.pick(start, direction, self.model_view)

    def place(self, shape, x, y):
        """Execute a placement of a new primitive into the scene."""
        start, direction = self.get_ray(x, y)
        self.scene.place(shape, start, direction, self.inverse_model_view)

    def move(self, x, y):
        """Execute a move command on the scene."""
        start, direction = self.get_ray(x, y)
        self.scene.move_selected(start, direction, self.inverse_model_view)

    def move_board_step(self):
        """Incrementally move the board to the target position."""
        if self.target_translation is None:
            return

        delta = self.target_translation - self.current_translation

        # Check if the translation is close enough to the target to stop the animation
        if abs(delta) <= self.animation_step:
            self.board.translate(0, 0, delta)
            self.target_translation = None
            self.current_translation = None
            print("Animation complete")
        else:
            # Move a small step towards the target
            step = self.animation_step if delta > 0 else -self.animation_step
            self.board.translate(0, 0, step)
            self.current_translation += step

        # Request a redraw
        glutPostRedisplay()

        # Continue the animation
        if self.target_translation is not None:
            glutTimerFunc(16, lambda x: self.move_board_step(), 0)

    def move_board(self, z: Literal[-1, 1]):
        if self.target_translation is None:
            self.target_translation = z
            self.current_translation = 0.0
            self.move_board_step()
        else:
            self.target_translation += z

    def rotate_board(self, direction: Literal["left", "right"]):
        angle = 1 / 2 * math.pi if direction == "right" else -(1 / 2 * math.pi)
        self.board.rotate_y(angle)

    def rotate_color(self, forward):
        """Rotate the color of the selected Node. Boolean 'forward' indicates direction of rotation."""
        self.scene.rotate_selected_color(forward)

    def scale(self, up):
        """Scale the selected Node. Boolean up indicates scaling larger."""
        self.scene.scale_selected(up)


if __name__ == "__main__":
    viewer = Viewer()
    viewer.main_loop()
