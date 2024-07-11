import math
from typing import Literal

import numpy
from interaction import Interaction
from node import Board, SnowFigure
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
from primitive import G_OBJ_DIRECTION, compile_primitives
from scene import Scene


ANIMATION_DELAY = 10


class Viewer:
    def __init__(self):
        """Initialize the viewer."""
        self.init_interface()
        self.init_opengl()
        self.init_scene()
        self.init_interaction()
        compile_primitives()

        self.target_translation = None
        self.target_rotation = None
        self.animation_step_ratio = 0.05

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
        board = Board.from_map()
        self.board = board
        self.scene.add_node(board)
        snow_figure = SnowFigure()
        self.scene.add_node(snow_figure)

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
        # glCallList(G_OBJ_PLANE)
        glCallList(G_OBJ_DIRECTION)
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
        step = self.target_translation * self.animation_step_ratio

        # Check if the translation is close enough to the target to stop the animation
        if sum(abs(delta)) <= sum(abs(step)):
            self.board.translate_and_adjust_center(delta)
            self.target_translation = None
            self.current_translation = None
        else:
            # Move a small step towards the target
            self.board.translate_and_adjust_center(step)
            self.current_translation += step

        # Request a redraw
        glutPostRedisplay()

        # Continue the animation
        if self.target_translation is not None:
            glutTimerFunc(ANIMATION_DELAY, lambda x: self.move_board_step(), 0)

    def move_board(self, direction: Literal["forward", "backward"]):
        translation_vec = (
            self.board.get_forward_direction()
            if direction == "forward"
            else -self.board.get_forward_direction()
        )
        if self.target_translation is None:
            self.target_translation = translation_vec
            self.current_translation = numpy.array([0.0, 0.0, 0.0])
            self.move_board_step()

    def rotate_board_step(self):
        """Incrementally rotate the board to the target angle."""
        if self.target_rotation is None:
            return

        delta = self.target_rotation - self.current_rotation
        step = self.target_rotation * self.animation_step_ratio

        # Check if the rotation is close enough to the target to stop the animation
        if abs(delta) <= abs(step):
            self.board.rotate_y(delta)
            self.target_rotation = None
            self.current_rotation = None
        else:
            # Rotate a small step towards the target
            self.board.rotate_y(step)
            self.current_rotation += step

        # Request a redraw
        glutPostRedisplay()

        # Continue the animation
        if self.target_rotation is not None:
            glutTimerFunc(ANIMATION_DELAY, lambda x: self.rotate_board_step(), 0)

    def rotate_board(self, direction: Literal["left", "right"]):
        if self.target_rotation is None:
            self.target_rotation = math.pi / 2 if direction == "right" else -math.pi / 2
            self.current_rotation = 0.0
            self.board.turn_forward_direction(direction)
            self.rotate_board_step()

    def rotate_color(self, forward):
        """Rotate the color of the selected Node. Boolean 'forward' indicates direction of rotation."""
        self.scene.rotate_selected_color(forward)

    def scale(self, up):
        """Scale the selected Node. Boolean up indicates scaling larger."""
        self.scene.scale_selected(up)


if __name__ == "__main__":
    viewer = Viewer()
    viewer.main_loop()
