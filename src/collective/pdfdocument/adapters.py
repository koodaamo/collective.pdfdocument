from StringIO import StringIO
from zope.interface import implementer
from collective.documentfile.interfaces import IDocumentInfo

from PyPDF2 import PdfFileReader, PdfFileWriter
from wand.image import Image


@implementer(IDocumentInfo)
class PDFDocumentInfo(object):
   "extractor of document info from OpenXML file"

   def __init__(self, context):
      "initialize the adapter"
      self.context = context
      self.pdf = PdfFileReader(StringIO(context.data))
      self.meta = self.pdf.getDocumentInfo()
      self.xmp = self.pdf.getXmpMetadata()

   @property
   def title(self):
      return self.meta["/Title"] if "/Title" in self.meta else ""

   @property
   def description(self):
      return self.meta["/Subject"] if "/Subject" in self.meta else ""

   @property
   def keywords(self):
      "keywords, tags... "
      # First, try Apple keywords as they are already nicely separated for us
      # Note that meta.get() would return a proxy object, not list of keywords..
      keywords = self.meta["/AAPL:Keywords"] if "/AAPL:Keywords" in self.meta else None
      # If not, split regular keywords string by commas
      if not keywords and self.meta.get("/Keywords"):
         keywords = [kw.strip() for kw in self.meta["/Keywords"].split(',')]
      # If still no keywords, try XMP metadata (should maybe be checked first)
      if not keywords:
         try:
            return [kw.strip() for kw in self.xmp.pdf_keywords.split(',')]
         except:
            pass
         try:
            return [kw.strip() for kw in self.xmp.dc_subject.split(',')]
         except:
            return []

      return keywords

   @property
   def language(self):
      "return xmp language"
      return getattr(self.xmp, "dc_language", "")

   @property
   def pagecount(self):
      "return number of pages/sheets/slides the PDF has"
      return self.pdf.getNumPages()

   @property
   def image(self):
      "return 75dpi representative max 192px high (cover) PNG image for document"
      cover = self.pdf.getPage(0)
      cover_fp = StringIO()
      writer = PdfFileWriter()
      writer.addPage(cover)
      writer.write(cover_fp)
      cover_fp.flush()
      cover_fp.seek(0)
      with Image(file=cover_fp, resolution=(75,75), format="pdf") as img:
         img.format = "png"
         img.transform(resize='x192')
         blob = img.make_blob()

      return ("png", blob)