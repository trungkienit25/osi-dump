# tests/osi_dump/exporter/hypervisor/test_excel_hypervisor_exporter.py

import pandas as pd
import pytest
from unittest.mock import MagicMock
import pandas.testing as pd_testing

# Import các thành phần cần thiết để test
from osi_dump.model.hypervisor import Hypervisor
from osi_dump.exporter.hypervisor.excel_hypervisor_exporter import ExcelHypervisorExporter, _extract_sort_keys
from osi_dump import util

# --- Test 1: Kiểm tra hàm helper tách key ---
def test_extract_sort_keys():
    """Kiểm tra logic tách tên thành prefix và suffix số."""
    assert _extract_sort_keys("compute-10") == ("compute-", 10)
    assert _extract_sort_keys("compute-2") == ("compute-", 2)
    assert _extract_sort_keys("hfx0wld01gld05") == ("hfx0wld01gld", 5)
    assert _extract_sort_keys("no-number") == ("no-number", float('inf'))
    assert _extract_sort_keys(None) == (None, float('inf')) # Xử lý giá trị None

# --- Test 2: Kiểm tra lỗi logic Sắp xếp & Mở rộng ---
def test_export_hypervisors_sort_and_expand_order(mocker):
    """
    Test kịch bản lỗi: Sắp xếp (sort) phải được thực hiện
    SAU KHI mở rộng (expand) cột 'aggregates' để đảm bảo dữ liệu
    không bị ánh xạ sai (mismatched).
    """
    
    # 1. Chuẩn bị Dữ liệu Mock
    # Danh sách cố tình không theo thứ tự sắp xếp mong muốn
    # (compute-10 đứng trước compute-2)
    hypervisor_list = [
        Hypervisor(
            name="compute-10",
            hypervisor_id="id-10",
            state="up", status="enabled", hypervisor_type="QEMU",
            local_disk_size=100, memory_size=1024, vcpus=10,
            vcpus_usage=1, memory_usage=100, local_disk_usage=10,
            vm_count=1,
            aggregates=[
                {"id": "agg-b-id", "name": "agg-b"}
            ],
            availability_zone="az1"
        ),
        Hypervisor(
            name="compute-2",
            hypervisor_id="id-2",
            state="up", status="enabled", hypervisor_type="QEMU",
            local_disk_size=200, memory_size=2048, vcpus=20,
            vcpus_usage=2, memory_usage=200, local_disk_usage=20,
            vm_count=2,
            aggregates=[
                {"id": "agg-a-id", "name": "agg-a"},
                {"id": "agg-c-id", "name": "agg-c"} # Test trường hợp mở rộng thành 2 dòng
            ],
            availability_zone="az1"
        )
    ]

    # Tạo generator từ danh sách
    def hypervisor_gen():
        yield from hypervisor_list

    # 2. Mock hàm ghi file Excel
    # Chúng ta không muốn test việc ghi file, chỉ muốn bắt
    # DataFrame cuối cùng được truyền vào nó.
    mock_export_excel = mocker.patch("osi_dump.util.export_data_excel")

    # 3. Chạy hàm cần test
    exporter = ExcelHypervisorExporter(sheet_name="test-sheet", output_file="test.xlsx")
    exporter.export_hypervisors(hypervisor_gen())

    # 4. Kiểm tra kết quả
    
    # Đảm bảo hàm export_data_excel được gọi 1 lần
    assert mock_export_excel.call_count == 1
    
    # Lấy DataFrame đã được xử lý mà hàm đã truyền cho export_data_excel
    # 'df' là một keyword argument
    passed_df = mock_export_excel.call_args[1]['df']

    # 5. Tạo DataFrame mong đợi (Expected)
    # Kết quả đúng là:
    # - 'compute-2' phải lên đầu (đã sắp xếp)
    # - 'compute-2' phải được mở rộng thành 2 dòng
    # - 2 dòng 'compute-2' phải giữ đúng aggregates của nó ('agg-a' và 'agg-c')
    # - 'compute-10' ở cuối và giữ đúng aggregate 'agg-b'
    
    expected_data = {
        'name': ['compute-2', 'compute-2', 'compute-10'],
        'hypervisor_id': ['id-2', 'id-2', 'id-10'],
        'state': ['up', 'up', 'up'],
        'status': ['enabled', 'enabled', 'enabled'],
        'hypervisor_type': ['QEMU', 'QEMU', 'QEMU'],
        'local_disk_size': [200, 200, 100],
        'memory_size': [2048, 2048, 1024],
        'vcpus': [20, 20, 10],
        'vcpus_usage': [2, 2, 1],
        'memory_usage': [200, 200, 100],
        'local_disk_usage': [20, 20, 10],
        'vm_count': [2, 2, 1],
        'availability_zone': ['az1', 'az1', 'az1'],
        'aggregates.id': ['agg-a-id', 'agg-c-id', 'agg-b-id'],
        'aggregates.name': ['agg-a', 'agg-c', 'agg-b']
    }
    expected_df = pd.DataFrame(expected_data)

    # 6. So sánh
    # Chúng ta chỉ so sánh các cột có trong expected_df
    columns_to_test = expected_df.columns
    
    # Đảm bảo DataFrame kết quả có đúng các cột này
    assert all(col in passed_df.columns for col in columns_to_test)
    
    output_df_to_test = passed_df[columns_to_test]
    
    # Sử dụng pandas.testing để so sánh,
    # reset_index(drop=True) để bỏ qua các vấn đề về index sau khi sort
    pd_testing.assert_frame_equal(
        output_df_to_test.reset_index(drop=True),
        expected_df.reset_index(drop=True)
    )