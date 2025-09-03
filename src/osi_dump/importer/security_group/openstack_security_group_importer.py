import logging
import concurrent.futures
from openstack.connection import Connection
from openstack.network.v2.security_group import SecurityGroup as OSSecurityGroup

from osi_dump.importer.security_group.security_group_importer import SecurityGroupImporter
from osi_dump.model.security_group import SecurityGroup, SecurityGroupRule

logger = logging.getLogger(__name__)

class OpenStackSecurityGroupImporter(SecurityGroupImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_security_groups(self) -> list[SecurityGroup]:
        logger.info(f"Importing security groups for {self.connection.auth['auth_url']}")
        try:
            os_sec_groups = list(self.connection.network.security_groups())
        except Exception as e:
            raise Exception(f"Cannot fetch security groups for {self.connection.auth['auth_url']}: {e}") from e

        sec_groups: list[SecurityGroup] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._get_sec_group_info, sg) for sg in os_sec_groups]
            for future in concurrent.futures.as_completed(futures):
                sec_groups.append(future.result())

        logger.info(f"Imported security groups for {self.connection.auth['auth_url']}")
        return sec_groups

    def _get_sec_group_info(self, os_sec_group: OSSecurityGroup) -> SecurityGroup:
        rules = []
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

        return SecurityGroup(
            security_group_id=os_sec_group.id,
            name=os_sec_group.name,
            project_id=os_sec_group.project_id,
            description=os_sec_group.description,
            rules=rules
        )