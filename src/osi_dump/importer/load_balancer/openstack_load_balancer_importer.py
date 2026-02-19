from typing import Any, Generator, Dict
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.load_balancer.py import LoadBalancerModel

class OpenStackLoadBalancerImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[LoadBalancerModel, None, None]:
        # Phase 1: Cache Projects
        project_map: Dict[str, str] = {}
        try:
            for project in self.conn.identity.projects():
                project_map[project.id] = project.name
        except Exception:
            pass

        # Phase 2: Fetch LBs
        try:
            # Need to check if Octavia service is available
            if not getattr(self.conn, 'load_balancer', None):
                self.logger.warning("Load Balancer service not available.")
                return

            lbs = self.conn.load_balancer.load_balancers()
            for lb in lbs:
                try:
                    yield LoadBalancerModel(
                        id=lb.id,
                        name=lb.name,
                        provisioning_status=lb.provisioning_status,
                        operating_status=lb.operating_status,
                        vip_address=lb.vip_address,
                        project_id=lb.project_id,
                        project_name=project_map.get(lb.project_id),
                        created_at=lb.created_at
                    )
                except Exception as e:
                    self.logger.error(f"Error processing lb {lb.id}: {e}")
        except Exception as e:
            self.logger.critical(f"Failed to list load balancers: {e}")
