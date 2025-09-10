import pandas as pd
import logging
from typing import Generator

from osi_dump import util
from osi_dump.exporter.image.image_exporter import ImageExporter
from osi_dump.model.image import Image

logger = logging.getLogger(__name__)

class ExcelImageExporter(ImageExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_images(self, images: Generator[Image, None, None]):
        df = pd.json_normalize(image.model_dump() for image in images)

        if df.empty:
            logger.info(f"No images to export for {self.sheet_name}")
            return
            
        if 'image_name' in df.columns:
            df.sort_values(by='image_name', inplace=True, na_position='last')

        logger.info(f"Exporting images for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported images for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting images for {self.sheet_name} error: {e}")
