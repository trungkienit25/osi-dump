import logging
from typing import Generator
from openstack.connection import Connection
from openstack.compute.v2.flavor import Flavor as OSFlavor

from osi_dump.importer.flavor.flavor_importer import FlavorImporter
from osi_dump.model.flavor import Flavor

logger = logging.getLogger(__name__)

class OpenStackFlavorImporter(FlavorImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_flavors(self) -> Generator[Flavor, None, None]:
        logger.info(f"Importing flavors for {self.connection.auth['auth_url']}")
        try:
            flavor_iterator = self.connection.list_flavors()

            for osflavor in flavor_iterator:
                yield self._get_flavor_info(osflavor)

        except Exception as e:
            logger.error(f"Cannot fetch flavors for {self.connection.auth['auth_url']}: {e}")
            return 

        logger.info(f"Finished importing flavors for {self.connection.auth['auth_url']}")

    def _get_flavor_info(self, flavor: OSFlavor) -> Flavor:

        swap_val = flavor.swap if flavor.swap else None

        return Flavor(
            flavor_id=flavor.id,
            flavor_name=flavor.name,
            ram=flavor.ram,
            vcpus=flavor.vcpus,
            disk=flavor.disk,
            swap=swap_val,
            public=flavor.is_public,
            properties=flavor.extra_specs,
        )
