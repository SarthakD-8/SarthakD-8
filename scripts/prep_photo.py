
"""
Prepare a portrait for ASCII conversion.

Pipeline:
1. Remove background using rembg.
2. Convert to grayscale.
3. Smooth image texture while preserving facial edges.
4. Enhance contrast and facial details.
5. Composite onto a clean white background.
6. Crop the subject into a square image.
"""

from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove


ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else ROOT / "source-photo.png"
)

OUTPUT_PATH = (
    Path(sys.argv[2])
    if len(sys.argv) > 2
    else ROOT / "source-prepped.png"
)

LINE_WEIGHT = 0.55
PADDING = 70


def prepare_photo(input_path: Path, output_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Photo not found: {input_path}")

    # 1. Remove background.
    original = Image.open(input_path).convert("RGBA")
    cutout = remove(original)

    rgb = np.array(cutout.convert("RGB"))
    alpha = np.array(cutout.getchannel("A"))

    if not np.any(alpha > 20):
        raise ValueError("Background removal produced an empty subject mask.")

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # 2. Smooth texture while preserving edges.
    smooth = gray.copy()

    for _ in range(3):
        smooth = cv2.bilateralFilter(
            smooth,
            d=9,
            sigmaColor=40,
            sigmaSpace=9,
        )

    # 3. Normalize tones using only the foreground.
    subject_pixels = smooth[alpha > 128]

    if subject_pixels.size == 0:
        raise ValueError("No usable foreground pixels detected.")

    low, high = np.percentile(subject_pixels, [2, 96])
    denominator = max(float(high - low), 1.0)

    tone = np.clip(
        (smooth.astype(np.float32) - low) / denominator,
        0,
        1,
    )

    # 4. Enhance fine facial details.
    fine = cv2.GaussianBlur(
        smooth.astype(np.float32),
        (0, 0),
        1.5,
    )

    coarse = cv2.GaussianBlur(
        smooth.astype(np.float32),
        (0, 0),
        6,
    )

    lines = np.clip((coarse - fine) / 40.0, 0, 1)

    enhanced = np.clip(
        tone - LINE_WEIGHT * lines,
        0,
        1,
    ) * 255

    # 5. Composite onto white.
    mask = cv2.GaussianBlur(
        alpha.astype(np.float32) / 255.0,
        (0, 0),
        1.0,
    )

    final = (
        enhanced * mask
        + 255.0 * (1.0 - mask)
    )

    final = np.clip(final, 0, 255).astype(np.uint8)

    # 6. Square crop around the foreground.
    ys, xs = np.where(alpha > 20)

    x_min, x_max = xs.min(), xs.max()
    y_min, y_max = ys.min(), ys.max()

    center_x = (x_min + x_max) // 2
    center_y = (y_min + y_max) // 2

    side = max(
        x_max - x_min,
        y_max - y_min,
    ) + PADDING

    canvas = np.full(
        (side, side),
        255,
        dtype=np.uint8,
    )

    x0 = center_x - side // 2
    y0 = center_y - side // 2

    sx0 = max(x0, 0)
    sy0 = max(y0, 0)

    sx1 = min(x0 + side, final.shape[1])
    sy1 = min(y0 + side, final.shape[0])

    canvas[
        sy0 - y0:sy1 - y0,
        sx0 - x0:sx1 - x0,
    ] = final[sy0:sy1, sx0:sx1]

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    Image.fromarray(canvas, mode="L").save(output_path)

    print(f"Prepared portrait: {output_path}")
    print(f"Image dimensions: {side} x {side}")


if __name__ == "__main__":
    prepare_photo(INPUT_PATH, OUTPUT_PATH)
