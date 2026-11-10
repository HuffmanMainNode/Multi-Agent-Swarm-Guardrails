import unittest
from pathlib import Path
from masg.conformance import verify_repository
ROOT=Path(__file__).resolve().parents[1]
class ConformanceTests(unittest.TestCase):
 def test_catalog_has_ten_contracts(self):
  result=verify_repository(ROOT)
  self.assertEqual(result["status"],"PASS",result["errors"])
  self.assertEqual(result["contracts_found"],10)
  self.assertEqual(result["scope"],"repository_structure_only")
if __name__=="__main__": unittest.main()
