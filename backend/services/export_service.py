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

    def create_markdown_pdf(self, files: dict[str, str]) -> bytes:
        import markdown
        from xhtml2pdf import pisa
        import io

        combined_html = "<html><head><style>body { font-family: sans-serif; line-height: 1.6; } h1, h2, h3 { color: #333; } code { background: #f4f4f4; padding: 2px 5px; border-radius: 4px; font-family: monospace; }</style></head><body>"
        
        for file_name, content in files.items():
            if not file_name.endswith('.md'):
                continue
            
            # Convert mermaid explicitly back to code block so it renders nicely in pdf
            content = content.replace("```mermaid", "```text")
            
            html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
            title = file_name.replace(".md", "").replace("_", " ").title()
            
            combined_html += f"<h1>{title}</h1>"
            combined_html += html_content
            combined_html += "<hr style='margin: 40px 0;'/>"
        
        combined_html += "</body></html>"
        
        pdf_buffer = io.BytesIO()
        # Create PDF
        pisa_status = pisa.CreatePDF(io.StringIO(combined_html), dest=pdf_buffer)
        
        if pisa_status.err:
            raise Exception("Failed to generate PDF from Markdown.")
            
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

export_service = ExportService()
