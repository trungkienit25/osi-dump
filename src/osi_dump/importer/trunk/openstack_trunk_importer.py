import logging
from typing import Generator
from openstack.connection import Connection
from openstack.network.v2.trunk import Trunk as OSTrunk
# https://github.com/openstack/openstacksdk/blob/master/openstack/network/v2/trunk.py
from osi_dump.importer.trunk.trunk_importer import TrunkImporter
from osi_dump.model.trunk import Trunk

logger = logging.getLogger(__name__)

class OpenStackTrunkImporter(TrunkImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_trunks(self) -> Generator[Trunk, None, None]:
        logger.info(f"Importing trunks for {self.connection.auth['auth_url']}")
        try:
            for trunk in self.connection.network.trunks(all_projects=True):
                
                if not trunk.sub_ports:
                    continue

                for sub_port in trunk.sub_ports:
                    yield Trunk(
                        trunk_id=trunk.id,
                        trunk_name=trunk.name,
                        trunk_status=trunk.status,
                        project_id=trunk.project_id,
                        parent_port_id=trunk.port_id, 
                        
                        sub_port_id=sub_port.get('port_id'),
                        segmentation_type=sub_port.get('segmentation_type'),
                        segmentation_id=sub_port.get('segmentation_id'),
                    )
        except Exception as e:
            logger.error(f"Cannot fetch trunks for {self.connection.auth['auth_url']}: {e}")
            return
        
        logger.info(f"Finished importing trunks for {self.connection.auth['auth_url']}")