import logging
from typing import Generator
from openstack.connection import Connection
from openstack.network.v2.security_group import SecurityGroup as OSSecurityGroup

from osi_dump.importer.security_group.security_group_importer import SecurityGroupImporter
from osi_dump.model.security_group import SecurityGroup, SecurityGroupRule

logger = logging.getLogger(__name__)

class OpenStackSecurityGroupImporter(SecurityGroupImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_security_groups(self) -> Generator[SecurityGroup, None, None]:
        logger.info(f"Importing security groups for {self.connection.auth['auth_url']}")
        try:
            os_sec_groups_iterator = self.connection.network.security_groups()

            for os_sec_group in os_sec_groups_iterator:
                yield self._get_sec_group_info(os_sec_group)

        except Exception as e:
            logger.error(f"Cannot fetch security groups for {self.connection.auth['auth_url']}: {e}")
            return 

        logger.info(f"Finished importing security groups for {self.connection.auth['auth_url']}")


    def _get_sec_group_info(self, os_sec_group: OSSecurityGroup) -> SecurityGroup:
        rules = []
        if hasattr(os_sec_group, 'security_group_rules'):
            for rule in os_sec_group.security_group_rules:
                port_range = None
                if rule.get('port_range_min') is not None and rule.get('port_range_max') is not None:
                    port_range = f"{rule['port_range_min']}-{rule['port_range_max']}"

                rules.append(SecurityGroupRule(
                    rule_id=rule['id'],
                    direction=rule['direction'],
                    protocol=rule.get('protocol'),
                    ethertype=rule['ethertype'],
                    port_range=port_range,
                    remote_ip_prefix=rule.get('remote_ip_prefix'),
                    remote_group_id=rule.get('remote_group_id')
                ))
        
        return SecurityGroup(
            security_group_id=os_sec_group.id,
            name=os_sec_group.name,
            project_id=os_sec_group.project_id,
            description=os_sec_group.description,
            rules=rules
        )