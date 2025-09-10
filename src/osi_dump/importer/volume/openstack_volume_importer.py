import logging
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
            osvolume_iterator = self.connection.block_storage.volumes(details=True, all_projects=True)
            
            for volume in osvolume_iterator:
                yield self._get_volume_info(volume)

        except Exception as e:
            logger.error(f"Cannot fetch volumes for {self.connection.auth['auth_url']}: {e}")
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

        return Volume(
            volume_id=volume.id,
            volume_name=volume.name,
            project_id=volume.project_id,
            status=volume.status,
            attachments=[att["server_id"] for att in volume.attachments],
            type=volume.volume_type,
            size=volume.size,
            snapshots=snapshots,
            updated_at=volume.updated_at,
            created_at=volume.created_at,
        )
