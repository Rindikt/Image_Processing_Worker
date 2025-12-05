from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DATA_DIR = Path("/app/data")

DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "processed").mkdir(exist_ok=True)
(DATA_DIR / "raw").mkdir(exist_ok=True)

def apply_grayscale(input_filename: str, output_filename: str):
    """
    Открывает изображение, применяет фильтр "Градации серого" и сохраняет результат.
    """

    input_path = DATA_DIR / "raw" / input_filename
    output_path = DATA_DIR / "processed" / output_filename

    try:
        img = Image.open(input_path)

        img_gray = img.convert("L")

        img_gray.save(output_path)

        return True
    except FileNotFoundError:
        print(f"File not found: {input_path}")
        return False
    except Exception as e:
        print(f"Error processing image: {e}")
        return False


def resize_image(input_filename: str, output_filename: str, size: tuple[int, int]):
    """
    Изменяет размер изображения до заданных width x height и сохраняет результат.
    """
    input_path = DATA_DIR / "raw" / input_filename
    output_path = DATA_DIR / "processed" / output_filename
    try:
        img = Image.open(input_path)

        img_resized = img.resize(size)
        img_resized.save(output_path)
        return True
    except FileNotFoundError:
        print(f"File not found: {input_path}")
        return False
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

def sepia_image(input_filename: str, output_filename: str):
    """
    Применяет эффект Сепии к изображению.
    """
    input_path = DATA_DIR / "raw" / input_filename
    output_path = DATA_DIR / "processed" / output_filename

    try:
        # 1. Открываем изображение и конвертируем в RGB (для надежности)
        img = Image.open(input_path).convert("RGB")

        # 2. Получаем монохромную версию (маска яркости)
        grayscale_mask = img.convert("L")

        # 3. Конвертируем маску обратно в RGB, чтобы она могла смешиваться
        grayscale_rgb = grayscale_mask.convert("RGB")

        # 4. Создаем "холст" с цветом сепии
        sepia_color = (255, 200, 150)  # Теплый, насыщенный бежевый
        sepia_base = Image.new("RGB", img.size, sepia_color)

        # 5. Смешивание (Image.blend): Смешиваем бежевый фон с черно-белым изображением.
        #    alpha=0.6 означает 60% Sepia Base и 40% Grayscale (для тонирования)
        final_img = Image.blend(sepia_base, grayscale_rgb, alpha=0.6)

        # 6. Сохраняем результат
        final_img.save(output_path, "JPEG")
        return True

    except Exception as e:
        logger.error(f"Error applying sepia to image {input_filename}: {e}")
        return False

def crop_image(input_filename: str, output_filename: str, box: tuple[int, int, int, int])-> bool:
    """
    Обрезает изображение по заданным координатам (left, top, right, bottom).
    """
    input_path = DATA_DIR / "raw" / input_filename
    output_path = DATA_DIR / "processed" / output_filename

    try:
        img = Image.open(input_path).convert("RGB")
        cropped_img = img.crop(box)
        cropped_img.save(output_path)
        return True
    except Exception as e:
        logger.error(f"Error cropping image {input_filename} with box {box}: {e}")
        return False
