import logging
from typing import Generator
from openstack.connection import Connection
from openstack.identity.v3.project import Project as OSProject
from openstack.load_balancer.v2.load_balancer import LoadBalancer as OSLoadBalancer

from osi_dump.importer.project.project_importer import ProjectImporter
from osi_dump.model.project import Project
import osi_dump.api.octavia as octavia_api

logger = logging.getLogger(__name__)

class OpenStackProjectImporter(ProjectImporter):
    def __init__(self, connection: Connection):
        self.connection = connection

    def import_projects(self) -> Generator[Project, None, None]:
        project_lb_dict = {}
        logger.info(f"Pre-caching load balancers for project count on {self.connection.auth['auth_url']}")
        try:
            osload_balancers = octavia_api.get_load_balancers(connection=self.connection)
            if osload_balancers:
                for lb in osload_balancers:
                    project_id = lb.get("project_id")
                    if project_id:
                        project_lb_dict[project_id] = project_lb_dict.get(project_id, 0) + 1
        except Exception as e:
            logger.warning(f"Could not pre-cache load balancers for project count: {e}")

        logger.info(f"Importing projects for {self.connection.auth['auth_url']}")
        try:
            project_iterator = self.connection.identity.projects()
            for project in project_iterator:
                yield self._get_project_info(project, project_lb_dict)
        except Exception as e:
            logger.error(f"Cannot fetch projects for {self.connection.auth['auth_url']}: {e}")
            return 
            
        logger.info(f"Finished importing projects for {self.connection.auth['auth_url']}")

    def _get_project_info(self, project: OSProject, project_lb_dict: dict) -> Project:
        usage_instance, quota_instance = None, None
        usage_ram, quota_ram = None, None
        usage_vcpu, quota_vcpu = None, None
        usage_volume, quota_volume = None, None
        usage_snapshot, quota_snapshot = None, None
        usage_storage, quota_storage = None, None

        try:
            compute_quotas = self.connection.compute.get_quota_set(project.id, usage=True)
            if compute_quotas and compute_quotas.usage:
                usage_instance = compute_quotas.usage.get("instances")
                quota_instance = compute_quotas.instances
                usage_ram = compute_quotas.usage.get("ram")
                quota_ram = compute_quotas.ram
                usage_vcpu = compute_quotas.usage.get("cores")
                quota_vcpu = compute_quotas.cores
        except Exception as e:
            logger.warning(f"Get compute quotas failed for {project.id} error: {e}")

        # Lấy thông tin storage quotas
        try:
            storage_quotas = self.connection.block_storage.get_quota_set(project.id, usage=True)
            if storage_quotas and storage_quotas.usage:
                usage_volume = storage_quotas.usage.get("volumes")
                quota_volume = storage_quotas.volumes
                usage_snapshot = storage_quotas.usage.get("snapshots")
                quota_snapshot = storage_quotas.snapshots
                usage_storage = storage_quotas.usage.get("gigabytes")
                quota_storage = storage_quotas.gigabytes
        except Exception as e:
            logger.warning(f"Get storage quotas failed for {project.id} error: {e}")

        domain_name = None
        try:
            domain = self.connection.identity.get_domain(project.domain_id)
            domain_name = domain.name
        except Exception as e:
            logger.warning(f"Get domain failed for {project.domain_id} error: {e}")

        lb_count = project_lb_dict.get(project.id)

        return Project(
            project_id=project.id,
            project_name=project.name,
            domain_id=project.domain_id,
            domain_name=domain_name,
            enabled=project.is_enabled,
            parent_id=project.parent_id,
            usage_instance=usage_instance, 
            quota_instance=quota_instance,
            usage_ram=usage_ram,
            quota_ram=quota_ram, 
            usage_vcpu=usage_vcpu,
            quota_vcpu=quota_vcpu,
            usage_volume=usage_volume,
            quota_volume=quota_volume,
            usage_snapshot=usage_snapshot,
            quota_snapshot=quota_snapshot,
            usage_storage=usage_storage,
            quota_storage=quota_storage,
            load_balancer_count=lb_count
        )