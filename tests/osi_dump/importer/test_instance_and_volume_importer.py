import pytest
from unittest.mock import MagicMock, Mock
from openstack.compute.v2.server import Server
from openstack.identity.v3.project import Project
from openstack.identity.v3.domain import Domain
from openstack.compute.v2.flavor import Flavor

from osi_dump.importer.instance.openstack_instance_importer import OpenStackInstanceImporter
from osi_dump.importer.volume.openstack_volume_importer import OpenStackVolumeImporter
from osi_dump.model.instance import Instance
from osi_dump.model.volume import Volume


class TestOpenStackInstanceImporter:
    @pytest.fixture
    def mock_connection(self):
        connection = MagicMock()
        connection.auth = {"auth_url": "https://test-openstack.local:5000"}
        return connection

    def test_pre_cache_and_import_instances_success(self, mock_connection):
        # Setup mock projects, domains, flavors
        mock_project = Mock(spec=Project)
        mock_project.id = "proj-123"
        mock_project.name = "My-Project"
        mock_project.domain_id = "dom-456"

        mock_domain = Mock(spec=Domain)
        mock_domain.id = "dom-456"
        mock_domain.name = "Default-Domain"

        mock_flavor = Mock(spec=Flavor)
        mock_flavor.id = "flavor-789"
        mock_flavor.name = "m1.large"
        mock_flavor.extra_specs = {"pci_passthrough:alias": "V100:2"}

        mock_connection.identity.projects.return_value = [mock_project]
        mock_connection.identity.domains.return_value = [mock_domain]
        mock_connection.compute.flavors.return_value = [mock_flavor]

        # Setup mock servers with special characters and quotes in name
        mock_server_1 = Mock(spec=Server)
        mock_server_1.id = "server-uuid-1"
        mock_server_1.name = 'VM "Special" Name \\ with \\ slashes'
        mock_server_1.project_id = "proj-123"
        mock_server_1.status = "ACTIVE"
        mock_server_1.hypervisor_hostname = "compute-01"
        mock_server_1.user_id = "user-111"
        mock_server_1.created_at = "2026-09-08T05:00:00Z"
        mock_server_1.updated_at = "2026-09-08T06:00:00Z"
        mock_server_1.flavor = {"id": "flavor-789", "ram": 8192, "vcpus": 4}
        mock_server_1.image = {"id": "img-999"}
        mock_server_1.addresses = {
            "internal-net": [
                {"OS-EXT-IPS:type": "fixed", "addr": "10.0.0.5"},
                {"OS-EXT-IPS:type": "floating", "addr": "103.20.5.10"},
            ]
        }

        mock_connection.compute.servers.return_value = [mock_server_1]

        importer = OpenStackInstanceImporter(mock_connection)
        instances = list(importer.import_instances())

        assert len(instances) == 1
        inst = instances[0]
        assert isinstance(inst, Instance)
        assert inst.instance_id == "server-uuid-1"
        assert inst.instance_name == 'VM "Special" Name \\ with \\ slashes'
        assert inst.project_name == "My-Project"
        assert inst.domain_name == "Default-Domain"
        assert inst.ram == 8192
        assert inst.vcpus == 4
        assert inst.vgpus == 2
        assert inst.vgpu_type == "V100"
        assert inst.private_v4_ips == ["10.0.0.5"]
        assert inst.floating_ip == "103.20.5.10"

        # Verify N+1 prevention: get_project / get_domain were NOT called individually
        assert mock_connection.identity.get_project.call_count == 0
        assert mock_connection.identity.get_domain.call_count == 0

    def test_import_instances_handles_server_errors_gracefully(self, mock_connection):
        mock_connection.identity.projects.return_value = []
        mock_connection.identity.domains.return_value = []
        mock_connection.compute.flavors.return_value = []

        # Server that throws error or has bad attributes
        bad_server = Mock(spec=Server)
        bad_server.id = "bad-uuid"
        bad_server.name = "bad-vm"
        # Accessing flavor raises exception
        type(bad_server).flavor = property(Mock(side_effect=Exception("Corrupt data")))

        good_server = Mock(spec=Server)
        good_server.id = "good-uuid"
        good_server.name = "good-vm"
        good_server.project_id = None
        good_server.status = "SHUTOFF"
        good_server.hypervisor_hostname = "comp-02"
        good_server.user_id = "user-222"
        good_server.created_at = "2026-09-08T05:00:00Z"
        good_server.updated_at = "2026-09-08T06:00:00Z"
        good_server.flavor = {"id": "f-1", "ram": 1024, "vcpus": 1}
        good_server.image = None
        good_server.addresses = {}

        mock_connection.compute.servers.return_value = [bad_server, good_server]

        importer = OpenStackInstanceImporter(mock_connection)
        instances = list(importer.import_instances())

        # Bad server should be skipped without crashing the entire batch
        assert len(instances) == 1
        assert instances[0].instance_id == "good-uuid"

    def test_import_instances_auto_downgrades_to_2_95_on_500_keyerror(self, mock_connection):
        mock_connection.identity.projects.return_value = []
        mock_connection.identity.domains.return_value = []
        mock_connection.compute.flavors.return_value = []

        # Simulate page 1 success with 2 servers, page 2 500 Server Error under default microversion,
        # and successful recovery of page 2 under microversion 2.95
        page1_resp = Mock()
        page1_resp.status_code = 200
        page1_resp.json.return_value = {
            "servers": [
                {
                    "id": "vm-page1-1",
                    "name": "vm-1",
                    "status": "ACTIVE",
                    "hypervisor_hostname": "comp-1",
                    "flavor": {"id": "f1", "ram": 1024, "vcpus": 1},
                    "addresses": {},
                },
                {
                    "id": "vm-page1-2",
                    "name": "vm-2",
                    "status": "ACTIVE",
                    "hypervisor_hostname": "comp-1",
                    "flavor": {"id": "f1", "ram": 1024, "vcpus": 1},
                    "addresses": {},
                },
            ]
        }

        page2_fail_resp = Mock()
        page2_fail_resp.status_code = 500
        page2_fail_resp.text = "Internal Server Error: <class 'KeyError'>"

        page2_fallback_resp = Mock()
        page2_fallback_resp.status_code = 200
        page2_fallback_resp.json.return_value = {
            "servers": [
                {
                    "id": "vm-page2-recovered",
                    "name": "vm-err",
                    "status": "ERROR",
                    "hypervisor_hostname": None,
                    "flavor": {"id": "f1", "ram": 1024, "vcpus": 1},
                    "addresses": {},
                }
            ]
        }

        def mock_compute_get(url, params=None, microversion=None):
            params = params or {}
            limit = params.get("limit", 1000)
            marker = params.get("marker")
            if marker is None:
                if limit == 1000:
                    p1_servers = [{"id": f"vm-p1-{i}", "name": f"vm-{i}", "status": "ACTIVE", "hypervisor_hostname": "c1", "flavor": {}, "addresses": {}} for i in range(limit)]
                    return Mock(status_code=200, json=lambda: {"servers": p1_servers})
            if marker == "vm-p1-999":
                # Page 2 bulk query fails with 500
                if limit == 1000:
                    return page2_fail_resp
                # In isolation mode (limit=1), returns the recovered server
                if limit == 1:
                    return page2_fallback_resp
            return Mock(status_code=200, json=lambda: {"servers": []})

        mock_connection.compute.get.side_effect = mock_compute_get

        importer = OpenStackInstanceImporter(mock_connection)
        instances = list(importer.import_instances())

        # Should retrieve 1000 servers from page 1 AND the recovered server from page 2
        assert len(instances) == 1001
        assert instances[-1].instance_id == "vm-page2-recovered"


class TestOpenStackVolumeImporter:
    @pytest.fixture
    def mock_connection(self):
        connection = MagicMock()
        connection.auth = {"auth_url": "https://test-openstack.local:5000"}
        return connection

    def test_pre_cache_snapshots_and_import_volume(self, mock_connection):
        # Mock pre-cached snapshots
        mock_snap_1 = Mock()
        mock_snap_1.id = "snap-001"
        mock_snap_1.volume_id = "vol-123"

        mock_connection.block_storage.snapshots.return_value = [mock_snap_1]

        # Mock volume
        mock_volume = Mock()
        mock_volume.id = "vol-123"
        mock_volume.name = 'Volume "Special" / Name'
        mock_volume.project_id = "proj-123"
        mock_volume.user_id = "user-111"
        mock_volume.status = "in-use"
        mock_volume.volume_type = "SSD"
        mock_volume.size = 100
        mock_volume.host = "storage-01"
        mock_volume.volume_image_metadata = '{"image_name": "Ubuntu 22.04"}'
        mock_volume.attachments = [{"server_id": "server-uuid-1"}]
        mock_volume.created_at = "2026-09-08T05:00:00Z"
        mock_volume.updated_at = "2026-09-08T06:00:00Z"

        mock_connection.block_storage.volumes.return_value = [mock_volume]

        importer = OpenStackVolumeImporter(mock_connection)
        volumes = list(importer.import_volumes())

        assert len(volumes) == 1
        vol = volumes[0]
        assert isinstance(vol, Volume)
        assert vol.volume_id == "vol-123"
        assert vol.volume_name == 'Volume "Special" / Name'
        assert vol.snapshots == ["snap-001"]
        assert vol.image_metadata == {"image_name": "Ubuntu 22.04"}
        assert vol.attachments == ["server-uuid-1"]

