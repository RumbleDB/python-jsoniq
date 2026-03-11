from jsoniq import RumbleSession
from unittest import TestCase
import uuid


class TestIcebergDefaultCatalog(TestCase):
    """
    Iceberg uses the session catalog (spark_catalog).
    - Delta custom catalogs are not tested here (to be added later).
    """

    @classmethod
    def setUpClass(cls):
        RumbleSession._rumbleSession = None
        RumbleSession._builder = RumbleSession.Builder()
        cls.rumble = RumbleSession.builder.withIceberg().getOrCreate()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.rumble._sparksession.stop()
        finally:
            RumbleSession._rumbleSession = None
            cls._cleanup_warehouses()

    @staticmethod
    def _cleanup_warehouses():
        import os
        import shutil

        for dirname in ("spark-warehouse", "iceberg-warehouse"):
            path = os.path.join(os.getcwd(), dirname)
            shutil.rmtree(path, ignore_errors=True)

    def test_default_catalog(self):
        """
        Iceberg using spark_catalog with a default namespace.
        This test runs in its own session to avoid Delta/spark_catalog conflicts.
        """
        suffix = uuid.uuid4().hex
        iceberg_table = f"default.iceberg_default_session_{suffix}"

        self.rumble.jsoniq(
            f'create collection iceberg-table("{iceberg_table}") with {{"k": 1}}'
        ).applyPUL()
        self.rumble.jsoniq(
            f'insert {{"k": 2}} last into collection iceberg-table("{iceberg_table}")'
        ).applyPUL()
        count_value = self.rumble.jsoniq(
            f'count(iceberg-table("{iceberg_table}"))'
        ).json()
        self.assertEqual(count_value, (2,))
