"""Extract text from PDF, txt, and other document formats."""
import fitz # PyMuPDF

class DocumentParser: 
    """Parse raw document bytes into plain text"""

    def parse(self, key: str, data: bytes) -> str: 
        """Parse document bytes to text. Routes by file extension"""
        if key.lower().endswith('.pdf'):
            return self._parse_pdf(data)
        return data.decode('utf-8', errors="replace")
    
    def _parse_pdf(self, data: bytes) -> str: 
        """Extract text from PDF bytes using Pymudf"""
        doc = fitz.open(stream=data, filetype = "pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n\n".join(pages)
        