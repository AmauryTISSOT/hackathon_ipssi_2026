import os
from datetime import datetime
from pathlib import Path
import cv2
import numpy as np
import random

from pymupdf import pymupdf

from data.utils import get_project_root


ROOT_DIR = get_project_root()

execution_date = datetime.now().strftime("%Y%m%d_%H%M%S")
PDF_BASE_DIR = os.path.join(ROOT_DIR, "data", "fake_data", "urssaf_vigilance")
IMG_CLEAN_DIR = Path(ROOT_DIR) / "data" / "fake_data" / "images_clean" / execution_date
IMG_NOISY_DIR = Path(ROOT_DIR) / "data" / "fake_data" / "images_noisy" / execution_date

IMG_CLEAN_DIR.mkdir(parents=True, exist_ok=True)
IMG_NOISY_DIR.mkdir(parents=True, exist_ok=True)


def extract_pdf_pages_to_images():
    versions = [
        d for d in Path(PDF_BASE_DIR).iterdir()
        if d.is_dir() and d.name.startswith("2026")
    ]

    if not versions:
        raise FileNotFoundError("Aucun dossier de version trouvé dans urssaf_vigilance.")

    pdf_dir = sorted(versions)[-1]
    print(f"Extraction PDF → PNG depuis : {pdf_dir}")

    for pdf_path in pdf_dir.glob("*.pdf"):
        doc = pymupdf.open(pdf_path)

        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
            save_path = IMG_CLEAN_DIR / f"{pdf_path.stem}_{i}.png"
            pix.save(str(save_path))
            print(f"Exporté : {save_path.name}")

        doc.close()

def add_noise(image):
    noise = np.random.normal(0, 25, image.shape).astype(np.uint8)
    return cv2.add(image, noise)


def add_blur(image):
    k = random.choice([3, 5])
    return cv2.GaussianBlur(image, (k, k), 0)


def add_motion_blur(image):
    size = random.randint(5, 15)
    kernel = np.zeros((size, size))
    kernel[int((size - 1) / 2), :] = np.ones(size)
    kernel /= size
    return cv2.filter2D(image, -1, kernel)


def rotate(image):
    angle = random.uniform(-5, 5)
    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
    return cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def perspective_transform(image):
    h, w = image.shape[:2]
    shift = 20

    pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
    pts2 = np.float32([
        [random.randint(0, shift), random.randint(0, shift)],
        [w - random.randint(0, shift), random.randint(0, shift)],
        [random.randint(0, shift), h - random.randint(0, shift)],
        [w - random.randint(0, shift), h - random.randint(0, shift)]
    ])

    M = cv2.getPerspectiveTransform(pts1, pts2)
    return cv2.warpPerspective(image, M, (w, h))


def jpeg_compression(image):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), random.randint(30, 70)]
    _, encimg = cv2.imencode('.jpg', image, encode_param)
    return cv2.imdecode(encimg, 1)


def change_brightness(image):
    factor = random.uniform(0.6, 1.4)
    return np.clip(image * factor, 0, 255).astype(np.uint8)


def degrade(image):
    if random.random() < 0.7:
        image = rotate(image)

    if random.random() < 0.5:
        image = perspective_transform(image)

    if random.random() < 0.6:
        image = add_blur(image)

    if random.random() < 0.5:
        image = add_motion_blur(image)

    if random.random() < 0.7:
        image = add_noise(image)

    if random.random() < 0.8:
        image = change_brightness(image)

    if random.random() < 0.9:
        image = jpeg_compression(image)

    return image

def degrade_images():
    print(f"Dégradation des images depuis : {IMG_CLEAN_DIR}")

    for img_path in IMG_CLEAN_DIR.glob("*.png"):
        image = cv2.imread(str(img_path))

        for i in range(3):
            degraded = degrade(image)
            output_path = IMG_NOISY_DIR / f"{img_path.stem}_noisy_{i}.jpg"
            cv2.imwrite(str(output_path), degraded)
            print(f"Créé : {output_path.name}")

def main():
    extract_pdf_pages_to_images()
    degrade_images()


if __name__ == "__main__":
    main()