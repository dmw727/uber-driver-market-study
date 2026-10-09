import unittest
import csv
from pathlib import Path

from analysis.analyze_survey import read_rows, split_selections
from analysis.chicago_april_traffic_validation import miles, phase_for
from analysis.nyc_yankee_driver_cycle import phase_for as nyc_phase_for
from datetime import datetime


class SurveyAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read_rows()

    def test_usable_response_count(self):
        self.assertEqual(len(self.rows), 51)

    def test_expectation_split(self):
        met = sum(
            row["income_expectation"] in {"Met expectations", "Exceeded expectations"}
            for row in self.rows
        )
        self.assertEqual(met, 27)
        self.assertEqual(len(self.rows) - met, 24)

    def test_retention_counts_are_multi_select(self):
        selected = [
            option
            for row in self.rows
            for option in split_selections(row["retention_priorities"])
        ]
        self.assertGreater(len(selected), len(self.rows))
        self.assertEqual(selected.count("Increase rates"), 42)
        self.assertEqual(selected.count("More promotions/opportunities"), 32)

    def test_removed_private_fields_are_absent(self):
        forbidden = {"Submitter", "Submission Date", "Submission ID", "market", "gender"}
        self.assertTrue(forbidden.isdisjoint(self.rows[0]))


class TrafficValidationTests(unittest.TestCase):
    def test_wrigley_distance_is_zero_at_reference_point(self):
        self.assertAlmostEqual(miles(41.9484, -87.6553, 41.9484, -87.6553), 0.0)

    def test_phase_boundaries_match_game_clock(self):
        self.assertEqual(phase_for(datetime(2026, 4, 20, 16, 40)), "pregame_2h")
        self.assertEqual(phase_for(datetime(2026, 4, 20, 18, 40)), "game_first_2h")
        self.assertEqual(phase_for(datetime(2026, 4, 20, 22, 40)), "extended_postgame")

    def test_nyc_phase_boundaries(self):
        anchor = datetime(2025, 4, 14, 19, 5)
        self.assertEqual(nyc_phase_for(datetime(2025, 4, 14, 17, 5), anchor), "pregame_2h")
        self.assertEqual(nyc_phase_for(datetime(2025, 4, 14, 19, 5), anchor), "game_first_2h")
        self.assertEqual(nyc_phase_for(datetime(2025, 4, 14, 21, 5), anchor), "game_late_post_2h")
        self.assertIsNone(nyc_phase_for(datetime(2025, 4, 14, 23, 5), anchor))


class PortfolioExtensionTests(unittest.TestCase):
    def test_chicago_headline_estimate(self):
        path = Path("data/derived/chicago_monday_panel_estimates.csv")
        with path.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        headline = next(row for row in rows if row["scenario"] == "All published Mondays")
        self.assertEqual(int(headline["dates"]), 22)
        self.assertAlmostEqual(float(headline["relative_difference"]), 0.4854)
        self.assertAlmostEqual(float(headline["bootstrap_ci_low"]), 0.3922)
        self.assertAlmostEqual(float(headline["bootstrap_ci_high"]), 0.5853)

    def test_nyc_full_clock_reversal(self):
        path = Path("data/derived/nyc_yankee_driver_cycle_estimates.csv")
        with path.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        result = next(
            row
            for row in rows
            if row["zone_group"] == "one_mile_ring"
            and row["phase"] == "game_late_post_2h"
        )
        self.assertGreater(float(result["median_occupied_pay_rate_change"]), 0)
        self.assertLess(float(result["median_cycle_pay_rate_change"]), 0)
        self.assertAlmostEqual(float(result["median_approach_time_change"]), 0.1737)

    def test_portfolio_artifacts_exist(self):
        expected = (
            "docs/CROSS_CITY_CASE_STUDY.md",
            "docs/METHODS_APPENDIX.md",
            "docs/images/chicago-event-demand-by-zone.png",
            "docs/images/nyc-complete-driver-clock.png",
            "docs/images/cross-city-measurement-coverage.png",
            "docs/images/nyc-surge-spillover-strategy.png",
        )
        self.assertTrue(all(Path(path).exists() for path in expected))

    def test_nyc_spillover_strategy_result(self):
        path = Path("data/derived/nyc_surge_spillover_estimates.csv")
        with path.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        result = next(row for row in rows if row["strategy"] == "spillover_away")
        self.assertAlmostEqual(float(result["cycle_time_change"]), -0.072)
        self.assertAlmostEqual(float(result["implied_event_pay_premium"]), 0.0001)
        self.assertLess(float(result["implied_event_passenger_fare_premium"]), 0)


if __name__ == "__main__":
    unittest.main()

