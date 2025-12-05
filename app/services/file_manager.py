from fastapi import UploadFile
from pathlib import Path
import uuid
import shutil
import logging

DATA_DIR = Path('/app/data')
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def generate_filenames(original_filename: str, process_type: str)->tuple[str, str]:
    """
    Генерирует уникальные имена для входного и выходного файлов.
    Возвращает (input_filename, output_filename)
    """

    file_extension = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())

    input_filename = f"{unique_id}_raw{file_extension}"
    output_filename = f"{unique_id}_{process_type}{file_extension}"

    return input_filename, output_filename

async def save_uploaded_file(uploaded_file: UploadFile, input_filename: str)->Path:
    """
    Сохраняет UploadFile на диск в папку RAW_DIR.
    Возвращает полный путь к сохраненному файлу.
    """
    input_path = RAW_DIR / input_filename

    with open(input_path, 'wb') as f:
        while chunk := await uploaded_file.read(8192):
            f.write(chunk)

    return input_path


def get_raw_file_path(input_filename: str)->Path:
    """
    Возвращает полный путь к исходному файлу.
    """
    return RAW_DIR / input_filename


def get_processed_file_path(output_filename: str)->Path:
    """
    Возвращает полный путь к обработанному файлу.
    """
    return PROCESSED_DIR / output_filename

def cleanup_files(input_filename: str, output_filename: str)->None:
    """
    Удаляет исходный и обработанный файлы с диска.
    """
    input_path = RAW_DIR / input_filename
    output_path = PROCESSED_DIR / output_filename

    if input_path.exists():
        try:
            input_path.unlink()
            logging.info(f"Successfully cleaned up RAW file: {input_filename}")
        except OSError as e:
            logging.error(f"Failed to cleanup RAW file: {input_filename}: {e}")
    if output_path.exists():
        try:
            output_path.unlink()
            logging.info(f"Successfully cleaned up PROCESSED file: {output_filename}")
        except OSError as e:
            logging.error(f"Failed to cleanup PROCESSED file: {output_filename}: {e}")

