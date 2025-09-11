import logging
from typing import Generator
from openstack.connection import Connection
from openstack.compute.v2.hypervisor import Hypervisor as OSHypervisor
from openstack.compute.v2.aggregate import Aggregate as OSAggregate
from openstack.placement.v1._proxy import Proxy as PlacementProxy
from openstack.placement.v1.resource_provider_inventory import ResourceProviderInventory

from osi_dump.importer.hypervisor.hypervisor_importer import HypervisorImporter
from osi_dump.model.hypervisor import Hypervisor
from osi_dump.api.placement import get_usage

logger = logging.getLogger(__name__)

class OpenStackHypervisorImporter(HypervisorImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_hypervisors(self) -> Generator[Hypervisor, None, None]:
        logger.info("Pre-caching aggregates...")
        try:
            aggregates = list(self.connection.list_aggregates())
        except Exception as e:
            logger.warning(f"Could not pre-cache aggregates: {e}")
            aggregates = []

        logger.info(f"Importing hypervisors for {self.connection.auth['auth_url']}")
        try:
            hypervisor_iterator = self.connection.compute.hypervisors(details=True, with_servers=True)
            for hypervisor in hypervisor_iterator:
                yield self._get_hypervisor_info(hypervisor, aggregates)
        except Exception as e:
            logger.error(f"Cannot fetch hypervisors for {self.connection.auth['auth_url']}: {e}")
            return 
            
        logger.info(f"Finished importing hypervisors for {self.connection.auth['auth_url']}")

    def _get_hypervisor_info(
        self, hypervisor: OSHypervisor, aggregates: list[OSAggregate]
    ) -> Hypervisor:
        aggregate_list, az = self._get_aggregates(hypervisor=hypervisor, all_aggregates=aggregates)

        placement_proxy: PlacementProxy = self.connection.placement
        rpi: list[ResourceProviderInventory] = []
        usage_data = {}
        
        try:
            rpi = list(
                placement_proxy.resource_provider_inventories(
                    resource_provider=hypervisor.id
                )
            )
            usage_data = get_usage(self.connection, resource_provider_id=hypervisor.id)
        except Exception as e:
            logger.warning(f"Could not get placement data for hypervisor {hypervisor.name}: {e}")

        vcpu = rpi[0] if len(rpi) > 0 else {}
        memory = rpi[1] if len(rpi) > 1 else {}
        disk = rpi[2] if len(rpi) > 2 else {}

        return Hypervisor(
            hypervisor_id=hypervisor.id,
            hypervisor_type=hypervisor.hypervisor_type,
            name=hypervisor.name,
            state=hypervisor.state,
            status=hypervisor.status,
            local_disk_size=disk.get("max_unit", 0),
            memory_size=memory.get("max_unit", 0) + memory.get("reserved", 0),
            vcpus=vcpu.get("max_unit", 0),
            vcpus_usage=usage_data.get("VCPU", 0),
            memory_usage=usage_data.get("MEMORY_MB", 0),
            local_disk_usage=usage_data.get("DISK_GB", 0),
            vm_count=len(hypervisor.servers),
            aggregates=aggregate_list,
            availability_zone=az,
        )

    def _get_aggregates(self, hypervisor: OSHypervisor, all_aggregates: list[OSAggregate]):
        aggregates_ret = []
        az = None
        for aggregate in all_aggregates:
            if hypervisor.name in aggregate.hosts:
                aggregates_ret.append(
                    {
                        "id": aggregate.id,
                        "name": aggregate.name,
                    }
                )
                if aggregate.availability_zone is not None:
                    az = aggregate.availability_zone
        
        aggregates_ret = sorted(aggregates_ret, key=lambda x: x['name'])
        return aggregates_ret, az