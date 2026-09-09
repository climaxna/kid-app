import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import blog_pipeline_check as checker
import naver_blog_draft as nbd


class NaverImagePlaceholderTests(unittest.TestCase):
    def test_generated_image_becomes_component_without_disclosure(self):
        body = (
            "<!-- parenting -->\n"
            "## 첫 단락\n"
            "📷 [생성이미지 1] 파일: `assets/posts/example/01.png`\n"
            "설명"
        )
        upload = {
            "path": "/upload/test.png",
            "fileSize": 123,
            "width": 1200,
            "height": 675,
            "fileName": "01.png",
        }
        results = [{"kind": "생성이미지", "upload": upload}]
        components = nbd.body_to_components(body, image_results=results)
        serialized = json.dumps(components, ensure_ascii=False)
        self.assertIn('"@ctype": "image"', serialized)
        image = next(component for component in components if component.get("@ctype") == "image")
        self.assertEqual(image["align"], "center")
        self.assertEqual(image["contentMode"], "fit")
        self.assertEqual(image["widthPercentage"], 100)
        self.assertNotIn("이해를 돕기 위한 생성 이미지입니다.", serialized)
        self.assertNotIn("📷 [생성이미지", serialized)

    def test_experience_marker_is_hidden_and_keeps_experience_color(self):
        body = (
            "<!-- parenting -->\n"
            "## 첫 단락\n"
            "<!-- experience -->\n"
            "> 새벽에는 기록을 짧게 남기는 방식이 편했습니다."
        )
        components = nbd.body_to_components(body)
        serialized = json.dumps(components, ensure_ascii=False)
        self.assertNotIn("experience", serialized)
        self.assertNotIn("경험담 초안", serialized)
        self.assertIn("#6b5a45", serialized)

    def test_local_image_path_resolves_from_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "sample.png"
            file_path.write_bytes(b"test")
            resolved = nbd._resolve_local_image(str(file_path))
            self.assertEqual(resolved, file_path.resolve())


class PipelineCheckTests(unittest.TestCase):
    def test_png_size_reader(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "sample.png"
            header = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR"
            header += struct.pack(">II", 1200, 675)
            image_path.write_bytes(header + b"\x08\x06\x00\x00\x00")
            self.assertEqual(checker._image_size(image_path), (1200, 675))

    def test_internal_image_brief_is_rejected(self):
        config = json.loads((ROOT / "BLOG_PIPELINE_CONFIG.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "draft.md"
            draft.write_text(
                "# 제목\n\n<!-- parenting -->\n\n## 본문\n내용\n\n"
                "## 이미지 생성 브리프 (발행 전 삭제)\n내부 메모\n",
                encoding="utf-8",
            )
            errors, _ = checker.validate(draft, "parenting_info", "local", config)
            self.assertTrue(any("내부 작업 섹션" in item for item in errors))

    def test_complete_parenting_package_passes_naver_gate(self):
        config = json.loads((ROOT / "BLOG_PIPELINE_CONFIG.json").read_text(encoding="utf-8"))
        output_root = ROOT / "assets" / "posts"
        output_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output_root) as tmp:
            package = Path(tmp)
            relative_dir = package.relative_to(ROOT).as_posix()
            image_files = []
            header = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR"
            header += struct.pack(">II", 1200, 675) + b"\x08\x06\x00\x00\x00"
            for number in range(1, 5):
                image_path = package / f"{number:02d}.png"
                image_path.write_bytes(header)
                image_files.append(f"{relative_dir}/{number:02d}.png")

            manifest = {
                "version": 1,
                "content_type": "parenting_info",
                "preset": "PARENTING_PRO_V1",
                "draft": "parenting/test.md",
                "images": [
                    {
                        "number": number,
                        "file": file_name,
                        "status": "ready",
                        "qa": {
                            "text": True,
                            "anatomy": True,
                            "safety": True,
                            "privacy": True,
                            "ratio": True,
                        },
                    }
                    for number, file_name in enumerate(image_files, start=1)
                ],
            }
            (package / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )
            draft = package / "draft.md"
            image_lines = "\n".join(
                f"📷 [생성이미지 {number}] 파일: `{file_name}`"
                for number, file_name in enumerate(image_files, start=1)
            )
            draft.write_text(
                "# 테스트 육아 정보\n\n<!-- parenting -->\n\n"
                "## 핵심 내용\n안전한 기본 정보입니다.\n"
                f"{image_lines}\n\n참고｜https://health.kdca.go.kr\n",
                encoding="utf-8",
            )
            errors, warnings = checker.validate(draft, "parenting_info", "naver", config)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_complete_island_package_requires_four_square_roles(self):
        config = json.loads((ROOT / "BLOG_PIPELINE_CONFIG.json").read_text(encoding="utf-8"))
        output_root = ROOT / "assets" / "posts"
        output_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output_root) as tmp:
            package = Path(tmp)
            relative_dir = package.relative_to(ROOT).as_posix()
            image_files = []
            header = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR"
            header += struct.pack(">II", 1080, 1080) + b"\x08\x06\x00\x00\x00"
            for number in range(1, 5):
                image_path = package / f"{number:02d}.png"
                image_path.write_bytes(header)
                image_files.append(f"{relative_dir}/{number:02d}.png")

            manifest = {
                "version": 1,
                "content_type": "island_compare",
                "preset": "ISLAND_COMPARE_PRO_V1",
                "draft": "drafts/test-islands.md",
                "images": [
                    {
                        "number": number,
                        "role": role,
                        "ratio": "1:1",
                        "file": file_name,
                        "status": "ready",
                        "qa": {
                            "text": True,
                            "geography": True,
                            "composition": True,
                            "privacy": True,
                            "ratio": True,
                            "photo_first": True,
                            "independent_file": True,
                            "no_duplicate_scene": True,
                        },
                    }
                    for number, (role, file_name) in enumerate(
                        zip(checker.ISLAND_IMAGE_ROLES, image_files), start=1
                    )
                ],
            }
            (package / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False),
                encoding="utf-8",
            )
            draft = package / "draft.md"
            image_lines = "\n".join(
                f"📷 [생성이미지 {number}] 파일: `{file_name}`"
                for number, file_name in enumerate(image_files, start=1)
            )
            draft.write_text(
                "# 테스트 섬 비교\n\n<!-- travel -->\n\n"
                "## 01. 한눈에 비교\n비교 내용입니다.\n"
                f"{image_lines}\n",
                encoding="utf-8",
            )
            errors, warnings = checker.validate(draft, "island_compare", "naver", config)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_island_package_rejects_non_square_image(self):
        config = json.loads((ROOT / "BLOG_PIPELINE_CONFIG.json").read_text(encoding="utf-8"))
        output_root = ROOT / "assets" / "posts"
        output_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output_root) as tmp:
            package = Path(tmp)
            relative_dir = package.relative_to(ROOT).as_posix()
            header = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR"
            header += struct.pack(">II", 1200, 675) + b"\x08\x06\x00\x00\x00"
            image_files = []
            for number in range(1, 5):
                image_path = package / f"{number:02d}.png"
                image_path.write_bytes(header)
                image_files.append(f"{relative_dir}/{number:02d}.png")
            manifest = {
                "images": [
                    {
                        "number": number,
                        "role": role,
                        "file": file_name,
                        "status": "ready",
                        "qa": {"ratio": True},
                    }
                    for number, (role, file_name) in enumerate(
                        zip(checker.ISLAND_IMAGE_ROLES, image_files), start=1
                    )
                ]
            }
            (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            draft = package / "draft.md"
            image_lines = "\n".join(
                f"📷 [생성이미지 {number}] 파일: `{file_name}`"
                for number, file_name in enumerate(image_files, start=1)
            )
            draft.write_text(
                "# 테스트 섬 비교\n\n<!-- travel -->\n\n## 본문\n" + image_lines,
                encoding="utf-8",
            )
            errors, _ = checker.validate(draft, "island_compare", "naver", config)
            self.assertTrue(any("1:1 정사각형" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
