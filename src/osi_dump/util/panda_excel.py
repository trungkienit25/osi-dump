import pandas as pd

def expand_list_column(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Mở rộng một cột chứa danh sách các dictionary thành CÁC CỘT MỚI
    trên CÙNG MỘT HÀNG (ví dụ: aggregates.0.id, aggregates.1.id).
    Không nhân bản hàng.
    """
    
    df = df.copy()

    if column_name not in df.columns or df[column_name].isnull().all():
        return df
    
    list_series = df[column_name].apply(lambda x: x if isinstance(x, list) else [])
    
    if list_series.apply(len).max() == 0:
        return df.drop(column_name, axis=1, errors='ignore')

    max_len = int(list_series.apply(len).max())

    expanded_df = pd.DataFrame(
        list_series.apply(lambda x: x + [{}] * (max_len - len(x))).tolist(),
        index=df.index,
    )

    expanded_df = pd.json_normalize(expanded_df.to_dict(orient="records"))

    # Thêm tiền tố 'column_name.' vào tên các cột mới
    expanded_df.columns = [f"{column_name}.{col}" for col in expanded_df.columns]

    # Xóa cột gốc (chứa list) và nối (join) các cột mới vào
    df = df.drop(column_name, axis=1).join(expanded_df)

    return df