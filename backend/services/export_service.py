import zipfile
import io

class ExportService:
    def create_markdown_zip(self, files: dict[str, str]) -> bytes:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for file_name, content in files.items():
                zip_file.writestr(file_name, content)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()

export_service = ExportService()
