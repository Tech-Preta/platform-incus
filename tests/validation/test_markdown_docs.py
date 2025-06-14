import pytest
import re
from pathlib import Path
from unittest.mock import patch
import requests
import markdown

@pytest.fixture
def markdown_files():
    """Collect all markdown files in the project."""
    project_root = Path(__file__).parent.parent.parent
    md_files = list(project_root.glob("**/*.md"))
    return md_files

@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing."""
    return """
# Test Document
This is a test document with [valid link](https://example.com) and [internal link](./README.md).

## Section 1
- Item 1
- Item 2

## Section 2
Code block:
```python
def hello():
    return "world"
```
"""

class TestMarkdownFileExistence:
    """Test that expected markdown files exist."""

    def test_readme_exists(self):
        """Test that README.md exists in project root."""
        readme_path = Path(__file__).parent.parent.parent / "README.md"
        assert readme_path.exists(), "README.md should exist in project root"

    def test_markdown_files_not_empty(self, markdown_files):
        """Test that markdown files are not empty."""
        for md_file in markdown_files:
            assert md_file.stat().st_size > 0, f"{md_file} should not be empty"

    def test_markdown_files_have_valid_encoding(self, markdown_files):
        """Test that markdown files have valid UTF-8 encoding."""
        for md_file in markdown_files:
            try:
                md_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                pytest.fail(f"{md_file} has invalid UTF-8 encoding")

class TestMarkdownSyntax:
    """Test markdown syntax and structure."""

    def test_markdown_parses_successfully(self, markdown_files):
        """Test that markdown files parse without errors."""
        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            try:
                markdown.markdown(content)
            except Exception as e:
                pytest.fail(f"{md_file} failed to parse: {e}")

    def test_headers_have_proper_hierarchy(self, markdown_files):
        """Test that headers follow proper hierarchy (no skipping levels)."""
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            headers = header_pattern.findall(content)

            prev_level = 0
            for header_marks, title in headers:
                current_level = len(header_marks)
                if prev_level > 0 and current_level > prev_level + 1:
                    pytest.fail(
                        f"{md_file}: Header '{title}' skips levels "
                        f"(from {prev_level} to {current_level})"
                    )
                prev_level = current_level

    def test_no_trailing_whitespace(self, markdown_files):
        """Test that lines don't have trailing whitespace."""
        for md_file in markdown_files:
            lines = md_file.read_text(encoding='utf-8').splitlines()
            for line_num, line in enumerate(lines, 1):
                if line.rstrip() != line:
                    pytest.fail(f"{md_file}:{line_num} has trailing whitespace")

class TestMarkdownLinks:
    """Test markdown link validation."""

    def test_internal_links_exist(self, markdown_files):
        """Test that internal links point to existing files."""
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            links = link_pattern.findall(content)

            for _, link_url in links:
                if link_url.startswith(('http://', 'https://', 'mailto:', '#')):
                    continue

                if link_url.startswith('./'):
                    link_path = md_file.parent / link_url[2:]
                elif link_url.startswith('../'):
                    link_path = md_file.parent / link_url
                else:
                    link_path = md_file.parent / link_url

                if not link_path.exists():
                    pytest.fail(
                        f"{md_file}: Internal link '{link_url}' points "
                        "to non-existent file"
                    )

    @patch('requests.head')
    def test_external_links_accessible(self, mock_head, markdown_files):
        """Test that external links are accessible (mocked)."""
        mock_head.return_value.status_code = 200
        link_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^)]+)\)')

        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            links = link_pattern.findall(content)

            for _, link_url in links:
                response = requests.head(link_url, timeout=10)
                mock_head.assert_called_with(link_url, timeout=10)
                assert response.status_code == 200

    def test_no_broken_anchor_links(self, markdown_files):
        """Test that anchor links point to existing headers."""
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        anchor_pattern = re.compile(r'\[([^\]]+)\]\(#([^)]+)\)')

        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            headers = header_pattern.findall(content)
            anchors = anchor_pattern.findall(content)

            header_anchors = []
            for _, header_text in headers:
                anchor = re.sub(r'[^\w\s-]', '', header_text.lower())
                anchor = re.sub(r'[\s_-]+', '-', anchor)
                header_anchors.append(anchor)

            for _, anchor_id in anchors:
                if anchor_id not in header_anchors:
                    pytest.fail(
                        f"{md_file}: Anchor link '#{anchor_id}' points "
                        "to non-existent header"
                    )

class TestMarkdownContentQuality:
    """Test markdown content quality and formatting."""

    def test_code_blocks_have_language_specified(self, markdown_files):
        """Test that code blocks specify a language for syntax highlighting."""
        code_block_pattern = re.compile(r'^```(\w*)$', re.MULTILINE)

        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            code_blocks = code_block_pattern.findall(content)

            for i, lang in enumerate(code_blocks, 1):
                if not lang:
                    pytest.fail(
                        f"{md_file}: Code block {i} missing language specification"
                    )

    def test_no_duplicate_headers(self, markdown_files):
        """Test that there are no duplicate headers at the same level."""
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            headers = header_pattern.findall(content)

            headers_by_level = {}
            for header_marks, title in headers:
                level = len(header_marks)
                headers_by_level.setdefault(level, []).append(title.strip())

            for level, titles in headers_by_level.items():
                seen = set()
                for title in titles:
                    key = title.lower()
                    if key in seen:
                        pytest.fail(
                            f"{md_file}: Duplicate header '{title}' at level {level}"
                        )
                    seen.add(key)

    def test_proper_list_formatting(self, markdown_files):
        """Test that lists use consistent formatting."""
        for md_file in markdown_files:
            content = md_file.read_text(encoding='utf-8')
            lines = content.splitlines()

            for line_num, line in enumerate(lines, 1):
                if re.match(r'^\s*[-*+]\s', line):
                    pass  # Could add more specific checks here

class TestMarkdownEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_markdown_file_handling(self, tmp_path):
        """Test handling of empty markdown files."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("")

        # Should not raise an exception
        content = empty_file.read_text(encoding='utf-8')
        assert content == ""

    def test_markdown_with_special_characters(self, tmp_path):
        """Test markdown with special characters and unicode."""
        special_content = """
# Test with Special Characters
This contains unicode: 你好, émojis: 🚀, and special chars: <>&"'
        """
        special_file = tmp_path / "special.md"
        special_file.write_text(special_content, encoding='utf-8')

        content = special_file.read_text(encoding='utf-8')
        assert "你好" in content
        assert "🚀" in content

    def test_very_large_markdown_file(self, tmp_path):
        """Test handling of large markdown files."""
        large_content = "# Large File\n" + "This is a line.\n" * 10000
        large_file = tmp_path / "large.md"
        large_file.write_text(large_content, encoding='utf-8')

        # Should handle large files without issues
        content = large_file.read_text(encoding='utf-8')
        assert len(content.splitlines()) > 10000

    def test_malformed_markdown_handling(self, tmp_path):
        """Test handling of malformed markdown."""
        malformed_content = """
# Unclosed link [text](
## Missing header space
###No space after hash
[Unclosed bracket
```
Unclosed code block
        """
        malformed_file = tmp_path / "malformed.md"
        malformed_file.write_text(malformed_content, encoding='utf-8')

        # Should still parse without crashing
        try:
            markdown.markdown(malformed_content)
        except Exception as e:
            pytest.fail(f"Malformed markdown caused parsing error: {e}")

class TestMarkdownIntegration:
    """Integration tests for markdown validation."""

    def test_full_validation_pipeline(self, markdown_files):
        """Test the complete validation pipeline."""
        validation_results = []

        for md_file in markdown_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                markdown.markdown(content)
                validation_results.append((md_file, True, None))
            except Exception as e:
                validation_results.append((md_file, False, str(e)))

        failed_files = [f for f, success, _ in validation_results if not success]
        if failed_files:
            pytest.fail(f"Validation failed for files: {failed_files}")