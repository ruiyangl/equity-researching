"""Tests for dcf.py: the program must reproduce the book's own numbers.

HOW TO RUN (from this folder)
    python3 -m unittest test_dcf                  every test
    python3 -m unittest -v test_dcf               the same, naming each test
    python3 -m unittest test_dcf.BookTable21      one group

THE GROUPS
    BookTable21              the Summary Illustration in chapter 2 (table 2.1)
    ContinuingValueExamples  the four worked examples in the chapter 2 appendix
    AuthorsSpreadsheet       the authors' Domino's Pizza spreadsheet
                             (expectationsinvesting.com, Online Tutorial 8)
    ReverseDcf               the answers the reverse DCF can give
    Inputs                   lists, named parts, and rejected inputs
    CommandLine              running the program as a user would

The book prints two decimals, so a result matches a printed figure when it is
within half a cent of it (BOOK below).
"""

import contextlib
import io
import json
import os
import tempfile
import unittest

import dcf

BOOK = 0.00501   # half a cent, plus a hair for floating-point arithmetic

# Chapter 2, Summary Illustration. No nonoperating assets or debt. One share,
# so that value per share equals shareholder value.
ILLUSTRATION = {
    "starting_sales": 100.0,
    "sales_growth_rate": 0.10,
    "operating_profit_margin": 0.15,
    "cash_tax_rate": 0.25,
    "incremental_fixed_capital_rate": 0.15,
    "incremental_working_capital_rate": 0.10,
    "cost_of_capital": 0.08,
    "continuing_value_method": "perpetuity_with_inflation",
    "inflation": 0.02,
    "nonoperating_assets": 0,
    "debt": 0,
    "shares_outstanding": 1,
    "forecast_years": 5,
}

# Table 2.1 as printed, years 1 to 5.
TABLE_2_1 = {
    "sales": [110.00, 121.00, 133.10, 146.41, 161.05],
    "operating_profit": [16.50, 18.15, 19.97, 21.96, 24.16],
    "cash_taxes": [4.13, 4.54, 4.99, 5.49, 6.04],
    "nopat": [12.38, 13.61, 14.97, 16.47, 18.12],
    "fixed_capital_investment": [1.50, 1.65, 1.82, 2.00, 2.20],
    "working_capital_investment": [1.00, 1.10, 1.21, 1.33, 1.46],
    "free_cash_flow": [9.88, 10.86, 11.95, 13.14, 14.46],
    "pv_free_cash_flow": [9.14, 9.31, 9.49, 9.66, 9.84],
    "cumulative_pv_free_cash_flow": [9.14, 18.46, 27.94, 37.60, 47.44],
}
TOTAL_INVESTMENT = [2.50, 2.75, 3.03, 3.33, 3.66]

# The authors' spreadsheet: shareholder value per share for forecast periods
# of 1 to 25 years (row 27 of its "Price Implied Expectations" sheet).
DOMINOS_VALUE_PER_SHARE = [
    285.184853, 303.249794, 321.596452, 340.229218, 359.152554,
    378.370993, 397.889135, 417.711654, 437.843298, 458.288887,
    479.053317, 500.141559, 521.558664, 543.309760, 565.400056,
    587.834841, 610.619488, 633.759452, 657.260274, 681.127582,
    705.367092, 729.984606, 754.986021, 780.377323, 806.164592,
]
# Two full columns of the same sheet: year 1 and year 8.
DOMINOS_YEAR_1 = {
    "sales": 3872.116, "operating_profit": 677.6203, "cash_taxes": 111.80735,
    "nopat": 565.812951, "fixed_capital_investment": 37.9974,
    "working_capital_investment": 25.3316, "free_cash_flow": 502.48395,
    "pv_free_cash_flow": 476.934566, "cumulative_pv_free_cash_flow": 476.934566,
    "pv_continuing_value": 14523.189383, "corporate_value": 15000.123949,
    "shareholder_value": 11222.023949,
}
DOMINOS_YEAR_8 = {
    "sales": 6217.772148, "operating_profit": 1088.110126, "cash_taxes": 179.538171,
    "nopat": 908.571955, "fixed_capital_investment": 61.015521,
    "working_capital_investment": 40.677014, "free_cash_flow": 806.87942,
    "pv_free_cash_flow": 531.497802, "cumulative_pv_free_cash_flow": 4030.352842,
    "pv_continuing_value": 16184.700759, "corporate_value": 20215.053601,
    "shareholder_value": 16436.953601,
}


def changed(base, **changes):
    """A copy of some inputs with a few of them changed. None removes a key."""
    inputs = dict(base)
    for key, value in changes.items():
        if value is None:
            inputs.pop(key, None)
        else:
            inputs[key] = value
    return inputs


class BookTable21(unittest.TestCase):
    """The program reproduces the Summary Illustration in chapter 2."""

    def setUp(self):
        self.result = dcf.analyse(ILLUSTRATION)
        self.rows = self.result["rows"]

    def test_every_line_of_the_table(self):
        for line, printed in TABLE_2_1.items():
            for year, figure in enumerate(printed, 1):
                with self.subTest(line=line, year=year):
                    self.assertAlmostEqual(self.rows[year - 1][line], figure, delta=BOOK)

    def test_total_investment(self):
        for year, figure in enumerate(TOTAL_INVESTMENT, 1):
            row = self.rows[year - 1]
            both = row["fixed_capital_investment"] + row["working_capital_investment"]
            self.assertAlmostEqual(both, figure, delta=BOOK)

    def test_present_value_of_continuing_value_is_209_63(self):
        self.assertAlmostEqual(self.rows[4]["pv_continuing_value"], 209.63, delta=BOOK)

    def test_shareholder_value_is_257_07(self):
        self.assertAlmostEqual(self.result["dcf"]["shareholder_value"], 257.07, delta=BOOK)
        self.assertAlmostEqual(self.result["dcf"]["value_per_share"], 257.07, delta=BOOK)

    def test_value_is_free_cash_flow_plus_continuing_value(self):
        # 47.44 + 209.63 = 257.07, as the text says.
        row = self.rows[4]
        self.assertAlmostEqual(
            row["cumulative_pv_free_cash_flow"] + row["pv_continuing_value"],
            self.result["dcf"]["shareholder_value"])


class ContinuingValueExamples(unittest.TestCase):
    """The appendix's examples: NOPAT of $1.00 and an 8% cost of capital."""

    def value(self, method, **extra):
        growth = dcf.growth_after_forecast_period(dict(extra, continuing_value_method=method))
        return dcf.continuing_value(1.00, 0.08, growth)

    def test_perpetuity_is_12_50(self):
        # 1.00 / 0.08
        self.assertAlmostEqual(self.value("perpetuity"), 12.50)

    def test_perpetuity_with_inflation_is_17_00(self):
        # 1.02 / (0.08 - 0.02)
        self.assertAlmostEqual(self.value("perpetuity_with_inflation", inflation=0.02), 17.00)

    def test_perpetuity_with_partial_inflation_is_14_43(self):
        # Half of 2% inflation recouped: 1.01 / (0.08 - 0.01)
        value = self.value("perpetuity_with_partial_inflation", inflation=0.02, inflation_recouped=0.5)
        self.assertAlmostEqual(value, 14.43, delta=BOOK)

    def test_perpetuity_with_decline_is_9_80(self):
        # 0.98 / (0.08 + 0.02)
        self.assertAlmostEqual(self.value("perpetuity_with_decline", decline_rate=0.02), 9.80)

    def test_the_method_changes_the_dcf_value(self):
        # More continuing value means a higher DCF value, in the appendix's order.
        values = [
            dcf.analyse(changed(ILLUSTRATION, continuing_value_method=method, **extra))["dcf"]["value_per_share"]
            for method, extra in [
                ("perpetuity_with_decline", {"decline_rate": 0.02}),
                ("perpetuity", {}),
                ("perpetuity_with_partial_inflation", {"inflation_recouped": 0.5}),
                ("perpetuity_with_inflation", {}),
            ]
        ]
        self.assertEqual(values, sorted(values))
        self.assertEqual(len(set(values)), 4)


class AuthorsSpreadsheet(unittest.TestCase):
    """The program reproduces the authors' Domino's Pizza spreadsheet."""

    def setUp(self):
        self.result = dcf.analyse(dcf.EXAMPLE)
        self.rows = self.result["rows"]

    def test_value_per_share_for_all_25_forecast_periods(self):
        self.assertEqual(len(self.rows), 25)
        for row, figure in zip(self.rows, DOMINOS_VALUE_PER_SHARE):
            with self.subTest(year=row["year"]):
                self.assertAlmostEqual(row["value_per_share"], figure, places=5)

    def test_every_line_of_year_1_and_year_8(self):
        for year, column in ((1, DOMINOS_YEAR_1), (8, DOMINOS_YEAR_8)):
            for line, figure in column.items():
                with self.subTest(year=year, line=line):
                    self.assertAlmostEqual(self.rows[year - 1][line], figure, places=5)

    def test_market_implied_forecast_period_is_8_years(self):
        # At $418 the sheet's answer is 8: $417.71 with 8 years, $437.84 with 9.
        reverse = self.result["reverse_dcf"]
        self.assertEqual(reverse["status"], "found")
        self.assertEqual(reverse["years"], 8)
        self.assertEqual(reverse["label"], "8 years")

    def test_dcf_reads_the_row_of_the_chosen_forecast_period(self):
        # The example asks for 10 years: the tenth figure in the sheet.
        self.assertEqual(self.result["dcf"]["forecast_years"], 10)
        self.assertAlmostEqual(self.result["dcf"]["value_per_share"], 458.288887, places=5)


class ReverseDcf(unittest.TestCase):
    """The answers the reverse DCF can give."""

    def reverse(self, **changes):
        return dcf.analyse(changed(dcf.EXAMPLE, **changes))["reverse_dcf"]

    def test_a_price_equal_to_the_value_at_n_years_gives_n(self):
        for years, value in enumerate(DOMINOS_VALUE_PER_SHARE, 1):
            with self.subTest(years=years):
                reverse = self.reverse(share_price=value + 0.001)
                self.assertEqual(reverse["years"], years if years < 25 else None)

    def test_price_below_the_one_year_value(self):
        reverse = self.reverse(share_price=200.0)       # year 1 is worth 285.18
        self.assertEqual((reverse["status"], reverse["years"]), ("less_than_1", None))
        self.assertEqual(reverse["label"], "less than 1 year")

    def test_price_above_the_last_year_in_the_table(self):
        reverse = self.reverse(share_price=1000.0)      # year 25 is worth 806.16
        self.assertEqual((reverse["status"], reverse["years"]), ("more_than_max", None))
        self.assertEqual(reverse["label"], "more than 25 years")

    def test_growth_that_destroys_value_never_reaches_the_price(self):
        # A 2% margin cannot pay for 80 cents of investment per dollar of new
        # sales, so every extra year of growth lowers the value.
        result = dcf.analyse(changed(
            ILLUSTRATION, operating_profit_margin=0.02,
            incremental_fixed_capital_rate=0.60, incremental_working_capital_rate=0.20,
            continuing_value_method="perpetuity", share_price=50.0))
        values = [row["value_per_share"] for row in result["rows"]]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertEqual(result["reverse_dcf"]["status"], "none")

    def test_a_longer_table_finds_a_longer_period(self):
        reverse = self.reverse(share_price=1000.0, max_years=40)
        self.assertEqual(reverse["status"], "found")
        self.assertGreater(reverse["years"], 25)

    def test_reverse_dcf_alone_needs_no_forecast_period(self):
        result = dcf.analyse(changed(dcf.EXAMPLE, forecast_years=None))
        self.assertIsNone(result["dcf"])
        self.assertEqual(result["reverse_dcf"]["years"], 8)

    def test_dcf_alone_needs_no_share_price(self):
        result = dcf.analyse(ILLUSTRATION)
        self.assertIsNone(result["reverse_dcf"])


class Inputs(unittest.TestCase):
    """Lists, named parts, notes, and inputs the program must refuse."""

    def problems(self, **changes):
        with self.assertRaises(dcf.InputError) as caught:
            dcf.analyse(changed(ILLUSTRATION, **changes))
        return " | ".join(caught.exception.problems)

    def test_a_list_gives_each_year_its_own_number_and_repeats_the_last(self):
        rows = dcf.analyse(changed(ILLUSTRATION, sales_growth_rate=[0.20, 0.10]))["rows"]
        self.assertAlmostEqual(rows[0]["sales"], 120.0)             # 100 x 1.20
        self.assertAlmostEqual(rows[1]["sales"], 132.0)             # x 1.10
        self.assertAlmostEqual(rows[2]["sales"], 145.2)             # x 1.10 again

    def test_a_list_of_equal_numbers_matches_a_single_number(self):
        one = dcf.analyse(ILLUSTRATION)["dcf"]["value_per_share"]
        many = dcf.analyse(changed(ILLUSTRATION, operating_profit_margin=[0.15] * 3))["dcf"]["value_per_share"]
        self.assertAlmostEqual(one, many)

    def test_named_parts_are_added_up(self):
        plain = dcf.analyse(changed(ILLUSTRATION, debt=30, nonoperating_assets=12))
        parts = dcf.analyse(changed(ILLUSTRATION, debt={"bonds": 25, "leases": 5},
                                    nonoperating_assets={"cash": 10, "stake": 2}))
        self.assertAlmostEqual(plain["dcf"]["shareholder_value"], parts["dcf"]["shareholder_value"])
        self.assertAlmostEqual(plain["dcf"]["shareholder_value"], 257.07 + 12 - 30, delta=BOOK)

    def test_value_per_share_divides_by_the_share_count(self):
        result = dcf.analyse(changed(ILLUSTRATION, shares_outstanding=10))
        self.assertAlmostEqual(result["dcf"]["value_per_share"], 25.707, delta=BOOK / 10)

    def test_keys_starting_with_underscore_are_notes(self):
        result = dcf.analyse(changed(ILLUSTRATION, _sources={"sales": "10-K"}))
        self.assertNotIn("_sources", result["inputs"])

    def test_a_missing_input_is_named(self):
        self.assertIn("'cash_tax_rate' is missing", self.problems(cash_tax_rate=None))

    def test_a_percentage_typed_as_7_is_refused(self):
        self.assertIn("write 7% as 0.07", self.problems(sales_growth_rate=7))
        self.assertIn("'operating_profit_margin' year 2", self.problems(operating_profit_margin=[0.15, 15]))

    def test_an_unknown_input_is_refused(self):
        self.assertIn("'price' is not an input", self.problems(price=40))

    def test_each_method_asks_for_its_own_inputs(self):
        self.assertIn("'inflation_recouped' is missing",
                      self.problems(continuing_value_method="perpetuity_with_partial_inflation"))
        self.assertIn("'decline_rate' is missing",
                      self.problems(continuing_value_method="perpetuity_with_decline"))
        self.assertIn("must be one of", self.problems(continuing_value_method="gordon"))

    def test_cost_of_capital_must_exceed_growth_after_the_forecast_period(self):
        self.assertIn("'cost_of_capital' must be higher", self.problems(inflation=0.08))

    def test_something_to_solve_for_is_required(self):
        self.assertIn("give 'forecast_years'", self.problems(forecast_years=None))

    def test_the_forecast_period_must_fit_in_the_table(self):
        self.assertIn("'forecast_years' must be a whole number from 1 to 25", self.problems(forecast_years=26))
        self.assertIn("'forecast_years' must be a whole number", self.problems(forecast_years=5.5))

    def test_all_problems_are_reported_together(self):
        text = self.problems(cash_tax_rate=None, shares_outstanding=0, price=40)
        for expected in ("'cash_tax_rate' is missing", "'shares_outstanding' must be greater than 0",
                         "'price' is not an input"):
            self.assertIn(expected, text)


class CommandLine(unittest.TestCase):
    """Running the program the way a user does."""

    def run_program(self, *arguments):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = dcf.main(list(arguments))
        return code, out.getvalue(), err.getvalue()

    def save(self, inputs):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with handle:
            json.dump(inputs, handle)
        self.addCleanup(os.remove, handle.name)
        return handle.name

    def test_the_example_runs_and_gives_the_spreadsheets_answer(self):
        code, example, _ = self.run_program("--example")
        self.assertEqual(code, 0)
        code, text, _ = self.run_program(self.save(json.loads(example)))
        self.assertEqual(code, 0)
        self.assertIn("**Market-implied forecast period: 8 years** at a share price of 418.00", text)
        self.assertIn("**DCF value per share: 458.29** with a 10-year forecast period", text)
        self.assertIn("Value per share is 417.71 with 8 and 437.84 with 9.", text)

    def test_the_report_shows_the_books_illustration(self):
        code, text, _ = self.run_program(self.save(ILLUSTRATION))
        self.assertEqual(code, 0)
        self.assertIn("**DCF value per share: 257.07** with a 5-year forecast period", text)
        self.assertIn("| 5 | 47.44 | 209.63 | 257.07 | 257.07 | 257.07 | your forecast period |", text)

    def test_the_report_prints_table_2_1_to_the_cent(self):
        # Sales, operating profit, cash taxes, NOPAT, fixed-capital investment,
        # working-capital investment, free cash flow and its present value,
        # exactly as printed in the book. Halves round up: 4.125 prints as 4.13.
        _, text, _ = self.run_program(self.save(ILLUSTRATION))
        for line in (
            "| 1 | 110.00 | 16.50 | 4.13 | 12.38 | 1.50 | 1.00 | 9.88 | 9.14 |",
            "| 2 | 121.00 | 18.15 | 4.54 | 13.61 | 1.65 | 1.10 | 10.86 | 9.31 |",
            "| 3 | 133.10 | 19.97 | 4.99 | 14.97 | 1.82 | 1.21 | 11.95 | 9.49 |",
            "| 4 | 146.41 | 21.96 | 5.49 | 16.47 | 2.00 | 1.33 | 13.14 | 9.66 |",
            "| 5 | 161.05 | 24.16 | 6.04 | 18.12 | 2.20 | 1.46 | 14.46 | 9.84 |",
        ):
            self.assertIn(line, text)

    def test_json_output_holds_the_same_numbers(self):
        code, text, _ = self.run_program(self.save(ILLUSTRATION), "--json")
        self.assertEqual(code, 0)
        result = json.loads(text)
        self.assertAlmostEqual(result["dcf"]["value_per_share"], 257.07, delta=BOOK)
        self.assertEqual(len(result["rows"]), 25)

    def test_rejected_inputs_exit_with_code_2_and_say_why(self):
        code, out, err = self.run_program(self.save(changed(ILLUSTRATION, cost_of_capital=8)))
        self.assertEqual((code, out), (2, ""))
        self.assertIn("Inputs rejected:", err)
        self.assertIn("'cost_of_capital' is 8", err)

    def test_a_missing_file_exits_with_code_2(self):
        code, _, err = self.run_program("no-such-file.json")
        self.assertEqual(code, 2)
        self.assertIn("Cannot read no-such-file.json", err)


if __name__ == "__main__":
    unittest.main()
