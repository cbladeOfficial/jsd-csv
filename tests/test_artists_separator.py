import os
import unittest
from jsd_csv.formatter import format_filename
from jsd_csv.config import save_config, load_config, DEFAULT_CONFIG
from jsd_csv.cli import build_parser


class TestArtistsSeparator(unittest.TestCase):

    def setUp(self):
        self.sample_meta = {
            "title": "Kesariya",
            "primary_artists": "Pritam",
            "artists_list": ["Pritam", "Arijit Singh", "Amitabh Bhattacharya"],
            "artists": "Pritam, Arijit Singh, Amitabh Bhattacharya",
            "album_artist": "Pritam",
            "album": "Brahmastra",
            "year": "2022",
            "track_number": 1,
            "duration_formatted": "04:28",
        }

    def test_default_artists_separator(self):
        # Default separator should be ", "
        res = format_filename("{artists} - {title}", self.sample_meta)
        self.assertEqual(res, "Pritam, Arijit Singh, Amitabh Bhattacharya - Kesariya")

    def test_custom_artists_separator_comma_nospace(self):
        # Custom separator ","
        res = format_filename("{artists} - {title}", self.sample_meta, artists_separator=",")
        self.assertEqual(res, "Pritam,Arijit Singh,Amitabh Bhattacharya - Kesariya")

    def test_custom_artists_separator_ampersand(self):
        # Custom separator " & "
        res = format_filename("{artists} - {title}", self.sample_meta, artists_separator=" & ")
        self.assertEqual(res, "Pritam & Arijit Singh & Amitabh Bhattacharya - Kesariya")

    def test_custom_artists_separator_semicolon(self):
        # Custom separator "; "
        res = format_filename("{artists} - {title}", self.sample_meta, artists_separator="; ")
        self.assertEqual(res, "Pritam; Arijit Singh; Amitabh Bhattacharya - Kesariya")

    def test_custom_artists_separator_pipe(self):
        # Custom separator " | "
        res = format_filename("{artists} - {title}", self.sample_meta, artists_separator=" | ")
        self.assertEqual(res, "Pritam _ Arijit Singh _ Amitabh Bhattacharya - Kesariya")

    def test_custom_artists_separator_slash(self):
        # Custom separator "/" without spaces
        res = format_filename("{artists} - {title}", self.sample_meta, artists_separator="/")
        self.assertEqual(res, "Pritam_Arijit Singh_Amitabh Bhattacharya - Kesariya")

    def test_custom_artists_separator_slash_sanitized(self):
        # Custom separator " / " should be sanitized to "_" in filename component
        res = format_filename("{artists} - {title}", self.sample_meta, artists_separator=" / ")
        self.assertEqual(res, "Pritam _ Arijit Singh _ Amitabh Bhattacharya - Kesariya")

    def test_metadata_override_artists_separator(self):
        # artists_separator in metadata dict overrides default or parameter
        meta = dict(self.sample_meta)
        meta["artists_separator"] = " + "
        res = format_filename("{artists} - {title}", meta, artists_separator=", ")
        self.assertEqual(res, "Pritam + Arijit Singh + Amitabh Bhattacharya - Kesariya")

    def test_artists_from_raw_string_without_artists_list(self):
        # Fallback when artists_list is not provided but comma-separated artists string is present
        meta = {
            "title": "Channa Mereya",
            "artists": "Pritam, Arijit Singh",
            "album": "Ae Dil Hai Mushkil",
        }
        res_default = format_filename("{artists} - {title}", meta)
        self.assertEqual(res_default, "Pritam, Arijit Singh - Channa Mereya")

        res_custom = format_filename("{artists} - {title}", meta, artists_separator=" & ")
        self.assertEqual(res_custom, "Pritam & Arijit Singh - Channa Mereya")

        # Fallback when raw string is separated by " / "
        meta_slash = {"title": "Song", "artists": "Artist A / Artist B"}
        self.assertEqual(format_filename("{artists} - {title}", meta_slash, artists_separator=" & "), "Artist A & Artist B - Song")

        # Fallback when raw string is separated by " | "
        meta_pipe = {"title": "Song", "artists": "Artist A | Artist B"}
        self.assertEqual(format_filename("{artists} - {title}", meta_pipe, artists_separator=" & "), "Artist A & Artist B - Song")

    def test_artists_deduplication(self):
        meta = {
            "title": "Song",
            "artists_list": ["Artist A", "Artist B", "Artist A"],
        }
        res = format_filename("{artists} - {title}", meta, artists_separator=", ")
        self.assertEqual(res, "Artist A, Artist B - Song")

    def test_compound_artist_with_comma_tyler(self):
        # Tyler, The Creator contains an internal comma in his stage name
        meta = {
            "title": "See You Again",
            "artists_list": ["Tyler, The Creator", "Kali Uchis"],
        }
        res_slash = format_filename("{artists} - {title}", meta, artists_separator=" / ")
        self.assertEqual(res_slash, "Tyler, The Creator _ Kali Uchis - See You Again")

        res_amp = format_filename("{artists} - {title}", meta, artists_separator=" & ")
        self.assertEqual(res_amp, "Tyler, The Creator & Kali Uchis - See You Again")

        # Even if raw string was split by comma, heal_compound_artists reconstructs Tyler, The Creator
        meta_raw = {
            "title": "See You Again",
            "artists": "Tyler, The Creator, Kali Uchis",
        }
        res_healed = format_filename("{artists} - {title}", meta_raw, artists_separator=" & ")
        self.assertEqual(res_healed, "Tyler, The Creator & Kali Uchis - See You Again")

    def test_compound_artist_with_ampersand_simon_and_garfunkel(self):
        # Simon & Garfunkel contains an '&' symbol as part of the group's name
        meta = {
            "title": "The Sound of Silence",
            "artists_list": ["Simon & Garfunkel"],
        }
        res_default = format_filename("{artists} - {title}", meta)
        self.assertEqual(res_default, "Simon & Garfunkel - The Sound of Silence")

        # When collaborating with another artist, & in group name is preserved
        meta_collab = {
            "title": "Collab",
            "artists_list": ["Simon & Garfunkel", "Bob Dylan"],
        }
        res_slash = format_filename("{artists} - {title}", meta_collab, artists_separator=" / ")
        self.assertEqual(res_slash, "Simon & Garfunkel _ Bob Dylan - Collab")

    def test_compound_artist_earth_wind_fire(self):
        # Earth, Wind & Fire contains both comma and ampersand
        meta_raw = {
            "title": "September",
            "artists": "Earth, Wind & Fire, Maurice White",
        }
        res = format_filename("{artists} - {title}", meta_raw, artists_separator=" / ")
        self.assertEqual(res, "Earth, Wind & Fire _ Maurice White - September")

    def test_config_save_and_load_artists_separator(self):
        test_cfg_path = "test_config_temp.json"
        try:
            cfg_to_save = {
                "template": "{artists} - {title}",
                "artists_separator": " & ",
            }
            save_config(cfg_to_save, test_cfg_path)
            loaded = load_config(test_cfg_path)
            self.assertEqual(loaded.get("artists_separator"), " & ")
            self.assertEqual(loaded.get("template"), "{artists} - {title}")
        finally:
            if os.path.exists(test_cfg_path):
                os.remove(test_cfg_path)

    def test_cli_parser_artists_separator(self):
        parser = build_parser()
        args1 = parser.parse_args(["-u", "https://jiosaavn.com/song/test/123"])
        self.assertEqual(args1.artists_separator, ", ")

        args2 = parser.parse_args(["--artists-separator", " & ", "-u", "test"])
        self.assertEqual(args2.artists_separator, " & ")

        args3 = parser.parse_args(["--artist-separator", ",", "-u", "test"])
        self.assertEqual(args3.artists_separator, ",")


if __name__ == "__main__":
    unittest.main()
