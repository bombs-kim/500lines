import random
from typing import Literal

import numpy
from OpenGL.GL import (
    GL_EMISSION,
    GL_FRONT,
    glCallList,
    glColor3f,
    glMaterialfv,
    glMultMatrixf,
    glPopMatrix,
    glPushMatrix,
)

import color
from aabb import AABB
from primitive import G_OBJ_CUBE, G_OBJ_SPHERE, make_quad
from transformation import scaling, translation, rotation_y


class Node:
    """Base class for scene elements"""

    def __init__(self):
        self.color_index = random.randint(color.MIN_COLOR, color.MAX_COLOR)
        self.aabb = AABB([0.0, 0.0, 0.0], [0.5, 0.5, 0.5])
        self.translation_matrix = numpy.identity(4)
        self.scaling_matrix = numpy.identity(4)
        self.selected = False

    def render(self):
        """renders the item to the screen"""
        glPushMatrix()
        glMultMatrixf(numpy.transpose(self.translation_matrix))
        glMultMatrixf(self.scaling_matrix)
        cur_color = color.COLORS[self.color_index]
        glColor3f(cur_color[0], cur_color[1], cur_color[2])
        if self.selected:  # emit light if the node is selected
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.3, 0.3, 0.3])

        self.render_self()
        if self.selected:
            glMaterialfv(GL_FRONT, GL_EMISSION, [0.0, 0.0, 0.0])

        glPopMatrix()

    def render_self(self):
        raise NotImplementedError(
            "The Abstract Node Class doesn't define 'render_self'"
        )

    def translate(self, x, y, z):
        self.translation_matrix = numpy.dot(
            self.translation_matrix, translation([x, y, z])
        )

    def rotate_y(self, angle):
        self.translation_matrix = numpy.dot(rotation_y(angle), self.translation_matrix)

    def rotate_color(self, forwards):
        self.color_index += 1 if forwards else -1
        if self.color_index > color.MAX_COLOR:
            self.color_index = color.MIN_COLOR
        if self.color_index < color.MIN_COLOR:
            self.color_index = color.MAX_COLOR

    def scale(self, up, custom=None):
        s = 1.1 if up else 0.9
        if custom is not None:
            s = custom
        self.scaling_matrix = numpy.dot(self.scaling_matrix, scaling([s, s, s]))

    def pick(self, start, direction, mat):
        """Return whether or not the ray hits the object
        Consume:  start, direction    the ray to check
                  mat                 the modelview matrix to transform the ray by"""

        # transform the modelview matrix by the current translation
        newmat = numpy.dot(
            numpy.dot(mat, self.translation_matrix),
            numpy.linalg.inv(self.scaling_matrix),
        )
        results = self.aabb.ray_hit(start, direction, newmat)
        return results

    def select(self, select=None):
        """Toggles or sets selected state"""
        if select is not None:
            self.selected = select
        else:
            self.selected = not self.selected


class Primitive(Node):
    def __init__(self):
        super().__init__()
        self.call_list = None

    def render_self(self):
        glCallList(self.call_list)


class Sphere(Primitive):
    def __init__(self, custom_scale=None):
        super().__init__()
        self.call_list = G_OBJ_SPHERE
        if custom_scale is not None:
            self.scale(True, custom_scale)


class Cube(Primitive):
    def __init__(self):
        super().__init__()
        self.call_list = G_OBJ_CUBE


class HierarchicalNode(Node):
    def __init__(self):
        super().__init__()
        self.child_nodes = []

    def render_self(self):
        for child in self.child_nodes:
            child.render()


class SnowFigure(HierarchicalNode):
    def __init__(self):
        super().__init__()
        self.child_nodes = [Sphere(), Sphere(), Sphere()]
        self.child_nodes[0].translate(0, -0.6, 0)
        self.child_nodes[1].translate(0, 0.1, 0)
        self.child_nodes[1].scaling_matrix = numpy.dot(
            self.scaling_matrix, scaling([0.8, 0.8, 0.8])
        )
        self.child_nodes[2].translate(0, 0.75, 0)
        self.child_nodes[2].scaling_matrix = numpy.dot(
            self.scaling_matrix, scaling([0.7, 0.7, 0.7])
        )
        for child_node in self.child_nodes:
            child_node.color_index = 10
        self.aabb = AABB([0.0, 0.0, 0.0], [0.5, 1.1, 0.5])


class BoardCell(Node):
    def __init__(
        self,
        board: "Board",
        color: Literal["magenta", "cyan"],
        x_start,
        z_start,
        size,
        sphere: Literal["unmarked", "marked"] | None = None,
    ):
        super().__init__()
        self.board = board
        self.color = (1.0, 0.0, 1.0) if color == "magenta" else (0.0, 1.0, 1.0)
        self.x_start = x = x_start
        self.z_start = z = z_start
        self.size = size
        self.points_base = numpy.array(
            [
                (x + 0 * size, 0.0, z + 1 * size),
                (x + 1 * size, 0.0, z + 1 * size),
                (x + 1 * size, 0.0, z + 0 * size),
                (x + 0 * size, 0.0, z + 0 * size),
            ]
        )
        # Center of mass when projected to the xz plane
        self.center_of_mass = numpy.array([x + size / 2, 0.0, z + size / 2])
        self.sphere = sphere

    @property
    def distance_to_center(self):
        """
        Returns the distance from the center of the board to the center of this cell
        when projected to the xz plane
        """
        return numpy.linalg.norm(self.center_of_mass - self.board.center)

    def render_sphere(self, point):
        sphere = Sphere(custom_scale=0.5)
        if self.sphere == "unmarked":
            color_index = color.MIN_COLOR
        elif self.sphere == "marked":
            color_index = 8
        sphere.color_index = color_index
        sphere_pos = numpy.array(point)
        sphere_pos[1] += 0.15
        sphere.translate(*sphere_pos)
        sphere.render()

    def render_self(self):
        glColor3f(*self.color)

        # copy the base points
        points = numpy.array(self.points_base)

        # Adjust the y coordinate of the points to create a curved surface
        for point in points:
            point_dist_to_center = numpy.linalg.norm(point - self.board.center)
            point[1] = -0.04 * (point_dist_to_center**2)

        if point_dist_to_center <= 0.1 and self.sphere == "unmarked":
            self.sphere = "marked"

        from OpenGL.GL import glEnable, GL_LIGHTING, glDisable

        glDisable(GL_LIGHTING)
        make_quad(*points)
        glEnable(GL_LIGHTING)

        if self.sphere is not None:
            self.render_sphere(points[-1])


class Board(HierarchicalNode):
    def __init__(
        self, board_size: tuple[int, int] = (50, 50), cell_size: float = 1.0, map=None
    ):
        super().__init__()
        self.dir_idx = 0
        self.board_size = board_size
        self.center = numpy.array([0.0, 0.0, 0.0])

        for i in range(board_size[0]):
            for j in range(board_size[1]):
                color = "magenta" if (i + j) % 2 == 0 else "cyan"
                x_start = (-(cell_size * board_size[0]) / 2) + i * cell_size
                z_start = (-(cell_size * board_size[1]) / 2) + j * cell_size

                if map and i > 1 and j > 1 and map[j - 1][i - 1] != 0:
                    sphere = "unmarked"
                else:
                    sphere = None

                cell = BoardCell(
                    self, color, x_start, z_start, cell_size, sphere=sphere
                )
                self.child_nodes.append(cell)

    def render_self(self):
        for child in self.child_nodes:
            child: BoardCell
            if child.distance_to_center < 8.0:
                child.render()

    def translate_and_adjust_center(self, translation_vec):
        self.translate(*translation_vec)
        self.center -= translation_vec

    def turn_forward_direction(self, to: Literal["left", "right"]):
        if to == "left":
            self.dir_idx = (self.dir_idx + 1) % 4
        else:
            self.dir_idx = (self.dir_idx - 1) % 4

    def get_forward_direction(self):
        return {
            0: numpy.array([0.0, 0.0, 1.0]),
            1: numpy.array([1.0, 0.0, 0.0]),
            2: numpy.array([0.0, 0.0, -1.0]),
            3: numpy.array([-1.0, 0.0, 0.0]),
        }[self.dir_idx]

    def get_backward_direction(self):
        return self.get_forward_direction() * (-1)

    @classmethod
    def from_map(cls):
        from board_config import map

        map = [[int(c) for c in line] for line in map.split("\n")]
        width, height = len(map[0]), len(map)

        assert width % 2 == 1 and height % 2 == 1

        for line in map:
            assert len(line) == width

        # The map is for denoting spheres.
        # The number of cells is width + 1 by height + 1.
        return cls((width + 1, height + 1), map=map)
