import os
import numpy as np
import scipy.ndimage as snd

from PySide6.QtGui import QColor
from PIL import Image
from .variables import FLUIDS
import h5py


def scale_with_pillow(
    arr: np.ndarray, factor: int | tuple[int, int] = 1, multiplier: int = 1
) -> np.ndarray:
    """
    scales an image using pillow
    """

    f_x, f_y = 1, 1
    if isinstance(factor, tuple):
        f_x, f_y = factor

    if isinstance(factor, int):
        f_x, f_y = (factor, factor)

    # create the pillow image
    img = Image.fromarray(arr)

    # scale it
    size = multiplier * f_x * img.width, multiplier * f_y * img.height
    s_img = img.resize(size, Image.LANCZOS)

    # resolve it as a np-array
    return np.array(s_img)


def apply_gaussian_filter(
    arr: np.ndarray, dimensions: list[int], factor: int = 1, multiplier: int = 1
) -> np.ndarray:
    """
    applies a uniform gaussian filter to target slices of array

    dimensions: a list integers of values 0 and 1. 0 for dimensions to be omited during filtration.
    len(dimensions) == len(arr.shape)
    """
    r = factor * multiplier

    # create the filter kernel
    kernel = []
    for i in range(len(dimensions)):
        kernel.append(dimensions[i] * r)

    f_arr = snd.gaussian_filter(arr, sigma=kernel)
    return f_arr


def apply_scaling(arr: np.ndarray, factor: int = 2, filter_only=False):
    if filter_only:
        return apply_gaussian_filter(arr, [1, 1, 0], 2, factor)
    
    _a = (arr * 255).astype(np.uint8)
    a = scale_with_pillow(_a, 1, factor)
    b = apply_gaussian_filter(a, [1, 1, 0], 2, factor)
    return b / 255.0


def get_all_file_paths(target_dir: str) -> list[str]:
    """
    Returns a list of all file paths in the target directory and its subdirectories.

    Parameters:
        target_dir (str): The root directory to search.

    Returns:
        List[str]: List of full paths to all files.
    """
    file_paths = []
    for root, _, files in os.walk(target_dir):
        for file in files:
            full_path = os.path.join(root, file)
            file_paths.append(full_path)
    return file_paths


def read_image(image_path: str) -> np.ndarray:
    """
    Reads an image from the specified path and returns it as a numpy array.

    Parameters:
        image_path (str): Path to the image file.

    Returns:
        np.ndarray: Image as a numpy array.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    image = Image.open(image_path).convert("RGBA")  # ensures 4 channels
    return np.array(image) / 255.0  # normalize to [0, 1] float range


def load_images_from_directory(directory: str) -> list[np.ndarray]:
    """
    Loads all images from a specified directory into a list of numpy arrays.

    Parameters:
        directory (str): Path to the directory containing images.

    Returns:
        List[np.ndarray]: List of images as numpy arrays.
    """
    if not os.path.isdir(directory):
        raise NotADirectoryError(f"Directory not found: {directory}")

    image_paths = get_all_file_paths(directory)
    images = [read_image(path) for path in image_paths]
    return images


def extract_conc_from_h5file(file: str) -> np.ndarray:
    f = h5py.File(file, "r")
    d = f["csave"][:]
    f.close()
    return np.array(d)


def load_frames(file: str) -> dict:
    """
    Loads frames from a specified file.

    Parameters:
        file (str): Path to the file containing frames.

    Returns:
        dict: Dictionary containing loaded frames.
    """
    if not os.path.isfile(file):
        raise FileNotFoundError(f"File not found: {file}")

    data: np.ndarray = extract_conc_from_h5file(file)
    tmd = 0
    bmd = 800
    unit = "m"

    section = 1

    time_step, n_fluids, n_sections, n_xi, n_zeta = data.shape

    color_arr = []
    fluids = list(FLUIDS.values())
    ch = 3  # RGB channels
    for i in range(n_fluids):
        r, g, b, _ = QColor(fluids[i]["color"]).getRgbF()
        color_arr.append([r, g, b])

    base_colors = np.zeros((n_fluids, n_xi, n_zeta, ch))
    for i in range(n_fluids):
        for j in range(ch):
            grid = np.ones((n_xi, n_zeta)) * color_arr[i][j]
            base_colors[i, :, :, j] = grid

    pipe_frames = []
    ann_frames = []
    frames = []

    rotate = 1 == 0
    annlus_only = 1 == 1
    scale = 1 == 0

    ts = time_step - 1
    # ts = 1

    for j in range(ts):
        for k in range(n_sections):
            c_vals = data[j, :, k, :, :]
            c, _, n = c_vals.shape

            if k == section:  # only the annulus section
                alphas = c_vals.copy()
                a_sum = np.sum(alphas, axis=0)
                a_sum[a_sum == 0] = 1  # replace all zero-sums with 1
                w_c_vals: np.ndarray = (
                    np.sum(base_colors * alphas[..., np.newaxis], axis=0)
                    / a_sum[..., np.newaxis]
                )
                if rotate:
                    w_c_vals = np.rot90(w_c_vals, k=1)  # k=1 => 90° counter-clockwise
                else:
                    w_c_vals = np.flip(w_c_vals, axis=1)  # for backwards flow

                if scale:
                    w_c_vals = apply_scaling(w_c_vals, 2, filter_only=True)

                n_xi = w_c_vals.shape[0]
                n_zeta = w_c_vals.shape[1]

                ann_frames.append(w_c_vals)
            else:
                if not annlus_only:
                    # get the 1D line
                    alphas = c_vals[:, 0, :].reshape((c, 1, n))
                    alpha_sum = np.sum(alphas, axis=0)
                    alpha_sum[alpha_sum == 0] = 1.0  # replace all zero-sums with 1

                    # compute weighted rbg using alphas as weights
                    w_c_vals: np.ndarray = (
                        np.sum(base_colors * alphas[..., np.newaxis], axis=0)
                        / alpha_sum[..., np.newaxis]
                    )
                    if rotate:
                        w_c_vals = np.rot90(w_c_vals, k=-1)  # k=-1 => 90° clockwise

                    if scale:
                        w_c_vals = apply_scaling(w_c_vals, 2, filter_only=True)

                    n_xi = w_c_vals.shape[0]
                    n_zeta = w_c_vals.shape[1]
                    pipe_frames.append(w_c_vals)

    if annlus_only:
        # collect all frames
        print(
            "ann_frames.shape",
            ann_frames[0].shape,
        )
    else:
        print(
            "pipe_frames.shape",
            pipe_frames[0].shape,
            "ann_frames.shape",
            ann_frames[0].shape,
        )

    if annlus_only:
        frames = np.array(ann_frames)
    else:
        frames = np.concatenate([pipe_frames, ann_frames])

    # ensure they are between 0 and 1
    frames[frames > 1] = 1.0
    frames[frames < 0] = 0.0

    return {
        "images": frames,
        "tmd": tmd,
        "bmd": bmd,
        "unit": unit,
        "nxi": n_xi,
        "nzeta": n_zeta,
        "time_step": time_step,
    }
