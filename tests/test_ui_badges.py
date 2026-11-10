import unittest
from jsd_csv.downloader import make_stage_desc
from jsd_csv.ui import make_box_badge


class TestUIBadges(unittest.TestCase):
    def test_stage_badges_symmetry(self):
        """Verify all downloader stage labels have even length matching even box widths for perfect symmetry."""
        stages = [
            "PROGRESS",
            "QUEUED",
            "RECORDED",
            "CACHED",
            "FAILED",
            "METADATA",
            "COMPLETE",
            "DOWNLOAD",
            "ENCODING",
            "YTM-DL",
        ]
        for box_w in (10, 12):
            for stage in stages:
                total_pad = box_w - len(stage)
                self.assertGreaterEqual(total_pad, 0, f"Stage {stage} exceeds box_w {box_w}")
                self.assertEqual(
                    total_pad % 2,
                    0,
                    f"Stage '{stage}' in box width {box_w} has odd padding ({total_pad}), causing visual asymmetry!",
                )

    def test_summary_badges_symmetry(self):
        """Verify all summary report badges have even length inside width 14 for perfect symmetry."""
        summary_labels = ["COMPLETE", "FAILED", "OUTPUT", "CSV RECORD", "TIME"]
        width = 14
        for label in summary_labels:
            total_pad = width - len(label)
            self.assertGreaterEqual(total_pad, 0, f"Label {label} exceeds width {width}")
            self.assertEqual(
                total_pad % 2,
                0,
                f"Summary label '{label}' in width {width} has odd padding ({total_pad}), causing visual asymmetry!",
            )

    def test_make_box_badge_even_padding(self):
        """Verify make_box_badge generates symmetrical left and right spaces."""
        badge = make_box_badge("COMPLETE", "#16a34a", width=14)
        plain = badge.plain
        self.assertEqual(len(plain), 14)
        left_spaces = len(plain) - len(plain.lstrip(" "))
        right_spaces = len(plain) - len(plain.rstrip(" "))
        self.assertEqual(left_spaces, right_spaces)
        self.assertEqual(left_spaces, 3)


    def test_smart_metrics_column_left_alignment(self):
        """Verify SmartMetricsColumn uses consistent left-alignment with zero leading spaces for even vertical alignment."""
        from unittest.mock import MagicMock
        from jsd_csv.downloader import SmartMetricsColumn

        col = SmartMetricsColumn(width=11)

        # Counter task (overall collection)
        task_counter = MagicMock()
        task_counter.fields = {"unit": "tracks"}
        task_counter.completed = 3
        task_counter.total = 3

        # Complete task (finished track)
        task_complete = MagicMock()
        task_complete.fields = {"unit": "step", "step_text": "Complete"}

        counter_text = col.render(task_counter).plain
        complete_text = col.render(task_complete).plain

        # Both strings must have length equal to column width
        self.assertEqual(len(counter_text), 11)
        self.assertEqual(len(complete_text), 11)

        # Both must start immediately at index 0 (0 leading spaces) to eliminate horizontal raggedness
        self.assertTrue(counter_text.startswith("[3/3]"))
        self.assertTrue(complete_text.startswith("Complete"))

        # Both left-alignment margins must match (zero leading offset)
        self.assertEqual(len(counter_text) - len(counter_text.lstrip(" ")), 0)
        self.assertEqual(len(complete_text) - len(complete_text.lstrip(" ")), 0)


if __name__ == "__main__":
    unittest.main()
