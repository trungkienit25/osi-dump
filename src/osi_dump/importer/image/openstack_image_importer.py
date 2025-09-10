import logging
from typing import Generator
from openstack.connection import Connection
from openstack.image.v2.image import Image as OSImage

from osi_dump.importer.image.image_importer import ImageImporter
from osi_dump.model.image import Image

logger = logging.getLogger(__name__)

class OpenStackImageImporter(ImageImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_images(self) -> Generator[Image, None, None]:
        logger.info(f"Importing images for {self.connection.auth['auth_url']}")
        try:
            os_image_iterator = self.connection.list_images(show_all=True)
            
            for os_image in os_image_iterator:
                yield self._get_image_info(os_image)

        except Exception as e:
            logger.error(f"Cannot fetch images for {self.connection.auth['auth_url']}: {e}")
            return

        logger.info(f"Finished importing images for {self.connection.auth['auth_url']}")


    def _get_image_info(self, os_image: OSImage) -> Image:
        properties = os_image.properties or {}
        properties.pop("owner_specified.openstack.md5", None)
        properties.pop("owner_specified.openstack.sha256", None)
        properties.pop("owner_specified.openstack.object", None)
        properties.pop("stores", None)

        return Image(
            image_id=os_image.id,
            disk_format=os_image.disk_format,
            min_disk=os_image.min_disk,
            min_ram=os_image.min_ram,
            image_name=os_image.name,
            owner=os_image.owner,
            properties=properties,
            protected=os_image.is_protected,
            status=os_image.status,
            os_distro=os_image.os_distro,
            size=os_image.size,
            virtual_size=os_image.virtual_size,
            visibility=os_image.visibility,
            created_at=os_image.created_at,
            updated_at=os_image.updated_at,
        )
