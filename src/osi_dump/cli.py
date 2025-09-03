import logging

import os

from pathlib import Path

import typer

from typing_extensions import Annotated

from osi_dump.batch_handler.external_port_batch_handler import ExternalPortBatchHandler
from osi_dump.batch_handler.load_balancer_batch_handler import LoadBalancerBatchHandler
from osi_dump.batch_handler.role_assignment_batch_handler import (
    RoleAssignmentBatchHandler,
)
from osi_dump.batch_handler.router_batch_handler import RouterBatchHandler

app = typer.Typer()


from osi_dump.batch_handler.flavor_batch_handler import FlavorBatchHandler
from osi_dump.batch_handler.network_batch_handler import NetworkBatchHandler

from osi_dump.batch_handler.image_batch_handler import ImageBatchHandler
from osi_dump.batch_handler.volume_batch_handler import VolumeBatchHandler
from osi_dump.batch_handler.security_group_batch_handler import SecurityGroupBatchHandler
from osi_dump.os_connection.get_connections import get_connections


from osi_dump.batch_handler import (
    InstanceBatchHandler,
    ProjectBatchHandler,
    HypervisorBatchHandler,
    FloatingIPBatchHandler,
)


from osi_dump.importer.external_port.openstack_external_port_importer import (
    OpenStackExternalPortImporter,
)


from osi_dump import util


def _instance(connections, output_path: str):
    instance_batch_handler = InstanceBatchHandler()

    instance_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    instance_batch_handler.process()


def _floating_ip(connections, output_path: str):
    floating_ip_batch_handler = FloatingIPBatchHandler()

    floating_ip_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    floating_ip_batch_handler.process()


def _volume(connections, output_path: str):
    volume_batch_handler = VolumeBatchHandler()

    volume_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    volume_batch_handler.process()


def _project(connections, output_path: str):
    project_batch_handler = ProjectBatchHandler()

    project_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    project_batch_handler.process()


def _hypervisor(connections, output_path: str):
    hypervisor_batch_handler = HypervisorBatchHandler()

    hypervisor_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    hypervisor_batch_handler.process()


def _image(connections, output_path: str):
    image_batch_handler = ImageBatchHandler()

    image_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    image_batch_handler.process()


def _flavor(connections, output_path: str):
    flavor_batch_handler = FlavorBatchHandler()

    flavor_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    flavor_batch_handler.process()


def _role_assignment(connections, output_path: str):
    _role_assignment_batch_handler = RoleAssignmentBatchHandler()

    _role_assignment_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    _role_assignment_batch_handler.process()


def _load_balancer(connections, output_path: str):
    _load_balancer_batch_handler = LoadBalancerBatchHandler()

    _load_balancer_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    _load_balancer_batch_handler.process()


def _router(connections, output_path: str):
    _router_batch_handler = RouterBatchHandler()

    _router_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    _router_batch_handler.process()


def _external_port(connections, output_path: str):
    _external_batch_handler = ExternalPortBatchHandler()

    _external_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    _external_batch_handler.process()

def _network(connections, output_path: str):
    _network_batch_handler = NetworkBatchHandler()

    _network_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )

    _network_batch_handler.process()

def inner_main(file_path: str, output_path: str):

    logger = logging.getLogger(__name__)

    connections = get_connections(file_path=file_path)

    _instance(connections=connections, output_path=output_path)

    _floating_ip(connections=connections, output_path=output_path)

    _volume(connections=connections, output_path=output_path)

    _hypervisor(connections=connections, output_path=output_path)

    _project(connections=connections, output_path=output_path)

    _image(connections=connections, output_path=output_path)

    _flavor(connections=connections, output_path=output_path)

    _role_assignment(connections=connections, output_path=output_path)

    _load_balancer(connections=connections, output_path=output_path)

    _router(connections=connections, output_path=output_path)

    _external_port(connections=connections, output_path=output_path)

    _network(connections=connections, output_path=output_path)

    _security_group(connections=connections, output_path=output_path) 

    util.excel_autosize_column(output_path)

    util.excel_sort_sheet(output_path)

    logger.info(
        f"Exported OpenStack information to file: {os.path.abspath(output_path)}"
    )

def _security_group(connections, output_path: str):
    sec_group_batch_handler = SecurityGroupBatchHandler()
    sec_group_batch_handler.add_importer_exporter_from_openstack_connections(
        connections, output_file=output_path
    )
    sec_group_batch_handler.process()


def main(
    file_path: Annotated[
        Path,
        typer.Argument(
            help=(
                """
            Path of the file containing OpenStack authentication information.

            The expected JSON file format is as follows:

\b
[
    {
	"auth_url": "string",
	"project_name": "string",
	"username": "string",
	"password": "string",
	"user_domain_name": "string",
	"project_domain_name": "string"
    }
]
            """
            )
        ),
    ],
    output_path: Annotated[
        Path,
        typer.Argument(
            help="""
\b
Path of the output file, will override if file already exists
             
                """
        ),
    ] = "output.xlsx",
):
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Suppress pool limit warning will investigate later
    logging.getLogger("urllib3").propagate = False

    logger = logging.getLogger(__name__)

    if util.validate_dir_path(file_path=output_path) is False:
        logger.error(f"Invalid path: {output_path}, folder does not exist.")
        raise typer.Exit(1)

    inner_main(file_path=file_path, output_path=output_path)


app.command()(main)

if __name__ == "__main__":
    app()
