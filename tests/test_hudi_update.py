from jsoniq import RumbleSession
from unittest import TestCase
import uuid


class TestHudiBuilderConfig(TestCase):
    """
    Hudi wraps the session catalog (spark_catalog), like Delta, so it cannot be
    combined with another format that also claims it. These tests only inspect the
    builder and do not start a Spark session.
    """
    def test_hudi_conflicts_with_delta(self):
        with self.assertRaises(ValueError):
            RumbleSession.Builder().withDelta().withHudi()

    def test_hudi_conflicts_with_iceberg_session_catalog(self):
        with self.assertRaises(ValueError):
            RumbleSession.Builder().withIceberg().withHudi()

    def test_hudi_with_named_iceberg_catalogs(self):
        options = RumbleSession.Builder().withIceberg(["ice"]).withHudi()._sparkbuilder._options
        self.assertEqual(
            options["spark.sql.catalog.spark_catalog"], "org.apache.spark.sql.hudi.catalog.HoodieCatalog"
        )
        self.assertEqual(options["spark.sql.catalog.ice"], "org.apache.iceberg.spark.SparkCatalog")


class TestHudiUpdate(TestCase):
    """
    Hudi tables live in the session catalog: <table> or <database>.<table>.
    """
    @classmethod
    def setUpClass(cls):
        RumbleSession._rumbleSession = None
        RumbleSession._builder = RumbleSession.Builder()
        cls.rumble = (
            RumbleSession.builder
            .withHudi()
            .getOrCreate()
        )

    def _create_insert_count(self, table_name):
        self.rumble.jsoniq(f'create collection hudi-table("{table_name}") with {{"k": 1}}').applyPUL()
        self.rumble.jsoniq(f'insert {{"k": 2}} last into collection hudi-table("{table_name}")').applyPUL()
        count_value = self.rumble.jsoniq(f'count(hudi-table("{table_name}"))').json()
        self.assertEqual(count_value, (2,))

    def test_unqualified_table(self):
        self._create_insert_count(f"hudi_plain_{uuid.uuid4().hex}")

    def test_database_qualified_table(self):
        self._create_insert_count(f"default.hudi_db_{uuid.uuid4().hex}")

    @staticmethod
    def _cleanup_warehouses():
        import os
        import shutil

        for dirname in ("hudi-warehouse", "spark-warehouse"):
            path = os.path.join(os.getcwd(), dirname)
            shutil.rmtree(path, ignore_errors=True)

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.rumble is not None:
                cls.rumble._sparksession.stop()
        finally:
            RumbleSession._rumbleSession = None
            cls._cleanup_warehouses()
