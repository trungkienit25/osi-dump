import pytest
from unittest.mock import Mock, MagicMock
from openstack.exceptions import ResourceNotFound

from osi_dump.importer.trunk.openstack_trunk_importer import OpenStackTrunkImporter
from osi_dump.model.trunk import Trunk

class TestOpenStackTrunkImporter:
    @pytest.fixture
    def mock_connection(self):
        """Tạo một kết nối giả lập (mock connection)"""
        connection = MagicMock()
        # Mock object auth để tránh lỗi khi log
        connection.auth = {'auth_url': 'http://mock-openstack:5000'}
        return connection

    def test_import_trunks_success(self, mock_connection):
        """
        Test trường hợp import thành công:
        - 1 Trunk cha
        - 2 Sub-ports (VLAN 100, VLAN 200)
        """
        # 1. Chuẩn bị dữ liệu giả lập (Mock Data)
        mock_sub_port_1 = {
            'port_id': 'sub-port-uuid-1',
            'segmentation_type': 'vlan',
            'segmentation_id': 100
        }
        mock_sub_port_2 = {
            'port_id': 'sub-port-uuid-2',
            'segmentation_type': 'vlan',
            'segmentation_id': 200
        }

        # Mock đối tượng Trunk trả về từ SDK
        mock_trunk = Mock()
        mock_trunk.id = "trunk-uuid-1"
        mock_trunk.name = "test-trunk"
        mock_trunk.status = "ACTIVE"
        mock_trunk.project_id = "project-uuid"
        mock_trunk.port_id = "parent-port-uuid"
        mock_trunk.sub_ports = [mock_sub_port_1, mock_sub_port_2]

        # Giả lập hành vi của connection.network.trunks()
        mock_connection.network.trunks.return_value = [mock_trunk]

        # 2. Thực thi Importer
        importer = OpenStackTrunkImporter(mock_connection)
        results = list(importer.import_trunks())

        # 3. Kiểm tra kết quả (Assert)
        assert len(results) == 2  # Phải tách ra làm 2 dòng (vì có 2 sub-ports)
        
        # Kiểm tra dòng 1 (VLAN 100)
        assert isinstance(results[0], Trunk)
        assert results[0].trunk_id == "trunk-uuid-1"
        assert results[0].sub_port_id == "sub-port-uuid-1"
        assert results[0].segmentation_id == 100

        # Kiểm tra dòng 2 (VLAN 200)
        assert results[1].segmentation_id == 200
        assert results[1].parent_port_id == "parent-port-uuid"

    def test_import_trunks_no_subports(self, mock_connection):
        """
        Test trường hợp Trunk không có sub-port nào.
        Importer nên bỏ qua trunk này (trả về list rỗng).
        """
        mock_trunk = Mock()
        mock_trunk.id = "trunk-empty"
        mock_trunk.sub_ports = [] # Danh sách rỗng

        mock_connection.network.trunks.return_value = [mock_trunk]

        importer = OpenStackTrunkImporter(mock_connection)
        results = list(importer.import_trunks())

        assert len(results) == 0

    def test_import_trunks_api_error_404(self, mock_connection):
        """
        Test trường hợp API bị lỗi (ví dụ: môi trường không hỗ trợ Trunk).
        Importer phải bắt lỗi và trả về list rỗng, KHÔNG được crash.
        """
        # Giả lập lỗi ResourceNotFound (404) khi gọi API
        mock_connection.network.trunks.side_effect = ResourceNotFound("404 Not Found")

        importer = OpenStackTrunkImporter(mock_connection)
        results = list(importer.import_trunks())

        # Assert: Kết quả trả về là list rỗng và không văng Exception
        assert len(results) == 0