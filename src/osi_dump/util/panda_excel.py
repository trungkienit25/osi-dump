import pandas as pd

def expand_list_column(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        # 1. Lấy dữ liệu hàng gốc
        base_data = row.to_dict()
        
        # 2. Lấy base data và xóa nó khỏi dữ liệu gốc
        list_data = base_data.pop(column_name)

        if list_data: # Nếu danh sách không rỗng
            for item in list_data:

                # 3. Tạo một BẢN SAO của hàng gốc cho MỖI item trong danh sách
                new_row = base_data.copy()

                if isinstance(item, dict):
                    # 4. Thêm các key được mở rộng vào BẢN SAO
                    for key, value in item.items():
                        new_row[f"{column_name}.{key}"] = value
                else:
                    # Xử lý trường hợp item không phải là dict (ví dụ: danh sách chuỗi)
                    new_row[column_name] = item
                
                # 5. Thêm hàng mới (đã bao gồm dữ liệu gốc + dữ liệu mở rộng)
                rows.append(new_row)
        else:
            # Nếu danh sách aggregates rỗng, chỉ cần thêm lại hàng gốc (đã xóa cột aggregates)
            rows.append(base_data)

    return pd.DataFrame(rows)