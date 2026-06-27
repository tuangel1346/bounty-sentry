import datetime as dt
import unittest

from bounty_scanner import markdown_report, reward_from, score_candidate


class RewardTests(unittest.TestCase):
    def test_extracts_supported_reward_formats(self):
        self.assertEqual(reward_from("[Bounty $2,500] fix it"), 2500)
        self.assertEqual(reward_from("Reward USD 99.50"), 100)

    def test_returns_none_without_explicit_currency(self):
        self.assertIsNone(reward_from("Reward: 500 points"))


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.issue = {
            "title": "[Bounty $500] Add tests",
            "body": "A focused task",
            "html_url": "https://github.com/example/project/issues/1",
            "comments": 2,
            "assignees": [],
        }
        self.repository = {
            "full_name": "example/project",
            "created_at": "2020-01-01T00:00:00Z",
            "stargazers_count": 250,
            "fork": False,
            "archived": False,
            "has_discussions": True,
        }

    def test_established_unassigned_bounty_scores_without_warnings(self):
        result = score_candidate(self.issue, self.repository, dt.date(2026, 6, 27))
        self.assertEqual(result.reward_usd, 500)
        self.assertEqual(result.warnings, ())
        self.assertGreater(result.score, 100)

    def test_flags_risky_and_assigned_repository(self):
        self.repository.update(
            full_name="demo/bounty-forge",
            created_at="2026-06-01T00:00:00Z",
            stargazers_count=0,
            fork=True,
        )
        self.issue["assignees"] = [{"login": "worker"}]
        result = score_candidate(self.issue, self.repository, dt.date(2026, 6, 27))
        self.assertIn("issue already assigned", result.warnings)
        self.assertIn("repository is a fork", result.warnings)
        self.assertLess(result.score, 0)

    def test_markdown_report_links_to_issue(self):
        result = score_candidate(self.issue, self.repository, dt.date(2026, 6, 27))
        report = markdown_report([result])
        self.assertIn("| $500 |", report)
        self.assertIn("https://github.com/example/project/issues/1", report)


if __name__ == "__main__":
    unittest.main()
