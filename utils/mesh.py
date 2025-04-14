import pyqtgraph.opengl as gl
import numpy as np
from PySide6.QtGui import QColor, QFont
from .signal_bus import signalBus


def create_mesh_item(opts: dict) -> gl.GLMeshItem:
    data = opts.get("meshdata", None)
    rotation = opts.get("rotation", (0, 0, 0, 0, False))
    if not isinstance(data, gl.MeshData):
        raise TypeError("meshdata must be of type MeshData")

    cc: object | tuple = QColor(opts.get("color", "#B2713D")).getRgbF()
    mesh_item = gl.GLMeshItem(
        meshdata=data,
        smooth=True,
        drawFaces=True,
        drawEdges=False,
        color=(cc[0], cc[1], cc[2], 0.5),
        edgeColor=(cc[0], cc[1], cc[2], 1),
        shader="shaded",
        glOptions="opaque",
    )
    angle, x, y, z, local = rotation
    mesh_item.rotate(angle, x, y, z, local)  # Rotate to align with the YZ plane
    return mesh_item


def create_slab_mesh(opts: dict = None) -> dict:
    if opts is None:
        opts = {}

    if not isinstance(opts, dict):
        raise TypeError("opts must be of type dict")

    _opts = {
        "color": opts.get("color", "#B2713D"),
        "images": opts.get("images", None),
        "width": opts.get("width", 1),  # along Y
        "height": opts.get("height", 1),  # along Z
        "base_thickness": opts.get("base_thickness", 0.1),  # base thickness along X
        "thickness_profile": opts.get("thickness_profile", None),
        "position": opts.get("position", (0, 0, 0)),
        "x_points": opts.get("x_points", 2),
        "y_points": opts.get("y_points", 20),
        "z_points": opts.get("z_points", 20),
    }

    base_thickness: float = _opts["base_thickness"]
    width: float = _opts["width"]
    height: float = _opts["height"]
    nx: int = _opts["x_points"]
    ny: int = _opts["y_points"]
    nz: int = _opts["z_points"]
    images: np.ndarray = _opts["images"]  # arr of shape (ny, nz, 4)
    use_image_color = images is not None and images.ndim == 4 and images.shape[1:3] == (nz, ny)
    print("images is not None", images is not None)
    print("images.ndim == 4", images.ndim == 4)
    print("images.shape[1:3] == (nz, ny)", images.shape[1:3] == (nz, ny))
    print("images.shape[1:3]", images.shape[1:3], "== (nz, ny)", (nz, ny))
    print("use_image_color", use_image_color)

    # Y and Z coordinates
    y: np.ndarray = np.linspace(-width / 2, width / 2, ny)
    z: np.ndarray = np.linspace(-height / 2, height / 2, nz)

    # Variable thickness profile along Z (height)
    if _opts["thickness_profile"] is not None:
        if len(_opts["thickness_profile"]) != nz:
            raise ValueError("thickness_profile must have the same length as z_points")
        thickness_profile: np.ndarray = _opts["thickness_profile"]
    else:
        # Default thickness profile: to be uniform
        thickness_profile: np.ndarray = (
            np.ones(shape=(nz,), dtype=float) * base_thickness
        )
    frames = []

    for image in images:
        vertices = []
        faces = []
        vertex_map = {}
        vertex_colors = []

        def add_vertex(v, j=None, k=None):
            key = tuple(np.round(v, 5))
            if key not in vertex_map:
                index = len(vertices)
                vertex_map[key] = index
                vertices.append(v)
                # Add default or texture color
                if use_image_color and j is not None and k is not None:
                    color = image[k, j]  # image indexed as (z, y)
                else:
                    color = QColor(_opts["color"]).getRgbF()
                vertex_colors.append(color)
            return vertex_map[key]

        def add_face(v0, v1, v2, v3):
            faces.append([v0, v1, v2])
            faces.append([v0, v2, v3])

        # Build faces along Y-Z plane (variable X thickness)
        for k in range(nz - 1):
            for j in range(ny - 1):
                z0, z1 = z[k], z[k + 1]
                t0 = thickness_profile[k] / 2
                t1 = thickness_profile[k + 1] / 2
                y0, y1 = y[j], y[j + 1]

                # Left face (X = -thickness/2)
                v0 = add_vertex([-t0, y0, z0], j=j, k=k)
                v1 = add_vertex([-t0, y1, z0], j=j + 1, k=k)
                v2 = add_vertex([-t1, y1, z1], j=j + 1, k=k + 1)
                v3 = add_vertex([-t1, y0, z1], j=j, k=k + 1)
                add_face(v0, v1, v2, v3)

                # Right face (X = +thickness/2)
                v0 = add_vertex([t0, y0, z0], j=j, k=k)
                v1 = add_vertex([t0, y1, z0], j=j + 1, k=k)
                v2 = add_vertex([t1, y1, z1], j=j + 1, k=k + 1)
                v3 = add_vertex([t1, y0, z1], j=j, k=k + 1)
                add_face(v0, v1, v2, v3)

        # Front and back faces (Y-constant), interpolated thickness
        for k in range(nz - 1):
            z0, z1 = z[k], z[k + 1]
            t0 = thickness_profile[k] / 2
            t1 = thickness_profile[k + 1] / 2
            for i in range(nx - 1):
                x0 = np.linspace(-t0, t0, nx)[i]
                x1 = np.linspace(-t0, t0, nx)[i + 1]
                x2 = np.linspace(-t1, t1, nx)[i + 1]
                x3 = np.linspace(-t1, t1, nx)[i]

                # Front face (Y = -width/2)
                y_front = -width / 2
                v0 = add_vertex([x0, y_front, z0])
                v1 = add_vertex([x1, y_front, z0])
                v2 = add_vertex([x2, y_front, z1])
                v3 = add_vertex([x3, y_front, z1])
                add_face(v0, v1, v2, v3)

                # Back face (Y = +width/2)
                y_back = width / 2
                v0 = add_vertex([x0, y_back, z0])
                v1 = add_vertex([x1, y_back, z0])
                v2 = add_vertex([x2, y_back, z1])
                v3 = add_vertex([x3, y_back, z1])
                add_face(v0, v1, v2, v3)

        # Top and bottom faces (Z = constant)
        for j in range(ny - 1):
            y0 = y[j]
            y1 = y[j + 1]
            for k in [0, nz - 1]:
                zc = z[k]
                tzc = thickness_profile[k] / 2
                for i in range(nx - 1):
                    x0 = np.linspace(-tzc, tzc, nx)[i]
                    x1 = np.linspace(-tzc, tzc, nx)[i + 1]

                    # Bottom face (Z = z[0])
                    if k == 0:
                        v0 = add_vertex([x0, y0, zc])
                        v1 = add_vertex([x1, y0, zc])
                        v2 = add_vertex([x1, y1, zc])
                        v3 = add_vertex([x0, y1, zc])
                    # Top face (Z = z[-1])
                    else:
                        v0 = add_vertex([x0, y0, zc])
                        v1 = add_vertex([x1, y0, zc])
                        v2 = add_vertex([x1, y1, zc])
                        v3 = add_vertex([x0, y1, zc])

                    add_face(v0, v1, v2, v3)

        v = np.array(vertices)
        f = np.array(faces)
        c = np.array(vertex_colors)
        frames.append(gl.MeshData(vertexes=v, faces=f, vertexColors=c))
    return {"meshdata": frames}


def create_depth_vertex_array(opts: dict) -> np.ndarray:
    if not isinstance(opts, dict):
        raise TypeError("opts must be of type dict")

    thickness_profile: np.ndarray = opts.get("thickness_profile", None)
    plane: str = opts.get("plane", "zy")
    size: int = opts.get("size", 1)
    anchor: str = opts.get("anchor", "center")
    padding: float = opts.get("padding", 0.01)

    if not isinstance(thickness_profile, np.ndarray):
        raise TypeError("thickness_profile must be of type np.ndarray")

    if thickness_profile.ndim == 1:
        msg = {
            "text": f"Assume vector of thicknesses: nz = <{thickness_profile.shape[0]}>",
            "type": "info",
        }
        signalBus.onMessage.emit(msg)

        if anchor == "center" and plane == "yz":
            entries = np.linspace(
                -size / 2, size / 2, thickness_profile.shape[0], dtype=float
            )
            depths = np.zeros((thickness_profile.shape[0], 3), dtype=float)
            depths[:, 0] = padding + thickness_profile
            depths[:, 1] = -(size / 2 + padding)
            depths[:, 2] = entries
            return depths

        elif anchor == "center" and plane == "zy":
            entries = np.linspace(
                -size / 2, size / 2, thickness_profile.shape[0], dtype=float
            )
            depths = np.zeros((thickness_profile.shape[0], 3), dtype=float)
            depths[:, 0] = padding + thickness_profile
            depths[:, 1] = size / 2 + padding
            depths[:, 2] = entries
            return depths
        
        elif anchor == "center" and plane == "xy":
            entries = np.linspace(
                -size / 2, size / 2, thickness_profile.shape[0], dtype=float
            )
            depths = np.zeros((thickness_profile.shape[0], 3), dtype=float)
            depths[:, 0] = padding + thickness_profile
            depths[:, 1] = entries
            depths[:, 2] = -(size / 2 + padding)
            return depths
        elif anchor == "center" and plane == "yx":
            entries = np.linspace(
                -size / 2, size / 2, thickness_profile.shape[0], dtype=float
            )
            depths = np.zeros((thickness_profile.shape[0], 3), dtype=float)
            depths[:, 0] = padding + thickness_profile
            depths[:, 1] = entries
            depths[:, 2] = size / 2 + padding
            return depths
        else:
            raise ValueError(
                "curreintly only support anchor = center and plane = yz or zy"
            )
    else:
        raise ValueError("Support 2d thickness profile not implemented yet")


def create_text_items(opts: dict) -> list[gl.GLTextItem]:
    if not isinstance(opts, dict):
        raise TypeError("opts must be of type dict")

    tmd: float = opts.get("tmd", 0)
    bmd: float = opts.get("bmd", 100)
    unit: str = opts.get("unit", "m")
    color: str = opts.get("text_color", "#FFFFFF")
    font: QFont = opts.get("font", QFont("Helvetica", 10))
    detail_level: int = opts.get(
        "detail_level", 0.25
    )  # exists between 0 and 1. 0 = no detail, 1 = full detail
    positions: np.ndarray = opts.get("text_positions", None)

    if tmd == 0 and bmd == 0:
        return []

    if not isinstance(tmd, (int, float)):
        raise TypeError("tmd must be of type int or float")
    if not isinstance(bmd, (int, float)):
        raise TypeError("bmd must be of type int or float")
    if not isinstance(unit, str):
        raise TypeError("unit must be of type str")
    if not isinstance(positions, np.ndarray):
        raise TypeError("positions must be of type np.ndarray")

    if positions.shape[1] != 3:
        raise ValueError(f"positions must have 3 columns: {positions.shape[1]} != 3")

    depths = np.round(np.linspace(tmd, bmd, positions.shape[0], dtype=float), 2)

    if detail_level == 0:
        return []

    keep_n = int(np.round(positions.shape[0] * detail_level))
    idx = np.linspace(0, positions.shape[0] - 1, keep_n, dtype=int)
    filtered_positions = positions[idx, :]
    filtered_depths = depths[idx]

    items = [
        gl.GLTextItem(
            pos=filtered_positions[i, :],
            text=f"{filtered_depths[i]} {unit}",
            color=QColor(color),
            font=font,
        )
        for i in range(filtered_positions.shape[0])
    ]

    return items
