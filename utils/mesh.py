import pyqtgraph.opengl as gl
import numpy as np
from PySide6.QtGui import QColor


def create_slab_mesh(opts: dict = None) -> gl.MeshData:
    if opts is None:
        opts = {}

    if not isinstance(opts, dict):
        raise TypeError("opts must be of type dict")

    _opts = {
        "color": opts.get("color", "#07293E"),
        "width": opts.get("width", 1),
        "height": opts.get("height", 1),
        "thickness": opts.get("thickness", 0.05),
        "position": opts.get("position", (0, 0, 0)),
        "x_points": opts.get("x_points", 2),
        "y_points": opts.get("y_points", 20),
        "z_points": opts.get("z_points", 20),
    }

    width: float = _opts["width"]
    height: float = _opts["height"]
    length: float = _opts["thickness"]
    nx: int = _opts["x_points"]
    ny: int = _opts["y_points"]
    nz: int = _opts["z_points"]

    # Create axes
    x = np.sin(np.linspace(-length / 2, length / 2, nx))
    y = np.linspace(-width / 2, width / 2, ny)
    z = np.sin(np.linspace(-height / 2, height / 2, nz))

    vertices = []
    faces = []
    vertex_map = {}  # To store unique vertex indices

    def add_vertex(v):
        key = tuple(v)
        if key not in vertex_map:
            vertex_map[key] = len(vertices)
            vertices.append(v)
        return vertex_map[key]

    def add_face(v0, v1, v2, v3):
        # Diagonal split into triangles
        faces.append([v0, v1, v2])
        faces.append([v0, v2, v3])

    # Generate 6 faces of the cuboid (surface only)
    for j in range(ny - 1):
        for i in range(nx - 1):
            # Bottom face (Z = -h/2)
            zc = -height / 2
            v0 = add_vertex([x[i], y[j], zc])
            v1 = add_vertex([x[i + 1], y[j], zc])
            v2 = add_vertex([x[i + 1], y[j + 1], zc])
            v3 = add_vertex([x[i], y[j + 1], zc])
            add_face(v0, v1, v2, v3)

            # Top face (Z = +h/2)
            zc = height / 2
            v0 = add_vertex([x[i], y[j], zc])
            v1 = add_vertex([x[i + 1], y[j], zc])
            v2 = add_vertex([x[i + 1], y[j + 1], zc])
            v3 = add_vertex([x[i], y[j + 1], zc])
            add_face(v0, v1, v2, v3)

    for k in range(nz - 1):
        for i in range(nx - 1):
            # Front face (Y = -w/2)
            yc = -width / 2
            v0 = add_vertex([x[i], yc, z[k]])
            v1 = add_vertex([x[i + 1], yc, z[k]])
            v2 = add_vertex([x[i + 1], yc, z[k + 1]])
            v3 = add_vertex([x[i], yc, z[k + 1]])
            add_face(v0, v1, v2, v3)

            # Back face (Y = +w/2)
            yc = width / 2
            v0 = add_vertex([x[i], yc, z[k]])
            v1 = add_vertex([x[i + 1], yc, z[k]])
            v2 = add_vertex([x[i + 1], yc, z[k + 1]])
            v3 = add_vertex([x[i], yc, z[k + 1]])
            add_face(v0, v1, v2, v3)

    for k in range(nz - 1):
        for j in range(ny - 1):
            # Left face (X = -l/2)
            xc = -length / 2
            v0 = add_vertex([xc, y[j], z[k]])
            v1 = add_vertex([xc, y[j + 1], z[k]])
            v2 = add_vertex([xc, y[j + 1], z[k + 1]])
            v3 = add_vertex([xc, y[j], z[k + 1]])
            add_face(v0, v1, v2, v3)

            # Right face (X = +l/2)
            xc = length / 2
            v0 = add_vertex([xc, y[j], z[k]])
            v1 = add_vertex([xc, y[j + 1], z[k]])
            v2 = add_vertex([xc, y[j + 1], z[k + 1]])
            v3 = add_vertex([xc, y[j], z[k + 1]])
            add_face(v0, v1, v2, v3)

    data = gl.MeshData(vertexes=np.array(vertices), faces=np.array(faces))
    return data


def create_mesh_item(opts: dict) -> gl.GLMeshItem:
    data = opts.get("meshdata", None)
    if not isinstance(data, gl.MeshData):
        raise TypeError("meshdata must be of type MeshData")

    cc: object | tuple = QColor(opts.get("color", "#fa0000")).getRgbF()
    mesh_item = gl.GLMeshItem(
        meshdata=data,
        smooth=True,
        drawFaces=True,
        drawEdges=True,
        color=(cc[0], cc[1], cc[2], 0.5),
        edgeColor=(cc[0], cc[1], cc[2], 1),
        shader="shaded",
        glOptions="opaque",
    )
    return mesh_item
