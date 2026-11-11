import json
import logging
import os

from pydantic import ValidationError

import typer

import openstack
from openstack.connection import Connection

from osi_dump.model.authentication_info import AuthenticationInfo


logger = logging.getLogger(__name__)

TIMEOUT_SECOND = 30


def get_connections(file_path) -> list[Connection]:
    auths = _parse_authentication_info(file_path=file_path)

    # Enforce OpenStack Compute microversion to 2.95 via official SDK environment variable
    # to avoid upstream Nova 2.96 KeyError bug on quota-exceeded VMs
    os.environ["OS_COMPUTE_DEFAULT_MICROVERSION"] = "2.95"
    logger.info("Setting OS_COMPUTE_DEFAULT_MICROVERSION=2.95 to ensure stable Compute API communication.")

    logger.info("Getting connections")

    connections = []
    auth_urls = []

    for auth in auths:
        try:
            connection = openstack.connect(
                auth_url=auth.auth_url,
                project_name=auth.project_name,
                username=auth.username,
                password=auth.password,
                project_domain_name=auth.project_domain_name,
                user_domain_name=auth.user_domain_name,
                interface=auth.interface,
                compute_default_microversion="2.95",
            )

            connections.append(connection)
            auth_urls.append(auth.auth_url)
        except Exception as e:
            logger.warning(f"Skipping {auth.auth_url}... error: {e}")
            pass

    logger.info("Established connection success with: ")
    for auth_url in auth_urls:
        logger.info(f"{auth_url}")

    return connections


def _parse_authentication_info(file_path: str) -> list[AuthenticationInfo]:

    with open(file_path, "r") as file:
        objects = json.load(file)
        if not isinstance(objects, list) or len(objects) == 0:
            raise ValueError(
                "The JSON file must contain a list with at least one object."
            )

        try:
            ret = [AuthenticationInfo.model_validate(obj) for obj in objects]
        except ValidationError as e:
            logger.error(e.errors())
            raise typer.Exit(1)

        return ret
