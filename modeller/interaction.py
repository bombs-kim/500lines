from collections import defaultdict
import os
from OpenGL.GLUT import (
    glutGet,
    glutKeyboardFunc,
    glutMotionFunc,
    glutMouseFunc,
    glutPostRedisplay,
    glutSpecialFunc,
)
from OpenGL.GLUT import (
    GLUT_LEFT_BUTTON,
    GLUT_RIGHT_BUTTON,
    GLUT_WINDOW_HEIGHT,
    GLUT_WINDOW_WIDTH,
    GLUT_DOWN,
    GLUT_KEY_UP,
    GLUT_KEY_DOWN,
    GLUT_KEY_LEFT,
    GLUT_KEY_RIGHT,
)
import trackball


class Interaction:
    def __init__(self):
        """Handles user interaction"""
        # currently pressed mouse button
        self.pressed = None
        # the current location of the camera
        self.translation = [0, 0, 0, 0]
        # the trackball to calculate rotation
        self.trackball = trackball.Trackball(theta=-25, distance=15)
        # the current mouse location
        self.mouse_loc = None
        # Unsophisticated callback mechanism
        self.callbacks = defaultdict(list)

        self.register()

    def register(self):
        """register callbacks with glut"""
        glutMouseFunc(self.handle_mouse_button)
        glutMotionFunc(self.handle_mouse_move)
        glutKeyboardFunc(self.handle_keystroke)
        glutSpecialFunc(self.handle_keystroke)

    def register_callback(self, name, func):
        """registers a callback for a certain event"""
        self.callbacks[name].append(func)

    def trigger(self, name, *args, **kwargs):
        """calls a callback, forwards the args"""
        for func in self.callbacks[name]:
            func(*args, **kwargs)

    def translate(self, x, y, z):
        """translate the camera"""
        self.translation[0] += x
        self.translation[1] += y
        self.translation[2] += z

    def handle_mouse_button(self, button, mode, x, y):
        """Called when the mouse button is pressed or released"""
        _, y_size = glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT)
        y = y_size - y  # invert the y coordinate because OpenGL is inverted
        self.mouse_loc = (x, y)

        if mode == GLUT_DOWN:
            self.pressed = button
            if button == GLUT_RIGHT_BUTTON:
                pass
            elif button == GLUT_LEFT_BUTTON:  # pick
                self.trigger("pick", x, y)
        else:  # mouse button release
            self.pressed = None
        glutPostRedisplay()

    def handle_mouse_move(self, x, screen_y):
        """Called when the mouse is moved"""
        _, y_size = glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT)
        y = y_size - screen_y  # invert the y coordinate because OpenGL is inverted
        if self.pressed is not None:
            dx = x - self.mouse_loc[0]
            dy = y - self.mouse_loc[1]
            if self.pressed == GLUT_RIGHT_BUTTON and self.trackball is not None:
                # ignore the updated camera loc because we want to always rotate around the origin
                self.trackball.drag_to(self.mouse_loc[0], self.mouse_loc[1], dx, dy)
            elif self.pressed == GLUT_LEFT_BUTTON:
                self.trigger("move", x, y)
            else:
                pass
            glutPostRedisplay()
        self.mouse_loc = (x, y)

    def handle_keystroke(self, key, x, screen_y):
        """Called on keyboard input from the user"""
        _, y_size = glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT)
        y = y_size - screen_y

        if key == b"s":
            self.trigger("place", "sphere", x, y)
        elif key == b"c":
            self.trigger("place", "cube", x, y)
        elif key == b"f":
            self.trigger("place", "figure", x, y)
        elif key == b"[":
            self.translate(0, 0, 1.0)
        elif key == b"]":
            self.translate(0, 0, -1.0)
        elif key == GLUT_KEY_UP:
            self.trigger("move_board", z=+1)
        elif key == GLUT_KEY_DOWN:
            self.trigger("move_board", z=-1)
        elif key == GLUT_KEY_LEFT:
            self.trigger("rotate_board", direction="left")
        elif key == GLUT_KEY_RIGHT:
            self.trigger("rotate_board", direction="right")
        elif key == b"q":
            os._exit(0)
        glutPostRedisplay()
