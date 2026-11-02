import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from openpyxl import Workbook
from tests.research.acss_audit import inspect_workbook


class SourceWorkbookAuditTests(unittest.TestCase):
    def test_formulas_are_never_narratives_and_duplicates_and_identifier_hits_count_rows(self):
        with TemporaryDirectory() as root:
            path=Path(root)/'source.xlsx';book=Workbook();sheet=book.active
            sheet.append(['subject','description','type','length'])
            sheet.append(['Fictional title','test@example.test phone 1234567890','Complaint','=LEN(B2)'])
            sheet.append(['Fictional title','test@example.test phone 1234567890','Complaint','=LEN(B3)'])
            sheet.append(['=UNTRUSTED_FUNCTION()','Other literal source','Support',None])
            book.save(path);book.close()
            result=inspect_workbook(path)[0]
            self.assertEqual(result['nonempty_rows'],3)
            self.assertEqual(result['formula_cells_not_executed'],3)
            self.assertEqual(result['complete_literal_text_rows'],2)
            self.assertEqual(result['duplicate_complete_literal_text_rows'],1)
            self.assertEqual(result['rows_with_potential_identifier_patterns'],2)
            self.assertEqual(result['recognized_type_counts'],{'complaint':2,'support':1})
