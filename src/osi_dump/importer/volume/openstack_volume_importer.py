import logging
import json
from typing import Generator
from openstack.connection import Connection
from openstack.block_storage.v3.volume import Volume as OSVolume

from osi_dump.importer.volume.volume_importer import VolumeImporter
from osi_dump.model.volume import Volume

logger = logging.getLogger(__name__)


class OpenStackVolumeImporter(VolumeImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_volumes(self) -> Generator[Volume, None, None]:
        logger.info(f"Importing volumes for {self.connection.auth['auth_url']}")
        try:
            osvolume_iterator = self.connection.block_storage.volumes(
                details=True, all_projects=True
            )
            for volume in osvolume_iterator:
                yield self._get_volume_info(volume)

        except Exception as e:
            logger.error(
                f"Cannot fetch volumes for {self.connection.auth['auth_url']}: {e}"
            )
            return

        logger.info(f"Finished importing volumes for {self.connection.auth['auth_url']}")

    def _get_volume_info(self, volume: OSVolume) -> Volume:
        snapshots = []
        try:
            snapshot_list = self.connection.block_storage.snapshots(
                details=False, all_projects=True, volume_id=volume.id
            )
            snapshots = [snapshot.id for snapshot in snapshot_list]

        except Exception as e:
            logger.warning(f"Fetching snapshots failed for {volume.id} error: {e}")

        # --- BẮT ĐẦU THAY ĐỔI THEO SDK ---
        # Lấy thuộc tính host trực tiếp như tài liệu SDK
        host_attr = volume.host

        # Lấy và xử lý metadata (giữ nguyên logic vì đã chính xác)
        image_metadata_dict = {}
        if volume.volume_image_metadata:
            # SDK có thể trả về dict sẵn hoặc string tùy phiên bản
            if isinstance(volume.volume_image_metadata, str):
                try:
                    image_metadata_dict = json.loads(volume.volume_image_metadata)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse volume_image_metadata for volume {volume.id}")
            elif isinstance(volume.volume_image_metadata, dict):
                image_metadata_dict = volume.volume_image_metadata
        # --- KẾT THÚC THAY ĐỔI THEO SDK ---

        return Volume(
            volume_id=volume.id,
            volume_name=volume.name,
            project_id=volume.project_id,
            status=volume.status,
            attachments=[att["server_id"] for att in volume.attachments],
            type=volume.volume_type,
            size=volume.size,
            snapshots=snapshots,
            host=host_attr,
            image_metadata=image_metadata_dict,
            updated_at=volume.updated_at,
            created_at=volume.created_at,
        )