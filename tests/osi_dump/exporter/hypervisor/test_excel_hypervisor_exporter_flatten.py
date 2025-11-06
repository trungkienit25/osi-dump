# tests/osi_dump/exporter/hypervisor/test_excel_hypervisor_exporter_flatten.py

import pandas as pd
import numpy as np
import pytest
from unittest.mock import MagicMock
import pandas.testing as pd_testing

# Import các thành phần cần thiết để test
from osi_dump.model.hypervisor import Hypervisor
from osi_dump.exporter.hypervisor.excel_hypervisor_exporter import ExcelHypervisorExporter, _extract_sort_keys
from osi_dump import util

# --- Test 1: Kiểm tra hàm helper tách key (đã có từ trước) ---
def test_extract_sort_keys():
    """Kiểm tra logic tách tên thành prefix và suffix số."""
    assert _extract_sort_keys("compute-10") == ("compute-", 10)
    assert _extract_sort_keys("compute-2") == ("compute-", 2)
    assert _extract_sort_keys("hfx0wld01gld05") == ("hfx0wld01gld", 5)
    assert _extract_sort_keys("no-number") == ("no-number", float('inf'))
    assert _extract_sort_keys(None) == (None, float('inf'))

# --- Test 2: Kiểm tra logic Sắp xếp (Sort) VÀ Làm phẳng (Flatten) ---
@pytest.mark.usefixtures("mocker")
def test_export_hypervisors_sort_and_flatten(mocker):
    """
    Test kịch bản:
    1. Sắp xếp (sort) theo logic prefixXX.
    2. Mở rộng (flatten) cột 'aggregates' thành nhiều cột trên cùng một hàng.
    """
    
    # 1. Chuẩn bị Dữ liệu Mock
    hypervisor_list = [
        Hypervisor(
            name="compute-10",
            hypervisor_id="id-10",
            state="up", status="enabled", hypervisor_type="QEMU",
            local_disk_size=100, memory_size=1024, vcpus=10,
            vcpus_usage=1, memory_usage=100, local_disk_usage=10,
            vm_count=1,
            aggregates=[{"id": "agg-b-id", "name": "agg-b"}],
            availability_zone="az1"
        ),
        Hypervisor(
            name="no-number-compute",
            hypervisor_id="id-99",
            state="up", status="enabled", hypervisor_type="QEMU",
            local_disk_size=0, memory_size=0, vcpus=0,
            vcpus_usage=0, memory_usage=0, local_disk_usage=0,
            vm_count=0,
            aggregates=[],
            availability_zone="az2"
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
                {"id": "agg-c-id", "name": "agg-c"}
            ],
            availability_zone="az1"
        )
    ]

    def hypervisor_gen():
        yield from hypervisor_list

    mock_export_excel = mocker.patch("osi_dump.util.export_data_excel")
    exporter = ExcelHypervisorExporter(sheet_name="test-sheet", output_file="test.xlsx")
    exporter.export_hypervisors(hypervisor_gen())

    assert mock_export_excel.call_count == 1
    passed_df = mock_export_excel.call_args.kwargs['df']

    # 5. Tạo DataFrame mong đợi (Expected)
    # Sắp xếp mong đợi: compute-2, compute-10, no-number-compute
    
    expected_data = {
        'name': ['compute-2', 'compute-10', 'no-number-compute'],
        'hypervisor_id': ['id-2', 'id-10', 'id-99'],
        'availability_zone': ['az1', 'az1', 'az2'],
        
        # --- BẮT ĐẦU SỬA LỖI (Bổ sung tất cả các trường còn lại) ---
        'state': ['up', 'up', 'up'],
        'status': ['enabled', 'enabled', 'enabled'],
        'hypervisor_type': ['QEMU', 'QEMU', 'QEMU'],
        'local_disk_size': [200, 100, 0],
        'memory_size': [2048, 1024, 0],
        'vcpus': [20, 10, 0],
        'vcpus_usage': [2, 1, 0],
        'memory_usage': [200, 100, 0],
        'local_disk_usage': [20, 10, 0],
        'vm_count': [2, 1, 0],
        # --- KẾT THÚC SỬA LỖI ---
        
        'aggregates.0.id': ['agg-a-id', 'agg-b-id', np.nan],
        'aggregates.0.name': ['agg-a', 'agg-b', np.nan],
        'aggregates.1.id': ['agg-c-id', np.nan, np.nan],
        'aggregates.1.name': ['agg-c', np.nan, np.nan]
    }
    
    base_columns = [
        col for col in Hypervisor.model_fields.keys() 
        if col not in ['aggregates']
    ]
    
    agg_columns = [
        col for col in expected_data.keys() 
        if col.startswith('aggregates.')
    ]
    
    all_expected_columns = base_columns + agg_columns
    expected_df = pd.DataFrame(columns=all_expected_columns)
    
    for col, data in expected_data.items():
        expected_df[col] = data
        
    for col in base_columns:
        if col not in expected_data:
            # Chuyển đổi kiểu dữ liệu của các cột None/NaN để khớp
            expected_df[col] = pd.Series([None] * len(expected_data['name']), dtype=object)

    columns_to_test = expected_df.columns
    
    missing_cols = [col for col in columns_to_test if col not in passed_df.columns]
    assert not missing_cols, f"DataFrame kết quả bị thiếu cột: {missing_cols}"
    
    extra_cols = [
        col for col in passed_df.columns 
        if col not in columns_to_test 
        and col not in ['aggregates.0.', 'aggregates.1.']
    ]
    assert not extra_cols, f"DataFrame kết quả có cột thừa: {extra_cols}"
    
    output_df_to_test = passed_df[columns_to_test].copy()

    output_df_to_test = output_df_to_test.reindex(sorted(output_df_to_test.columns), axis=1)
    expected_df = expected_df.reindex(sorted(expected_df.columns), axis=1)
    
    pd_testing.assert_frame_equal(
        output_df_to_test.reset_index(drop=True),
        expected_df.reset_index(drop=True),
        check_like=True
    )