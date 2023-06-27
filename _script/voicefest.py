#!/usr/bin/env python3
import hashlib
import json
import unittest
from pathlib import Path

_DIR = Path(__file__).parent
_REPO_DIR = _DIR.parent


class VoiceTest(unittest.TestCase):
    def test_voices(self):
        for onnx_path in _REPO_DIR.rglob("*.onnx"):
            with self.subTest(onnx_path=onnx_path):
                self.assertGreater(onnx_path.stat().st_size, 0, "Empty onnx file")

                # Load JSON config for voice
                config_path = onnx_path.parent / f"{onnx_path.name}.json"
                with open(config_path, "r", encoding="utf-8") as config_file:
                    config = json.load(config_file)

                # Verify config
                self.assertIn(
                    "piper_version", config, "Missing piper_version in config"
                )
                self.assertIn("language", config, "Missing language in config")
                self.assertIn("dataset", config, "Missing dataset in config")
                self.assertIn(
                    "quality", config["audio"], "Missing audio quality in config"
                )

                # Verify directory structure
                # <lang_family>/<lang_code>/<dataset>/<quality>/
                quality_dir = onnx_path.parent
                dataset_dir = quality_dir.parent
                lang_code_dir = dataset_dir.parent
                lang_family_dir = lang_code_dir.parent

                self.assertEqual(
                    lang_family_dir.name,
                    config["language"]["family"],
                    "Wrong lang family dir",
                )
                self.assertEqual(
                    lang_code_dir.name,
                    config["language"]["code"],
                    "Wrong lang code dir",
                )
                self.assertEqual(
                    dataset_dir.name, config["dataset"], "Wrong dataset dir"
                )
                self.assertEqual(
                    quality_dir.name, config["audio"]["quality"], "Wrong quality dir"
                )

                # Verify file names
                file_lang_code, file_dataset, file_quality = onnx_path.stem.split("-")
                file_lang_family = file_lang_code.split("_", maxsplit=1)[0]

                self.assertEqual(
                    file_lang_family,
                    config["language"]["family"],
                    "Wrong lang family file",
                )
                self.assertEqual(
                    file_lang_code, config["language"]["code"], "Wrong lang code file"
                )
                self.assertEqual(file_dataset, config["dataset"], "Wrong dataset file")
                self.assertEqual(
                    file_quality, config["audio"]["quality"], "Wrong quality file"
                )


def run_tests():
    runner = unittest.TextTestRunner()
    runner.run(unittest.makeSuite(VoiceTest))


# -----------------------------------------------------------------------------


def write_voices_json():
    # {
    #   "<family>_<region>-<dataset>-<quality>": {
    #     "name": "<dataset>",
    #     "language": "<family>_<region>",
    #     "quality": "<quality>",  // x_low, low, medium, high
    #     "num_speakers": int,
    #     "speaker_id_map": {
    #       "name": int,
    #       ...
    #     }
    #     "files": {
    #       "relative/path/to/file": {
    #         "size_bytes": int,
    #         "md5_digest": str,        // hex
    #       },
    #       ...
    #     }
    #   },
    #   ...
    # }
    voices = {}

    for onnx_path in _REPO_DIR.rglob("*.onnx"):
        voice_dir = onnx_path.parent
        config_path = voice_dir / f"{onnx_path.name}.json"
        with open(config_path, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

        quality = config["audio"]["quality"]
        dataset = config["dataset"]
        lang_code = config["language"]["code"]
        voice_key = f"{lang_code}-{dataset}-{quality}"

        model_card_path = voice_dir / "MODEL_CARD"
        assert model_card_path.exists(), f"Missing {model_card_path}"

        voices[voice_key] = {
            "name": dataset,
            "language": lang_code,
            "quality": quality,
            "num_speakers": config["num_speakers"],
            "speaker_id_map": config.get("speaker_id_map", {}),
            "files": {
                str(file_path.relative_to(_REPO_DIR)): {
                    "size_bytes": file_path.stat().st_size,
                    "md5_digest": get_file_hash(file_path),
                }
                for file_path in (
                    onnx_path,
                    config_path,
                    model_card_path,
                )
            },
        }

    with open(_REPO_DIR / "voices.json", "w", encoding="utf-8") as voices_file:
        json.dump(voices, voices_file, indent=4, ensure_ascii=False)


def get_file_hash(path, bytes_per_chunk: int = 8192) -> str:
    """Hash a file in chunks using md5."""
    path_hash = hashlib.md5()
    with open(path, "rb") as path_file:
        chunk = path_file.read(bytes_per_chunk)
        while chunk:
            path_hash.update(chunk)
            chunk = path_file.read(bytes_per_chunk)

    return path_hash.hexdigest()


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    run_tests()

    print("Writing voices.json")
    write_voices_json()
