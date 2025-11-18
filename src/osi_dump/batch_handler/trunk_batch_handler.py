import logging
from osi_dump.importer.trunk.openstack_trunk_importer import OpenStackTrunkImporter
from osi_dump.exporter.trunk.excel_trunk_exporter import ExcelTrunkExporter
from osi_dump.util.extract_hostname import extract_hostname

logger = logging.getLogger(__name__)

class TrunkBatchHandler:
    def __init__(self):
        # Tạo một danh sách để chứa các cặp (importer, exporter) cần xử lý
        self.workers = []

    def add_importer_exporter_from_openstack_connections(
        self, connections: list, output_file: str
    ):
        """
        Hàm này chuẩn bị các importer và exporter cho từng connection
        và lưu vào danh sách chờ xử lý.
        """
        for connection in connections:
            try:
                # Lấy URL xác thực (dạng chuỗi) để tránh lỗi decode
                auth_url = connection.auth.get("auth_url")
                
                # Trích xuất hostname từ URL
                hostname = extract_hostname(auth_url)
                sheet_name = f"{hostname}-trunk"

                # Khởi tạo Importer và Exporter riêng cho Trunk
                importer = OpenStackTrunkImporter(connection)
                exporter = ExcelTrunkExporter(sheet_name, output_file)

                # Thêm cặp này vào danh sách workers
                self.workers.append((importer, exporter))
                
            except Exception as e:
                # Log lỗi nếu có vấn đề khi chuẩn bị (ví dụ: URL sai)
                logger.error(f"Error preparing trunk batch for connection: {e}")

    def process(self):
        """
        Hàm này duyệt qua danh sách workers và thực thi việc import/export
        """
        for importer, exporter in self.workers:
            try:
                # 1. Gọi Importer để lấy dữ liệu
                trunks = importer.import_trunks()
                
                # 2. Gọi Exporter để ghi ra Excel
                exporter.export_trunks(trunks)
                
            except Exception as e:
                # Lấy thông tin URL để log lỗi cho rõ ràng
                try:
                    conn_url = importer.connection.auth.get('auth_url', 'unknown')
                except:
                    conn_url = 'unknown'
                    
                logger.error(f"Error processing trunk batch for {conn_url}: {e}")