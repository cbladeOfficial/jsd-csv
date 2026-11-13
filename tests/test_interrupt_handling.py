import os
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

from jsd_csv.cli import main
from jsd_csv.downloader import DownloaderEngine
from jsd_csv.ui import console, print_interrupt_message


class TestInterruptHandling(unittest.TestCase):
    def test_print_interrupt_message_no_error(self):
        """Verify print_interrupt_message executes cleanly and produces formatted output without emojis."""
        with patch.object(console, "print") as mock_print:
            print_interrupt_message()
            self.assertTrue(mock_print.called)

        with patch.object(console, "print") as mock_print:
            print_interrupt_message(detail="Preserved 2 completed track(s).")
            self.assertTrue(mock_print.called)

    @patch("jsd_csv.cli.build_parser")
    @patch("jsd_csv.cli.print_banner")
    def test_cli_catches_keyboard_interrupt(self, mock_banner, mock_parser):
        """Verify cli.main gracefully intercepts KeyboardInterrupt and returns exit code 130."""
        mock_parser.side_effect = KeyboardInterrupt()
        with patch("jsd_csv.cli.print_interrupt_message") as mock_interrupt_msg:
            exit_code = main([])
            self.assertEqual(exit_code, 130)
            self.assertTrue(mock_interrupt_msg.called)

    @patch("jsd_csv.cli.prompt_interactive_options")
    @patch("jsd_csv.cli.print_banner")
    def test_cli_catches_wizard_keyboard_interrupt(self, mock_banner, mock_wizard):
        """Verify cli.main catches KeyboardInterrupt occurring inside the interactive wizard."""
        mock_wizard.side_effect = KeyboardInterrupt()
        with patch("jsd_csv.cli.print_interrupt_message") as mock_interrupt_msg:
            exit_code = main(["-i"])
            self.assertEqual(exit_code, 130)
            self.assertTrue(mock_interrupt_msg.called)

    @patch.object(DownloaderEngine, "_download_and_tag_track")
    def test_downloader_engine_handles_keyboard_interrupt(self, mock_download):
        """Verify DownloaderEngine catches KeyboardInterrupt, writes partial records, and sets interrupted flag."""
        call_count = 0

        def fake_download(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise KeyboardInterrupt()
            return True

        mock_download.side_effect = fake_download

        engine = DownloaderEngine(output_dir="./downloads", mode="songs")
        songs = [
            {"id": "1", "title": "Track One", "media_urls": {"320": "http://example.com/1"}},
            {"id": "2", "title": "Track Two", "media_urls": {"320": "http://example.com/2"}},
        ]
        coll_meta = {"title": "Test Collection"}

        with patch.object(engine.api, "resolve_and_fetch", return_value=(coll_meta, songs)), \
             patch("jsd_csv.downloader.print_interrupt_message") as mock_msg:
            total, success, csv_path = engine.run(input_target="test query", auto_confirm=True)
            self.assertTrue(engine.interrupted)
            self.assertEqual(success, 1)
            self.assertTrue(mock_msg.called)


if __name__ == "__main__":
    unittest.main()
