from typing import Any, Generator, Optional, Dict, List
import logging
from collections import defaultdict

from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.volume import VolumeModel

class OpenStackVolumeImporter(IResourceImporter):
    """
    Fetches Volume data from OpenStack using a Two-Phase Fetch pattern.
    """
    def __init__(self, conn: Any):
        """
        :param conn: An initialized openstack.connection.Connection object
        """
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[VolumeModel, None, None]:
        """
        Phase 1: Cache Snapshots and Projects.
        Phase 2: Fetch volume summaries and iterate for details.
        """
        # --- PHASE 1: Caching & Discovery ---
        self.logger.info("Phase 1: Caching Snapshots and Projects...")

        # Cache Projects: ID -> Name
        project_map: Dict[str, str] = {}
        try:
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
        except Exception as e:
            self.logger.warning(f"Failed to cache projects in volume importer: {e}")

        # Cache Snapshots: Volume ID -> List of Snapshot IDs
        # We fetch ALL snapshots once instead of querying per volume
        snapshots_map: Dict[str, List[str]] = defaultdict(list)
        try:
            # Ensure we look at all projects
            all_snapshots = self.conn.block_storage.snapshots(all_projects=True, details=False)
            for snap in all_snapshots:
                if snap.volume_id:
                    snapshots_map[snap.volume_id].append(snap.id)
        except Exception as e:
            self.logger.error(f"Failed to cache snapshots: {e}")
            # Proceed even if snapshot caching fails

        # --- PHASE 2: Extraction ---
        self.logger.info("Phase 2: Fetching Volume Summaries...")
        
        try:
            volume_summaries = self.conn.block_storage.volumes(details=False, all_projects=True)
        except Exception as e:
            self.logger.critical(f"Failed to list volumes: {e}")
            return

        for summary in volume_summaries:
            try:
                # Granular fetch for details
                volume = self.conn.block_storage.get_volume(summary.id)
                if not volume:
                    self.logger.warning(f"Volume {summary.id} not found during detail fetch.")
                    continue

                # 1. Resolve Project Name
                proj_name = project_map.get(volume.project_id)
                
                # 2. Get Associated Snapshots from Cache
                associated_snaps = snapshots_map.get(volume.id, [])

                # 3. Yield Model
                yield VolumeModel(
                    id=volume.id,
                    name=volume.name,
                    status=volume.status,
                    size_gb=volume.size,
                    project_id=volume.project_id,
                    project_name=proj_name,
                    user_id=volume.user_id,
                    volume_type=volume.volume_type,
                    snapshot_ids=associated_snaps,
                    created_at=volume.created_at
                )

            except Exception as e:
                # Robustness: Log and continue
                self.logger.error(f"Error extracting volume {summary.id}: {e}")
                continue