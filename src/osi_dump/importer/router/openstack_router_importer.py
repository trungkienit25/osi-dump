import logging
from typing import Generator
from openstack.connection import Connection
from openstack.network.v2.router import Router as OSRouter

from osi_dump.importer.router.router_importer import RouterImporter
from osi_dump.model.router import Router

logger = logging.getLogger(__name__)

class OpenStackRouterImporter(RouterImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_routers(self) -> Generator[Router, None, None]:
        logger.info(f"Importing routers for {self.connection.auth['auth_url']}")
        try:
            router_iterator = self.connection.network.routers()

            for osrouter in router_iterator:
                yield self._get_router_info(osrouter)

        except Exception as e:
            logger.error(f"Cannot fetch routers for {self.connection.auth['auth_url']}: {e}")
            return 

        logger.info(f"Finished importing routers for {self.connection.auth['auth_url']}")


    def _get_router_info(self, router: OSRouter) -> Router:
        external_net_id = None
        if router.external_gateway_info:
            external_net_id = router.external_gateway_info.get("network_id")

        external_net_ip = None
        if router.external_gateway_info and router.external_gateway_info.get("external_fixed_ips"):
            try:
                external_net_ip = router.external_gateway_info["external_fixed_ips"][0].get("ip_address")
            except (IndexError, KeyError) as e:
                logger.warning(f"Could not get external net ip for router {router.id}: {e}")

        return Router(
            router_id=router.id,
            name=router.name,
            external_net_id=external_net_id,
            external_net_ip=external_net_ip,
            status=router.status,
            admin_state=router.is_admin_state_up,
            project_id=router.project_id,
            created_at=router.created_at,
            updated_at=router.updated_at,
        )
