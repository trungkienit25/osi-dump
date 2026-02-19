from typing import Any, Generator, List
import logging
from osi_dump.core.interfaces import IResourceImporter
from osi_dump.model.hypervisor import HypervisorModel

class OpenStackHypervisorImporter(IResourceImporter):
    def __init__(self, conn: Any):
        self.conn = conn
        self.logger = logging.getLogger(__name__)

    def fetch_data(self) -> Generator[HypervisorModel, None, None]:
        self.logger.info("Phase 1 & 2: Fetching Hypervisors...")
        try:
             # Hypervisors usually don't have heavy dependencies to cache first
            hypervisors = self.conn.compute.hypervisors(details=True)
            
            for hyp in hypervisors:
                try:
                    # Robust check for placement API issues (checking aggregates often triggers it)
                    # We skip complex aggregate fetching here if it's prone to failure, 
                    # or wrap it if we were to add it.
                    
                    yield HypervisorModel(
                        id=hyp.id,
                        name=hyp.name,
                        host_ip=hyp.host_ip,
                        state=hyp.state,
                        status=hyp.status,
                        vcpus=hyp.vcpus,
                        vcpus_used=hyp.vcpus_used,
                        memory_mb=hyp.memory_mb,
                        memory_mb_used=hyp.memory_mb_used
                    )
                except Exception as e:
                    self.logger.error(f"Error processing hypervisor {hyp.name}: {e}")
                    continue
        except Exception as e:
            # Critical fallback for Placement API failure
            self.logger.critical(f"Failed to list hypervisors (Placement API issue?): {e}")
            return