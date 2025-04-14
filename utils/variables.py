import numpy as np
from .decorators import errorhandler
from .colors import appColors


@errorhandler
def constant(nz: int, base_thickness: float) -> np.ndarray:
    """Constant thickness profile."""
    return np.full(nz, base_thickness)


@errorhandler
def linearly_tappered(nz: int, base_thickness: float) -> np.ndarray:
    """Linearly tapered thickness profile."""
    return np.linspace(base_thickness * 0.5, base_thickness * 1.5, nz)


@errorhandler
def parabolic(nz: int, base_thickness: float) -> np.ndarray:
    """Parabolic thickness profile."""
    normalized_z = np.linspace(-1, 1, nz)
    return base_thickness * (1 + 0.5 * (1 - normalized_z**2))


@errorhandler
def custom_wavy(nz: int, base_thickness: float) -> np.ndarray:
    """Custom wavy thickness profile."""
    return base_thickness * np.flip(np.square(np.sin(np.linspace(0, np.pi/2, nz))))


THICKNESS_PROFILES = {
    "C": {
        "name": "Constant",
        "equation": constant,
    },
    "LT": {
        "name": "LINEARLY_TAPPERED",
        "equation": linearly_tappered,
    },
    "P": {
        "name": "PARABOLIC",
        "equation": parabolic,
    },
    "CW": {
        "name": "CUSTOM WAVY",
        "equation": custom_wavy,
    },
}


AXIS_LABELS = {
    "x": {
        "label": "X",
        "color": appColors.tertiary_rbg,
        "pos": (1, 0, 0),
    },
    "y": {
        "label": "Y",
        "color": appColors.warning_rbg,
        "pos": (0, 1, 0),
    },
    "z": {
        "label": "Z",
        "color": appColors.success_rbg,
        "pos": (0, 0, 1),
    },
}


DEPTH_DETAIL_LEVELS = [
    {
        "name": "None",
        "value": 0,
    },
    {
        "name": "Low",
        "value": 25,
    },
    {
        "name": "Medium",
        "value": 50,
    },
    {
        "name": "High",
        "value": 75,
    },
    {
        "name": "Ultra",
        "value": 100,
    },
]

FLUIDS = {
    "mud": {
        "name": "Mud",
        "color": appColors.danger_shade_rbg,
    },
    "spacer": {
        "name": "Water",
        "color": appColors.tertiary_rbg,
    },
    "slurry": {
        "name": "Slurry",
        "color": appColors.medium_shade_rbg,
    },
}


PROGESS_BAR_STYLE = """

    QProgressBar {
        border-width: 1px 0px 0px 0px;
        border-color: white;
        border-style: solid;
        padding: 0px;
        background: white;
    }

    QProgressBar::chunk {
        background-color: orange;
    }

"""