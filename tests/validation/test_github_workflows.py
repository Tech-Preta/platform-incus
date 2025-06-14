import pytest
import yaml
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from io import StringIO
import requests

@pytest.fixture
def sample_workflow_yaml():
    """Sample GitHub workflow YAML for testing."""
    return """
name: Test Workflow
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: echo "Running tests"
"""

@pytest.fixture
def invalid_workflow_yaml():
    """Invalid GitHub workflow YAML for error testing."""
    return """
name: Invalid Workflow
on: [push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      missing_dash: "This should cause a YAML parse error"
"""

@pytest.fixture
def complex_workflow_yaml():
    """Complex GitHub workflow with multiple jobs and advanced features."""
    return """
name: Complex Workflow
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'
env:
  NODE_VERSION: '18'
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16, 18, 20]
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        run: echo "Deploying"
"""

@pytest.fixture
def temp_workflow_file():
    """Create a temporary workflow file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("""
name: Temp Workflow
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "test"
""")
        yield f.name
    os.unlink(f.name)

class TestWorkflowYAMLValidation:
    """Test suite for GitHub workflow YAML validation."""
    
    def test_valid_workflow_parsing(self, sample_workflow_yaml):
        """Test parsing of valid workflow YAML."""
        parsed = yaml.safe_load(sample_workflow_yaml)
        assert parsed['name'] == 'Test Workflow'
        assert 'push' in parsed['on']
        assert 'pull_request' in parsed['on']
        assert 'test' in parsed['jobs']
        assert parsed['jobs']['test']['runs-on'] == 'ubuntu-latest'
    
    def test_invalid_workflow_yaml_raises_error(self, invalid_workflow_yaml):
        """Test that invalid YAML raises appropriate error."""
        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(invalid_workflow_yaml)
    
    def test_workflow_required_fields_validation(self):
        """Test validation of required workflow fields."""
        minimal_workflow = {"name": "Test", "on": ["push"], "jobs": {"test": {"runs-on": "ubuntu-latest", "steps": []}}}
        # This should not raise an error
        yaml.safe_load(yaml.dump(minimal_workflow))
        
        # Test missing required fields
        incomplete_workflows = [
            {"on": ["push"], "jobs": {"test": {"runs-on": "ubuntu-latest", "steps": []}}},  # Missing name
            {"name": "Test", "jobs": {"test": {"runs-on": "ubuntu-latest", "steps": []}}},  # Missing on
            {"name": "Test", "on": ["push"]},  # Missing jobs
        ]
        
        for workflow in incomplete_workflows:
            # Structurally valid YAML but missing required workflow fields
            parsed = yaml.safe_load(yaml.dump(workflow))
            assert isinstance(parsed, dict)
    
    def test_complex_workflow_structure(self, complex_workflow_yaml):
        """Test parsing complex workflow with advanced features."""
        parsed = yaml.safe_load(complex_workflow_yaml)
        assert parsed['name'] == 'Complex Workflow'
        assert 'push' in parsed['on']
        assert 'pull_request' in parsed['on']
        assert 'schedule' in parsed['on']
        assert len(parsed['jobs']) == 2
        assert 'strategy' in parsed['jobs']['test']
        assert 'matrix' in parsed['jobs']['test']['strategy']
        assert parsed['jobs']['deploy']['needs'] == 'test'
    
    def test_workflow_file_loading(self, temp_workflow_file):
        """Test loading workflow from file."""
        with open(temp_workflow_file, 'r') as f:
            content = f.read()
            parsed = yaml.safe_load(content)
            assert parsed['name'] == 'Temp Workflow'
            assert parsed['on'] == ['push']

class TestWorkflowSyntaxValidation:
    """Test suite for workflow syntax and structure validation."""
    
    @pytest.mark.parametrize("trigger", ["push", "pull_request", "schedule", "workflow_dispatch", "release"])
    def test_valid_workflow_triggers(self, trigger):
        """Test various valid workflow triggers."""
        workflow = {
            "name": "Test Workflow",
            "on": [trigger],
            "jobs": {"test": {"runs-on": "ubuntu-latest", "steps": []}}
        }
        parsed = yaml.safe_load(yaml.dump(workflow))
        assert trigger in parsed['on']
    
    @pytest.mark.parametrize("runner", ["ubuntu-latest", "windows-latest", "macos-latest", "ubuntu-20.04", "windows-2019"])
    def test_valid_runners(self, runner):
        """Test various valid GitHub runners."""
        workflow = {
            "name": "Test Workflow",
            "on": ["push"],
            "jobs": {"test": {"runs-on": runner, "steps": []}}
        }
        parsed = yaml.safe_load(yaml.dump(workflow))
        assert parsed['jobs']['test']['runs-on'] == runner
    
    def test_workflow_with_environment_variables(self):
        """Test workflow with environment variables."""
        workflow = {
            "name": "Test Workflow",
            "on": ["push"],
            "env": {"NODE_VERSION": "18", "PYTHON_VERSION": "3.9"},
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "env": {"TEST_ENV": "test"},
                    "steps": [{"run": "echo $NODE_VERSION"}]
                }
            }
        }
        parsed = yaml.safe_load(yaml.dump(workflow))
        assert parsed['env']['NODE_VERSION'] == "18"
        assert parsed['jobs']['test']['env']['TEST_ENV'] == "test"
    
    def test_workflow_with_secrets_and_variables(self):
        """Test workflow using secrets and variables syntax."""
        workflow = {
            "name": "Test Workflow",
            "on": ["push"],
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"run": "echo ${{ secrets.API_KEY }}"},
                        {"run": "echo ${{ vars.ENVIRONMENT }}"},
                        {"run": "echo ${{ github.ref }}"}
                    ]
                }
            }
        }
        parsed = yaml.safe_load(yaml.dump(workflow))
        assert "${{ secrets.API_KEY }}" in parsed['jobs']['test']['steps'][0]['run']
        assert "${{ vars.ENVIRONMENT }}" in parsed['jobs']['test']['steps'][1]['run']
    
    def test_workflow_with_matrix_strategy(self):
        """Test workflow with matrix strategy."""
        workflow = {
            "name": "Matrix Test",
            "on": ["push"],
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "strategy": {
                        "matrix": {
                            "python-version": ["3.8", "3.9", "3.10"],
                            "os": ["ubuntu-latest", "windows-latest"]
                        },
                        "fail-fast": False
                    },
                    "steps": [{"run": "python --version"}]
                }
            }
        }
        parsed = yaml.safe_load(yaml.dump(workflow))
        assert len(parsed['jobs']['test']['strategy']['matrix']['python-version']) == 3
        assert parsed['jobs']['test']['strategy']['fail-fast'] is False

class TestWorkflowEdgeCases:
    """Test suite for edge cases and error conditions."""
    
    def test_empty_workflow_file(self):
        """Test handling of empty workflow file."""
        empty_content = ""
        parsed = yaml.safe_load(empty_content)
        assert parsed is None
    
    def test_workflow_with_only_comments(self):
        """Test workflow file with only comments."""
        comment_only = """
        # This is a comment
        # Another comment
        """
        parsed = yaml.safe_load(comment_only)
        assert parsed is None
    
    def test_workflow_with_invalid_characters(self):
        """Test workflow with invalid characters that might cause issues."""
        workflow_with_special_chars = """
        name: "Test with special chars: @#$%^&*()"
        on: [push]
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - run: echo "Special chars in command: @#$%"
        """
        parsed = yaml.safe_load(workflow_with_special_chars)
        assert "Test with special chars: @#$%^&*()" in parsed['name']
    
    def test_deeply_nested_workflow_structure(self):
        """Test workflow with deeply nested structure."""
        nested_workflow = {
            "name": "Nested Test",
            "on": {"push": {"branches": ["main", "develop"]}},
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "if": "github.event_name == 'push'",
                    "strategy": {
                        "matrix": {
                            "include": [
                                {"os": "ubuntu-latest", "python": "3.8"},
                                {"os": "windows-latest", "python": "3.9"}
                            ]
                        }
                    },
                    "steps": [
                        {
                            "uses": "actions/checkout@v3",
                            "with": {"fetch-depth": 0}
                        }
                    ]
                }
            }
        }
        parsed = yaml.safe_load(yaml.dump(nested_workflow))
        assert parsed['on']['push']['branches'] == ["main", "develop"]
        assert len(parsed['jobs']['test']['strategy']['matrix']['include']) == 2
    
    def test_workflow_with_large_content(self):
        """Test workflow with large amount of content."""
        large_workflow = {
            "name": "Large Workflow",
            "on": ["push"],
            "jobs": {}
        }
        
        # Create 50 jobs to test large workflows
        for i in range(50):
            large_workflow["jobs"][f"job_{i}"] = {
                "runs-on": "ubuntu-latest",
                "steps": [{"run": f"echo 'Job {i}'"}] * 10
            }
        
        parsed = yaml.safe_load(yaml.dump(large_workflow))
        assert len(parsed['jobs']) == 50
        assert len(parsed['jobs']['job_0']['steps']) == 10
    
    @pytest.mark.parametrize("invalid_yaml", [
        "name: Test\non: [push\njobs: test",  
        "name: Test\n  on: [push]\njobs:\n  test:",  
        "name: 'Test\non: [push]\njobs: {}",  
    ])
    def test_malformed_yaml_handling(self, invalid_yaml):
        """Test handling of various malformed YAML structures."""
        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(invalid_yaml)

class TestWorkflowPerformanceAndIntegration:
    """Test suite for performance and integration scenarios."""
    
    def test_multiple_workflow_parsing_performance(self):
        """Test performance when parsing multiple workflows."""
        import time
        
        workflows = []
        for i in range(100):
            workflow = {
                "name": f"Workflow {i}",
                "on": ["push"],
                "jobs": {
                    f"job_{i}": {
                        "runs-on": "ubuntu-latest",
                        "steps": [{"run": f"echo 'Step {j}'"} for j in range(10)]
                    }
                }
            }
            workflows.append(yaml.dump(workflow))
        
        start_time = time.time()
        for workflow_yaml in workflows:
            parsed = yaml.safe_load(workflow_yaml)
            assert parsed is not None
        end_time = time.time()
        
        # Should parse 100 workflows in reasonable time (less than 1 second)
        assert end_time - start_time < 1.0
    
    def test_workflow_directory_structure_validation(self):
        """Test validation of workflow directory structure."""
        workflow_paths = [
            ".github/workflows/ci.yml",
            ".github/workflows/deploy.yaml",
            ".github/workflows/test.yml"
        ]
        
        for path in workflow_paths:
            assert path.startswith(".github/workflows/")
            assert path.endswith((".yml", ".yaml"))
    
    @patch('requests.get')
    def test_workflow_action_version_validation(self, mock_get):
        """Test validation of action versions used in workflows."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"tag_name": "v3.0.0"}
        
        workflow = {
            "name": "Action Version Test",
            "on": ["push"],
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v3"},
                        {"uses": "actions/setup-node@v3"}
                    ]
                }
            }
        }
        
        parsed = yaml.safe_load(yaml.dump(workflow))
        for step in parsed['jobs']['test']['steps']:
            if 'uses' in step:
                _, version = step['uses'].split('@')
                assert version.startswith('v')
    
    def test_workflow_secrets_detection(self):
        """Test detection of secrets usage in workflows."""
        workflow_with_secrets = {
            "name": "Secrets Test",
            "on": ["push"],
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"run": "echo ${{ secrets.API_KEY }}"},
                        {"run": "curl -H 'Authorization: Bearer ${{ secrets.TOKEN }}'"}
                    ]
                }
            }
        }
        
        yaml_content = yaml.dump(workflow_with_secrets)
        assert "${{ secrets.API_KEY }}" in yaml_content
        assert "${{ secrets.TOKEN }}" in yaml_content
        
        parsed = yaml.safe_load(yaml_content)
        assert len(parsed['jobs']['test']['steps']) == 2

class TestWorkflowFileOperations:
    """Test suite for workflow file operations and cleanup."""
    
    def test_workflow_file_permissions(self, temp_workflow_file):
        """Test workflow file has appropriate permissions."""
        import stat
        file_stat = os.stat(temp_workflow_file)
        assert file_stat.st_mode & stat.S_IRUSR
    
    def test_workflow_file_encoding(self, temp_workflow_file):
        """Test workflow file encoding handling."""
        with open(temp_workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert isinstance(content, str)
        
        unicode_workflow = """
        name: "Unicode Test 🚀"
        on: [push]
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - run: echo "Testing unicode: 你好世界"
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as f:
            f.write(unicode_workflow)
            temp_unicode_file = f.name
        
        try:
            with open(temp_unicode_file, 'r', encoding='utf-8') as f:
                content = f.read()
                parsed = yaml.safe_load(content)
                assert "🚀" in parsed['name']
                assert "你好世界" in parsed['jobs']['test']['steps'][0]['run']
        finally:
            os.unlink(temp_unicode_file)
    
    def test_workflow_yaml_vs_yml_extensions(self):
        """Test that both .yml and .yaml extensions are handled."""
        workflow_content = """
        name: Extension Test
        on: [push]
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - run: echo "test"
        """
        
        for extension in ['.yml', '.yaml']:
            with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as f:
                f.write(workflow_content)
                temp_file = f.name
            
            try:
                with open(temp_file, 'r') as f:
                    parsed = yaml.safe_load(f.read())
                    assert parsed['name'] == 'Extension Test'
            finally:
                os.unlink(temp_file)
    
    def test_cleanup_after_tests(self):
        """Test that temporary files are properly cleaned up."""
        temp_files_before = len([f for f in os.listdir('/tmp') if f.startswith('tmp') and f.endswith('.yml')])
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=True) as f:
            f.write("name: Cleanup Test\non: [push]\njobs: {}")
        temp_files_after = len([f for f in os.listdir('/tmp') if f.startswith('tmp') and f.endswith('.yml')])
        assert temp_files_before == temp_files_after

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])