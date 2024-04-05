from datetime import datetime
import qrcode
import logging.config
import os
from pathlib import Path
from pydantic import BaseModel, HttpUrl
from fastapi import FastAPI, APIRouter, HTTPException
app = FastAPI()


class QRCodeRequest(BaseModel):
    url: HttpUrl
    fill_color: str = "red"
    back_color: str = "white"
    size: int = 10


# Environment Variables for Configuration
QR_DIRECTORY = Path(os.getenv('QR_CODE_DIR', './qr_codes'))
FILL_COLOR = os.getenv('FILL_COLOR', 'red')
BACK_COLOR = os.getenv('BACK_COLOR', 'white')


def setup_logging():
    logging.config.dictConfig({
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'detailed',
            },
        },
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console'],
                'level': 'INFO'
            },
        }
    })


def create_directory():
    try:
        QR_DIRECTORY.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to create directory {QR_DIRECTORY}: {e}")
        raise


def generate_qr_code(data: str, path: Path, fill_color: str = 'red', back_color: str = 'white', size: int = 10):
    try:
        qr = qrcode.QRCode(version=1, box_size=size, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fill_color, back_color=back_color)

        with path.open('wb') as qr_file:
            img.save(qr_file)
        logging.info(f"QR code successfully saved to {path}")
    except Exception as e:
        logging.error(
            f"An error occurred while generating or saving the QR code: {e}")
        raise


router = APIRouter()


@router.post("/generate_qr/")
async def generate_qr(request: QRCodeRequest):
    setup_logging()  # Initialize logging
    create_directory()  # Ensure QR directory exists

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    qr_filename = f"QRCode_{timestamp}.png"
    qr_code_full_path = QR_DIRECTORY / qr_filename

    try:
        generate_qr_code(request.url, qr_code_full_path,
                         request.fill_color, request.back_color, request.size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

    return {"message": "QR code generated successfully", "path": str(qr_code_full_path)}

app.include_router(router)
