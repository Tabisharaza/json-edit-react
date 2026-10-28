"""Standard-library regression tests for npm README link conversion.

Run: python3 -m unittest discover -s scripts -p 'test_build_npm_readme.py' -v
"""

import tempfile
import unittest
from pathlib import Path

from build_npm_readme import build_readme, convert_internal_links


BASE = "https://github.com/example/project"


class InternalLinkTests(unittest.TestCase):
    def check_link(self, source, expected):
        self.assertEqual(convert_internal_links(source, BASE), expected)

    def test_anchor(self):
        self.check_link("[intro](#intro)", f"[intro]({BASE}#intro)")

    def test_relative_markdown(self):
        self.check_link("[guide](docs/guide.md)", f"[guide]({BASE}/blob/main/docs/guide.md)")

    def test_relative_markdown_with_anchor(self):
        self.check_link("[guide](docs/guide.md#intro)", f"[guide]({BASE}/blob/main/docs/guide.md#intro)")

    def test_relative_non_markdown_file(self):
        self.check_link("[source](src/index.ts)", f"[source]({BASE}/blob/main/src/index.ts)")

    def test_relative_file_with_colon_after_slash(self):
        self.check_link("[file](docs/example:one.md)", f"[file]({BASE}/blob/main/docs/example:one.md)")

    def test_https(self):
        self.check_link("[web](https://example.com/docs)", "[web](https://example.com/docs)")

    def test_http(self):
        self.check_link("[web](http://example.com/docs)", "[web](http://example.com/docs)")

    def test_mailto(self):
        self.check_link("[mail](mailto:test@example.com)", "[mail](mailto:test@example.com)")

    def test_uppercase_https(self):
        self.check_link("[web](HTTPS://example.com/docs)", "[web](HTTPS://example.com/docs)")

    def test_mixed_case_mailto(self):
        self.check_link("[mail](MailTo:test@example.com)", "[mail](MailTo:test@example.com)")

    def test_tel_scheme(self):
        self.check_link("[call](tel:+12345)", "[call](tel:+12345)")

    def test_ftp_scheme(self):
        self.check_link("[file](ftp://example.com/file)", "[file](ftp://example.com/file)")

    def test_custom_scheme(self):
        self.check_link("[app](my-app.v2+test:page)", "[app](my-app.v2+test:page)")

    def test_protocol_relative(self):
        self.check_link("[cdn](//example.com/file)", "[cdn](//example.com/file)")

    def test_root_relative(self):
        self.check_link("[root](/docs/guide.md)", "[root](/docs/guide.md)")

    def test_relative_image(self):
        self.check_link("![image](assets/example.png)", "![image](assets/example.png)")

    def test_image_anchor(self):
        self.check_link("![image](#symbol)", "![image](#symbol)")

    def test_image_and_normal_anchor_together(self):
        self.check_link("![image](#symbol) [intro](#intro)", f"![image](#symbol) [intro]({BASE}#intro)")

    def test_mixed_content(self):
        self.check_link(
            "[intro](#intro) [guide](docs/guide.md) ![photo](assets/photo.png) [web](https://example.com) [mail](mailto:a@example.com)",
            f"[intro]({BASE}#intro) [guide]({BASE}/blob/main/docs/guide.md) ![photo](assets/photo.png) [web](https://example.com) [mail](mailto:a@example.com)",
        )

    def test_conversion_is_idempotent(self):
        once = convert_internal_links("[intro](#intro) [guide](docs/guide.md) [app](my-app:page)", BASE)
        self.assertEqual(convert_internal_links(once, BASE), once)


class BuildReadmeTests(unittest.TestCase):
    def test_passthrough_without_link_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "README.md"
            original = "[intro](#intro) [file](guide.md) [call](tel:+12345)\n"
            source.write_text(original, encoding="utf-8")
            self.assertEqual(build_readme(source, rewrite_links=False), original)
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_template_expansion_and_output_leave_source_intact(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "README.md"
            template = Path(directory) / "template.md"
            output = Path(directory) / "generated.md"
            original = "<!-- INTRO -->[guide](docs/guide.md) [web](HTTPS://example.com)<!-- INTRO -->\n"
            source.write_text(original, encoding="utf-8")
            template.write_text("# Package\n{{INTRO}}\n", encoding="utf-8")
            self.assertIsNone(build_readme(source, template, output, BASE))
            self.assertEqual(output.read_text(encoding="utf-8"), f"# Package\n[guide]({BASE}/blob/main/docs/guide.md) [web](HTTPS://example.com)\n")
            self.assertEqual(source.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
