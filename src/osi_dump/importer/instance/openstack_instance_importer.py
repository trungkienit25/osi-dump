from typing import Any, Generator, Optional, Dict
import logging

from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.instance import InstanceModel

class OpenStackInstanceImporter(IResourceImporter):
    """
    Fetches Instance data from OpenStack using a Two-Phase Fetch pattern
    to minimize API latency and N+1 query issues.
    """
    def __init__(self, conn: Any):
        """
        :param conn: An initialized openstack.connection.Connection object
        """
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[InstanceModel, None, None]:
        """
        Phase 1: Cache dependent data (Projects, Flavors).
        Phase 2: Fetch instance summaries and iterate for details.
        """
        # --- PHASE 1: Caching & Discovery ---
        self.logger.info("Phase 1: Caching Projects and Flavors...")
        
        # Cache Projects: ID -> Name
        project_map: Dict[str, str] = {}
        try:
            # listing projects might require admin rights or scope
            # We wrap this in a try-except to handle permissions safely
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
        except Exception as e:
            self.logger.warning(f"Failed to cache projects (continuing without project names): {e}")

        # Cache Flavors: ID -> Flavor Object (dict or object)
        # We need the full flavor details for extra_specs (GPU parsing)
        flavor_map: Dict[str, Any] = {}
        try:
            for flavor in self.conn.compute.flavors(details=True):
                flavor_map[flavor.id] = flavor
        except Exception as e:
            self.logger.error(f"Failed to cache flavors (GPU info may be missing): {e}")
            # We proceed even if flavor caching fails

        # --- PHASE 2: Extraction ---
        self.logger.info("Phase 2: Fetching Instance Summaries...")
        
        # Get list of servers with details=False for speed
        # all_projects=True is usually required for a 'dump' tool
        try:
            server_summaries = self.conn.compute.servers(details=False, all_projects=True)
        except Exception as e:
            self.logger.critical(f"Failed to list servers: {e}")
            return

        for summary in server_summaries:
            try:
                # Granular fetch for details
                # We fetch the full server details to get precise current state
                server = self.conn.compute.get_server(summary.id)
                if not server:
                    self.logger.warning(f"Server {summary.id} not found during detail fetch.")
                    continue

                # 1. Resolve Project Name
                proj_name = project_map.get(server.project_id)

                # 2. Resolve Flavor and GPU Info
                flavor_id = server.flavor.get('id') if server.flavor else ''
                flavor_name = server.flavor.get('original_name') or server.flavor.get('id')
                
                # Check our cached flavor map for extra_specs
                cached_flavor = flavor_map.get(flavor_id)
                gpu_type = None
                gpu_count = 0

                if cached_flavor:
                    # 'extra_specs' might be a property or dict key depending on SDK version
                    extra_specs = getattr(cached_flavor, 'extra_specs', {}) or {}
                    pci_alias = extra_specs.get('pci_passthrough:alias')
                    
                    if pci_alias:
                        # Logic: "hgx_h100:8,bridge_h100:4" -> "hgx_h100", 8
                        try:
                            # Take first alias before comma
                            primary_alias = pci_alias.split(',')[0]
                            if ':' in primary_alias:
                                parts = primary_alias.split(':')
                                gpu_type = parts[0]
                                gpu_count = int(parts[1])
                            else:
                                # Fallback if no count specified (unlikely but safe)
                                gpu_type = primary_alias
                                gpu_count = 1
                        except (ValueError, IndexError) as parse_err:
                            self.logger.warning(f"Failed to parse GPU alias '{pci_alias}' for flavor {flavor_id}: {parse_err}")

                # 3. Yield Model
                yield InstanceModel(
                    id=server.id,
                    name=server.name,
                    status=server.status,
                    flavor_id=str(flavor_id),
                    flavor_name=str(flavor_name),
                    project_id=server.project_id,
                    project_name=proj_name,
                    availability_zone=server.availability_zone,
                    gpu_type=gpu_type,
                    gpu_count=gpu_count,
                    created_at=server.created_at
                )

            except Exception as e:
                # Robustness: Log and continue, do not crash the generator
                self.logger.error(f"Error extracting server {summary.id}: {e}")
                continue