from jsoniq import RumbleSession
from unittest import TestCase
import uuid


class TestCatalogsUpdate(TestCase):
    """
    Default Spark session catalog for Delta + custom Iceberg catalogs.
    - Delta uses spark_catalog.
    - Iceberg uses named catalogs (e.g., iceberg, ice_b, ice_one).
    """
    @classmethod
    def setUpClass(cls):
        RumbleSession._rumbleSession = None
        RumbleSession._builder = RumbleSession.Builder()
        cls.rumble = (
            RumbleSession.builder
            .withDelta()
            .withIceberg(["iceberg", "ice_b", "ice_one"])
            .getOrCreate()
        )

    def _create_insert_count(self, rumble, create_query, insert_query, count_query):
        rumble.jsoniq(create_query).applyPUL()
        rumble.jsoniq(insert_query).applyPUL()
        count_value = rumble.jsoniq(count_query).json()
        self.assertEqual(count_value, (2,))

    def _assert_query_fails(self, rumble, query):
        with self.assertRaises(Exception):
            rumble.jsoniq(query).json()

    @staticmethod
    def _cleanup_warehouses():
        import os
        import shutil

        for dirname in ("spark-warehouse", "iceberg-warehouse"):
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

    def test_default_catalogs(self):
        """
        Delta uses spark_catalog and Iceberg uses the named catalog "iceberg".
        Also verifies that cross-catalog reads are rejected.
        """
        suffix = uuid.uuid4().hex
        delta_table = f"default.delta_default_{suffix}"
        iceberg_table = f"iceberg.default.iceberg_default_{suffix}"

        self._create_insert_count(
            self.rumble,
            f'create collection table("{delta_table}") with {{"k": 1}}',
            f'insert {{"k": 2}} last into collection table("{delta_table}")',
            f'count(table("{delta_table}"))'
        )
        self._create_insert_count(
            self.rumble,
            f'create collection iceberg-table("{iceberg_table}") with {{"k": 1}}',
            f'insert {{"k": 2}} last into collection iceberg-table("{iceberg_table}")',
            f'count(iceberg-table("{iceberg_table}"))'
        )
        self._assert_query_fails(
            self.rumble,
            f'iceberg-table("ice_b.{iceberg_table.split(".", 1)[1]}")'
        )

    def test_single_custom_catalogs(self):
        """
        Iceberg on a single custom catalog (ice_one).
        Ensures unqualified access does not resolve to this catalog.
        """
        suffix = uuid.uuid4().hex
        iceberg_table = f"ice_one.default.ice_single_{suffix}"

        self._create_insert_count(
            self.rumble,
            f'create collection iceberg-table("{iceberg_table}") with {{"k": 1}}',
            f'insert {{"k": 2}} last into collection iceberg-table("{iceberg_table}")',
            f'count(iceberg-table("{iceberg_table}"))'
        )
        self._assert_query_fails(
            self.rumble,
            f'iceberg-table("{iceberg_table.split(".", 1)[1]}")'
        )

    def test_multiple_catalogs(self):
        """
        Iceberg on multiple catalogs (iceberg + ice_b).
        Verifies isolation by asserting cross-catalog reads fail.
        """
        suffix = uuid.uuid4().hex
        iceberg_default_table = f"iceberg.default.iceberg_multi_default_{suffix}"
        iceberg_custom_table = f"ice_b.default.iceberg_multi_{suffix}"

        self._create_insert_count(
            self.rumble,
            f'create collection iceberg-table("{iceberg_default_table}") with {{"k": 1}}',
            f'insert {{"k": 2}} last into collection iceberg-table("{iceberg_default_table}")',
            f'count(iceberg-table("{iceberg_default_table}"))'
        )
        self._create_insert_count(
            self.rumble,
            f'create collection iceberg-table("{iceberg_custom_table}") with {{"k": 1}}',
            f'insert {{"k": 2}} last into collection iceberg-table("{iceberg_custom_table}")',
            f'count(iceberg-table("{iceberg_custom_table}"))'
        )
        self._assert_query_fails(
            self.rumble,
            f'iceberg-table("ice_b.{iceberg_default_table.split(".", 1)[1]}")'
        )
        self._assert_query_fails(
            self.rumble,
            f'iceberg-table("{iceberg_custom_table.split(".", 1)[1]}")'
        )

    def test_resolution_order(self):
        """
        Matches Iceberg's catalog/namespace resolution order for spark.table().
        Ensures unqualified access fails when spark_catalog is not Iceberg.
        """
        suffix = uuid.uuid4().hex
        table_name = f"iceberg.default.iceberg_res_{suffix}"
        short_name = f"iceberg_res_{suffix}"
        multi_ns_table = f"iceberg.ns1.ns2.iceberg_res_{suffix}_ns"

        self._create_insert_count(
            self.rumble,
            f'create collection iceberg-table("{table_name}") with {{"k": 1}}',
            f'insert {{"k": 2}} last into collection iceberg-table("{table_name}")',
            f'count(iceberg-table("{table_name}"))'
        )

        # catalog.table -> catalog.currentNamespace.table
        self._create_insert_count(
            self.rumble,
            f'create collection iceberg-table("iceberg.{short_name}_2") with {{"k": 1}}',
            f'insert {{"k": 2}} last into collection iceberg-table("iceberg.{short_name}_2")',
            f'count(iceberg-table("iceberg.{short_name}_2"))'
        )

        # catalog.namespace1.namespace2.table -> catalog.namespace1.namespace2.table
        self._create_insert_count(
            self.rumble,
            f'create collection iceberg-table("{multi_ns_table}") with {{"k": 1}}',
            f'insert {{"k": 2}} last into collection iceberg-table("{multi_ns_table}")',
            f'count(iceberg-table("{multi_ns_table}"))'
        )

        # namespace.table (current catalog) should fail because spark_catalog is not Iceberg here.
        self._assert_query_fails(
            self.rumble,
            f'iceberg-table("default.{short_name}")'
        )
        # table (current catalog + namespace) should also fail for the same reason.
        self._assert_query_fails(
            self.rumble,
            f'iceberg-table("{short_name}")'
        )
