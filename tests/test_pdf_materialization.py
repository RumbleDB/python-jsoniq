import json
from datetime import date
from decimal import Decimal
from unittest import TestCase

from jsoniq import RumbleSession


class TestPdfMaterialization(TestCase):
    """
    Stress the .pdf() materialization path: seq.pdf() -> seq.df() ->
    getAsDataFrame() schema inference.

    Each case asserts the exact shape, dtypes, and values a query produces.
    Values are checked because an object dtype covers strings, Row structs,
    lists, Decimals, dates, and None.
    """

    @classmethod
    def setUpClass(cls):
        RumbleSession._rumbleSession = None
        RumbleSession._builder = RumbleSession.Builder()
        cls.rumble = RumbleSession.builder.appName("pdf_materialization").getOrCreate()
        try:
            cls.rumble.sparkContext.setLogLevel("ERROR")
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.rumble is not None:
                cls.rumble._sparksession.stop()
        finally:
            RumbleSession._rumbleSession = None

    def _assert_pdf(self, query, expected_shape, expected_dtypes):
        pdf = self.rumble.jsoniq(query).pdf()
        self.assertEqual(pdf.shape, expected_shape)
        self.assertEqual({c: str(t) for c, t in pdf.dtypes.items()}, expected_dtypes)
        return pdf

    def _assert_decimals(self, values, expected):
        # Decimal("1") == 1 == 1.0, so pin the type as well as the value.
        values = list(values)
        for x in values:
            self.assertIsInstance(x, Decimal)
        self.assertEqual(values, expected)

    def _assert_json_strings(self, series, expected):
        # the column holds serialized JSON strings; whitespaces are ignored.
        for x in series:
            self.assertIsInstance(x, str)
        actual = [json.dumps(json.loads(x), sort_keys=True) for x in series]
        wanted = [json.dumps(e, sort_keys=True) for e in expected]
        self.assertEqual(actual, wanted)

    def test_baseline_homogeneous(self):
        """Homogeneous sequences keep structure (objects as Row, arrays as list)."""
        with self.subTest("flat object"):
            pdf = self._assert_pdf(
                'for $i in 1 to 3 return {"a":$i,"b":"x"}',
                (3, 2),
                {"a": "object", "b": "object"},
            )
            # integers produced by a range surface as Decimal; strings are kept
            self._assert_decimals(
                pdf["a"], [Decimal("1"), Decimal("2"), Decimal("3")]
            )
            self.assertEqual(list(pdf["b"]), ["x", "x", "x"])

        with self.subTest("nested object"):
            pdf = self._assert_pdf(
                'for $i in 1 to 3 return {"a":$i,"o":{"p":$i,"q":"y"}}',
                (3, 2),
                {"a": "object", "o": "object"},
            )
            # a homogeneous nested object is kept as a struct (Row)
            self.assertEqual(
                [r.asDict() for r in pdf["o"]],
                [
                    {"p": Decimal("1"), "q": "y"},
                    {"p": Decimal("2"), "q": "y"},
                    {"p": Decimal("3"), "q": "y"},
                ],
            )

        with self.subTest("nested array"):
            pdf = self._assert_pdf(
                'for $i in 1 to 3 return {"a":$i,"arr":[1,2,3]}',
                (3, 2),
                {"a": "object", "arr": "object"},
            )
            # a homogeneous array is kept as a list
            for arr in pdf["arr"]:
                self._assert_decimals(
                    arr, [Decimal("1"), Decimal("2"), Decimal("3")]
                )

        with self.subTest("deep nesting"):
            pdf = self._assert_pdf(
                'for $i in 1 to 2 return {"l1":{"l2":{"l3":{"v":$i}}}}',
                (2, 1),
                {"l1": "object"},
            )
            self.assertEqual(
                [r.asDict(recursive=True) for r in pdf["l1"]],
                [
                    {"l2": {"l3": {"v": Decimal("1")}}},
                    {"l2": {"l3": {"v": Decimal("2")}}},
                ],
            )

    def test_nulls_treated_as_absent(self):
        """An explicit null and an absent field yield the same nullable column."""
        with self.subTest("explicit null"):
            pdf = self._assert_pdf(
                '({"a":1,"b":2},{"a":3,"b":null},{"a":5,"b":6})',
                (3, 2),
                {"a": "int32", "b": "float64"},
            )
            self.assertEqual(list(pdf["a"]), [1, 3, 5])
            self.assertEqual(pdf["b"].isna().tolist(), [False, True, False])
            self.assertEqual([pdf["b"].iloc[0], pdf["b"].iloc[2]], [2.0, 6.0])

        with self.subTest("absent field"):
            # an absent field produces the same nullable column as an explicit null
            pdf = self._assert_pdf(
                '({"a":1,"b":2},{"a":3},{"a":5,"b":6})',
                (3, 2),
                {"a": "int32", "b": "float64"},
            )
            self.assertEqual(list(pdf["a"]), [1, 3, 5])
            self.assertEqual(pdf["b"].isna().tolist(), [False, True, False])
            self.assertEqual([pdf["b"].iloc[0], pdf["b"].iloc[2]], [2.0, 6.0])

        with self.subTest("field always null"):
            pdf = self._assert_pdf(
                '({"a":1,"b":null},{"a":2,"b":null})',
                (2, 2),
                {"a": "object", "b": "object"},
            )
            self._assert_decimals(pdf["a"], [Decimal("1"), Decimal("2")])
            self.assertEqual(list(pdf["b"]), [None, None])

        with self.subTest("null, absent, and value"):
            pdf = self._assert_pdf(
                '({"a":1,"b":null},{"a":2},{"a":3,"b":4})',
                (3, 2),
                {"a": "int32", "b": "float64"},
            )
            self.assertEqual(list(pdf["a"]), [1, 2, 3])
            self.assertEqual(pdf["b"].isna().tolist(), [True, True, False])
            self.assertEqual(pdf["b"].iloc[2], 4.0)

        with self.subTest("null in nested object"):
            pdf = self._assert_pdf(
                '({"o":{"p":1,"q":null}},{"o":{"p":2,"q":5}})',
                (2, 1),
                {"o": "object"},
            )
            self.assertEqual(pdf["o"].iloc[0].asDict(), {"p": 1, "q": None})
            self.assertEqual(pdf["o"].iloc[1].asDict(), {"p": 2, "q": 5})

        with self.subTest("null in array"):
            pdf = self._assert_pdf(
                '({"arr":[1,null,3]},{"arr":[4,5,6]})',
                (2, 1),
                {"arr": "object"},
            )
            self.assertEqual(list(pdf["arr"].iloc[0]), [1, None, 3])
            self.assertEqual(list(pdf["arr"].iloc[1]), [4, 5, 6])

        with self.subTest("all values null"):
            pdf = self._assert_pdf(
                '({"a":null},{"a":null})',
                (2, 1),
                {"a": "object"},
            )
            self.assertEqual(list(pdf["a"]), [None, None])

    def test_numeric_mixing(self):
        """Mixing int with double widens to double; with decimal stays Decimal."""
        with self.subTest("int + decimal"):
            pdf = self._assert_pdf(
                '({"n":1},{"n":1.5})',
                (2, 1),
                {"n": "object"},
            )
            self._assert_decimals(pdf["n"], [Decimal("1"), Decimal("1.5")])

        with self.subTest("int + double"):
            pdf = self._assert_pdf(
                '({"n":1},{"n":1.5e0})',
                (2, 1),
                {"n": "float64"},
            )
            self.assertEqual(list(pdf["n"]), [1.0, 1.5])

        with self.subTest("int + decimal + double"):
            pdf = self._assert_pdf(
                '({"n":1},{"n":1.5},{"n":2.5e0})',
                (3, 1),
                {"n": "float64"},
            )
            self.assertEqual(list(pdf["n"]), [1.0, 1.5, 2.5])

        with self.subTest("int + null + double"):
            pdf = self._assert_pdf(
                '({"n":1},{"n":null},{"n":2.5e0})',
                (3, 1),
                {"n": "float64"},
            )
            self.assertEqual(pdf["n"].isna().tolist(), [False, True, False])
            self.assertEqual([pdf["n"].iloc[0], pdf["n"].iloc[2]], [1.0, 2.5])

        with self.subTest("long max"):
            pdf = self._assert_pdf(
                '({"n":9223372036854775807},{"n":1})',
                (2, 1),
                {"n": "object"},
            )
            self._assert_decimals(
                pdf["n"], [Decimal("9223372036854775807"), Decimal("1")]
            )

        with self.subTest("beyond long range"):
            pdf = self._assert_pdf(
                '({"n":92233720368547758070},{"n":1})',
                (2, 1),
                {"n": "object"},
            )
            self._assert_decimals(
                pdf["n"], [Decimal("92233720368547758070"), Decimal("1")]
            )

    def test_numeric_and_nonnumeric_to_string(self):
        """Numeric mixed with non-numeric serializes each value to a string."""
        with self.subTest("int + string"):
            pdf = self._assert_pdf(
                '({"v":1},{"v":"hello"})',
                (2, 1),
                {"v": "object"},
            )
            self.assertEqual(list(pdf["v"]), ["1", "hello"])

        with self.subTest("int + boolean"):
            pdf = self._assert_pdf(
                '({"v":1},{"v":true})',
                (2, 1),
                {"v": "object"},
            )
            self.assertEqual(list(pdf["v"]), ["1", "true"])

        with self.subTest("int + null + string"):
            pdf = self._assert_pdf(
                '({"v":1},{"v":null},{"v":"x"})',
                (3, 1),
                {"v": "object"},
            )
            # a null stays null even when the column is stringified
            self.assertEqual(list(pdf["v"]), ["1", None, "x"])

        with self.subTest("boolean + string"):
            pdf = self._assert_pdf(
                '({"v":true},{"v":"x"})',
                (2, 1),
                {"v": "object"},
            )
            self.assertEqual(list(pdf["v"]), ["true", "x"])

    def test_atomic_vs_structured(self):
        """Atomic mixed with array/object serializes each value to its JSON string."""
        with self.subTest("int + array"):
            pdf = self._assert_pdf(
                '({"v":1},{"v":[1,2,3]})',
                (2, 1),
                {"v": "object"},
            )
            self._assert_json_strings(pdf["v"], [1, [1, 2, 3]])

        with self.subTest("int + object"):
            pdf = self._assert_pdf(
                '({"v":1},{"v":{"p":1}})',
                (2, 1),
                {"v": "object"},
            )
            self._assert_json_strings(pdf["v"], [1, {"p": 1}])

        with self.subTest("object + array"):
            pdf = self._assert_pdf(
                '({"v":{"p":1}},{"v":[1,2]})',
                (2, 1),
                {"v": "object"},
            )
            self._assert_json_strings(pdf["v"], [{"p": 1}, [1, 2]])

        with self.subTest("int + array + object"):
            pdf = self._assert_pdf(
                '({"v":1},{"v":[1,2]},{"v":{"p":1}})',
                (3, 1),
                {"v": "object"},
            )
            self._assert_json_strings(pdf["v"], [1, [1, 2], {"p": 1}])

    def test_nested_heterogeneity(self):
        """A type conflict keeps the outer container but resolves the leaf."""
        with self.subTest("conflict in struct leaf"):
            pdf = self._assert_pdf(
                '({"o":{"x":1}},{"o":{"x":"s"}})',
                (2, 1),
                {"o": "object"},
            )
            # the outer struct is kept; only the conflicting leaf becomes a string
            self.assertEqual(pdf["o"].iloc[0].asDict(), {"x": "1"})
            self.assertEqual(pdf["o"].iloc[1].asDict(), {"x": "s"})

        with self.subTest("conflict in array elements"):
            pdf = self._assert_pdf(
                '({"arr":[1,"two",3]},{"arr":[4,5,6]})',
                (2, 1),
                {"arr": "object"},
            )
            # the array is kept; its elements are coerced to string
            self.assertEqual(list(pdf["arr"].iloc[0]), ["1", "two", "3"])
            self.assertEqual(list(pdf["arr"].iloc[1]), ["4", "5", "6"])

        with self.subTest("different array lengths"):
            pdf = self._assert_pdf(
                '({"arr":[1]},{"arr":[1,2,3,4]})',
                (2, 1),
                {"arr": "object"},
            )
            self.assertEqual(list(pdf["arr"].iloc[0]), [1])
            self.assertEqual(list(pdf["arr"].iloc[1]), [1, 2, 3, 4])

        with self.subTest("merged struct schemas"):
            pdf = self._assert_pdf(
                '({"o":{"x":1}},{"o":{"x":1,"y":2}})',
                (2, 1),
                {"o": "object"},
            )
            # struct schemas are merged; the missing field is null
            self.assertEqual(pdf["o"].iloc[0].asDict(), {"x": 1, "y": None})
            self.assertEqual(pdf["o"].iloc[1].asDict(), {"x": 1, "y": 2})

    def test_array_of_objects_preserves_conflicting_field(self):
        """
        A type conflict on an object field nested in an array should keep the
        field as a string, as it does for a plain struct.
        """
        pdf = self._assert_pdf(
            '({"arr":[{"x":1}]},{"arr":[{"x":"s"}]})',
            (2, 1),
            {"arr": "object"},
        )
        self.assertEqual([r.asDict() for r in pdf["arr"].iloc[0]], [{"x": "1"}])
        self.assertEqual([r.asDict() for r in pdf["arr"].iloc[1]], [{"x": "s"}])

    def test_shape_boundaries(self):
        """Empty, single-item, and bare-atomic sequences."""
        with self.subTest("empty sequence"):
            self._assert_pdf("()", (0, 0), {})

        with self.subTest("single object"):
            pdf = self._assert_pdf(
                '{"a":1,"b":2}',
                (1, 2),
                {"a": "object", "b": "object"},
            )
            self._assert_decimals(pdf["a"], [Decimal("1")])
            self._assert_decimals(pdf["b"], [Decimal("2")])

        with self.subTest("bare atomics"):
            pdf = self._assert_pdf(
                "(1,2,3)",
                (3, 1),
                {"__value": "object"},
            )
            # bare atomics are materialized under a synthetic "__value" column
            self._assert_decimals(
                pdf["__value"], [Decimal("1"), Decimal("2"), Decimal("3")]
            )

        with self.subTest("mixed bare atomics"):
            pdf = self._assert_pdf(
                '(1,"two",3)',
                (3, 1),
                {"__value": "object"},
            )
            self.assertEqual(list(pdf["__value"]), ["1", "two", "3"])

        with self.subTest("empty object"):
            pdf = self._assert_pdf(
                '({"a":1},{})',
                (2, 1),
                {"a": "float64"},
            )
            # the object missing "a" yields a null (absent == null)
            self.assertEqual(pdf["a"].isna().tolist(), [False, True])
            self.assertEqual(pdf["a"].iloc[0], 1.0)

        with self.subTest("empty array"):
            pdf = self._assert_pdf(
                '({"arr":[]},{"arr":[1,2]})',
                (2, 1),
                {"arr": "object"},
            )
            self.assertEqual(list(pdf["arr"].iloc[0]), [])
            self.assertEqual(list(pdf["arr"].iloc[1]), [1, 2])

        with self.subTest("empty nested object"):
            pdf = self._assert_pdf(
                '({"o":{}},{"o":{"p":1}})',
                (2, 1),
                {"o": "object"},
            )
            self.assertEqual(pdf["o"].iloc[0].asDict(), {"p": None})
            self.assertEqual(pdf["o"].iloc[1].asDict(), {"p": 1})

    def test_string_and_number_detection(self):
        """Numeric-looking strings stay strings; special doubles stay double."""
        with self.subTest("numeric-looking strings"):
            pdf = self._assert_pdf(
                '({"v":"1"},{"v":"2"})',
                (2, 1),
                {"v": "object"},
            )
            self.assertEqual(list(pdf["v"]), ["1", "2"])

        with self.subTest("int + numeric string"):
            pdf = self._assert_pdf(
                '({"v":1},{"v":"2"})',
                (2, 1),
                {"v": "object"},
            )
            self.assertEqual(list(pdf["v"]), ["1", "2"])

        with self.subTest("empty and non-ascii strings"):
            pdf = self._assert_pdf(
                '({"v":""},{"v":"\\u00e9\\u6f22"})',
                (2, 1),
                {"v": "object"},
            )
            self.assertEqual(list(pdf["v"]), ["", "é漢"])

        with self.subTest("special doubles"):
            pdf = self._assert_pdf(
                '({"v":xs:double("NaN")},{"v":xs:double("INF")},'
                '{"v":xs:double("-INF")},{"v":1.0})',
                (4, 1),
                {"v": "float64"},
            )
            self.assertEqual(pdf["v"].isna().tolist(), [True, False, False, False])
            self.assertEqual(
                [pdf["v"].iloc[1], pdf["v"].iloc[2], pdf["v"].iloc[3]],
                [float("inf"), float("-inf"), 1.0],
            )

    def test_temporal_types(self):
        """Dates materialize as date objects; dateTimes and mixes as strings."""
        with self.subTest("homogeneous dates"):
            pdf = self._assert_pdf(
                '({"d":xs:date("2020-01-01")},{"d":xs:date("2021-06-15")})',
                (2, 1),
                {"d": "object"},
            )
            # homogeneous dates keep the date type
            self.assertEqual(list(pdf["d"]), [date(2020, 1, 1), date(2021, 6, 15)])

        with self.subTest("date + string"):
            pdf = self._assert_pdf(
                '({"d":xs:date("2020-01-01")},{"d":"not a date"})',
                (2, 1),
                {"d": "object"},
            )
            # mixing a date with a string forces string serialization
            self.assertEqual(list(pdf["d"]), ["2020-01-01", "not a date"])

        with self.subTest("dateTimes"):
            pdf = self._assert_pdf(
                '({"t":xs:dateTime("2020-01-01T10:00:00")},'
                '{"t":xs:dateTime("2021-01-01T00:00:00")})',
                (2, 1),
                {"t": "object"},
            )
            self.assertEqual(
                list(pdf["t"]), ["2020-01-01T10:00:00", "2021-01-01T00:00:00"]
            )
