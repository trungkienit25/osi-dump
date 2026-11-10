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

    def test_import_instances_auto_downgrades_to_2_95_on_500_keyerror(self, mock_connection, monkeypatch):
        mock_connection.identity.projects.return_value = []
        mock_connection.identity.domains.return_value = []
        mock_connection.compute.flavors.return_value = []

        # compute.servers() raises 500 Server Error KeyError (like Nova 2.96 upstream bug)
        mock_connection.compute.servers.side_effect = Exception("500 Server Error: <class 'KeyError'> 'RequestSpec'")

        recovered_server = Mock(spec=Server)
        recovered_server.id = "recovered-uuid"
        recovered_server.name = "recovered-vm"
        recovered_server.project_id = None
        recovered_server.status = "ACTIVE"
        recovered_server.hypervisor_hostname = "comp-01"
        recovered_server.user_id = "user-111"
        recovered_server.created_at = "2026-09-08T05:00:00Z"
        recovered_server.updated_at = "2026-09-08T06:00:00Z"
        recovered_server.flavor = {"id": "f-1", "ram": 2048, "vcpus": 2}
        recovered_server.image = None
        recovered_server.addresses = {}

        # Monkeypatch Server.list to verify it gets called with microversion="2.95"
        server_list_called = []
        def mock_server_list(session, **kwargs):
            server_list_called.append(kwargs)
            return iter([recovered_server])

        monkeypatch.setattr(Server, "list", mock_server_list)

        importer = OpenStackInstanceImporter(mock_connection)
        instances = list(importer.import_instances())

        # Verify fallback to microversion 2.95 was invoked and instances recovered
        assert len(server_list_called) == 1
        assert server_list_called[0].get("microversion") == "2.95"
        assert len(instances) == 1
        assert instances[0].instance_id == "recovered-uuid"


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

