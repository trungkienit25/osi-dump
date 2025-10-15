import pandas as pd
import logging
from typing import Generator

from osi_dump import util
from osi_dump.exporter.volume.volume_exporter import VolumeExporter
from osi_dump.model.volume import Volume

logger = logging.getLogger(__name__)


class ExcelVolumeExporter(VolumeExporter):
    def __init__(self, sheet_name: str, output_file: str):
        self.sheet_name = sheet_name
        self.output_file = output_file

    def export_volumes(self, volumes: Generator[Volume, None, None]):
        df = pd.DataFrame(volume.model_dump() for volume in volumes)

        if df.empty:
            logger.info(f"No volumes to export for {self.sheet_name}")
            return

        if "image_metadata" in df.columns and not df["image_metadata"].isnull().all():
            try:
                valid_metadata = df["image_metadata"].apply(lambda x: x if isinstance(x, dict) else {})
                
                metadata_df = pd.json_normalize(valid_metadata)

                if not metadata_df.empty:
                    metadata_df = metadata_df.add_prefix("meta.")

                    df = df.drop(columns=["image_metadata"])
                    df = pd.concat([df, metadata_df], axis=1)
                else:
                    df = df.drop(columns=["image_metadata"])

            except Exception as e:
                logger.warning(f"Could not normalize image_metadata for {self.sheet_name}: {e}")
                if "image_metadata" in df.columns:
                    df = df.drop(columns=["image_metadata"])

        if "volume_name" in df.columns:
            df.sort_values(by="volume_name", inplace=True, na_position="last")

        logger.info(f"Exporting volumes for {self.sheet_name}")
        try:
            util.export_data_excel(self.output_file, sheet_name=self.sheet_name, df=df)
            logger.info(f"Exported volumes for {self.sheet_name}")
        except Exception as e:
            logger.warning(f"Exporting volumes for {self.sheet_name} error: {e}")