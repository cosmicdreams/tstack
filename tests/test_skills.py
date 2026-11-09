import hashlib
import re
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / "skills"
# sha256 of t3dotgg/tstack skills/full-stop/SKILL.md at the pinned upstream commit
# 1085050 (README "Upstream"). Update both together on an upstream merge.
UPSTREAM_FULL_STOP = "091dcabfcba73e009ddb8e32c498a993a6bb60f8c223d3e21e917f4e52ab9939"
LINK = re.compile(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)")


class SkillContractTests(unittest.TestCase):
    def test_each_skill_has_frontmatter_naming_its_directory(self):
        for skill in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
            with self.subTest(skill=skill.name):
                text = (skill / "SKILL.md").read_text()
                match = re.match(r"---\nname: (.+)\ndescription: (.+)\n(?:.*\n)*?---\n", text)
                self.assertIsNotNone(match, "frontmatter needs name then description")
                self.assertEqual(match[1].strip(), skill.name)

    def test_relative_markdown_links_resolve(self):
        for doc in sorted(SKILLS.rglob("*.md")):
            for target in LINK.findall(doc.read_text()):
                if "://" in target:
                    continue
                with self.subTest(doc=str(doc.relative_to(SKILLS)), target=target):
                    self.assertTrue((doc.parent / target).resolve().is_file())

    def test_full_stop_is_byte_identical_to_pinned_upstream(self):
        digest = hashlib.sha256((SKILLS / "full-stop/SKILL.md").read_bytes()).hexdigest()
        self.assertEqual(digest, UPSTREAM_FULL_STOP)


if __name__ == "__main__":
    unittest.main()
