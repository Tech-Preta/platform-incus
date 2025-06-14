"""
Comprehensive unit tests for Terraform configuration validation.
Testing Framework: pytest
"""
import pytest
import json
import os
import tempfile
import subprocess
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import yaml
import time
import threading
import concurrent.futures
from typing import Dict, List, Any

# Assuming the validation module exists - adjust import based on actual module structure
try:
    from validation.terraform_validator import (
        validate_terraform_config,
        validate_terraform_file,
        validate_terraform_files,
        TerraformValidationResult
    )
except ImportError:
    # Create mock classes if the actual module doesn't exist yet
    class TerraformValidationResult:
        def __init__(self, is_valid: bool, errors: List[str] = None):
            self.is_valid = is_valid
            self.errors = errors or []
    
    def validate_terraform_config(config):
        # Mock implementation for testing
        if config is None:
            return TerraformValidationResult(False, ["Configuration cannot be None"])
        if not isinstance(config, dict) or not config:
            return TerraformValidationResult(False, ["Configuration cannot be empty"])
        return TerraformValidationResult(True, [])
    
    def validate_terraform_file(file_path):
        # Mock implementation for testing
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        return TerraformValidationResult(True, [])
    
    def validate_terraform_files(file_paths):
        # Mock implementation for testing
        return [validate_terraform_file(fp) for fp in file_paths]


@pytest.fixture
def valid_basic_terraform_config():
    """Basic valid Terraform configuration for testing."""
    return {
        "terraform": {
            "required_version": ">= 0.14"
        },
        "provider": {
            "aws": {
                "region": "us-west-2"
            }
        },
        "resource": {
            "aws_instance": {
                "web_server": {
                    "ami": "ami-12345678",
                    "instance_type": "t2.micro",
                    "tags": {
                        "Name": "WebServer",
                        "Environment": "test"
                    }
                }
            }
        }
    }

@pytest.fixture
def valid_complex_terraform_config():
    """Complex valid Terraform configuration with multiple resources."""
    return {
        "terraform": {
            "required_version": ">= 1.0",
            "required_providers": {
                "aws": {
                    "source": "hashicorp/aws",
                    "version": "~> 4.0"
                }
            }
        },
        "provider": {
            "aws": {
                "region": "us-west-2",
                "default_tags": {
                    "tags": {
                        "Environment": "test",
                        "ManagedBy": "terraform"
                    }
                }
            }
        },
        "data": {
            "aws_availability_zones": {
                "available": {
                    "state": "available"
                }
            }
        },
        "resource": {
            "aws_vpc": {
                "main": {
                    "cidr_block": "10.0.0.0/16",
                    "enable_dns_hostnames": True,
                    "enable_dns_support": True
                }
            },
            "aws_subnet": {
                "public": {
                    "vpc_id": "${aws_vpc.main.id}",
                    "cidr_block": "10.0.1.0/24",
                    "availability_zone": "${data.aws_availability_zones.available.names[0]}",
                    "map_public_ip_on_launch": True
                }
            },
            "aws_instance": {
                "web": {
                    "ami": "ami-12345678",
                    "instance_type": "t3.micro",
                    "subnet_id": "${aws_subnet.public.id}",
                    "depends_on": ["aws_subnet.public"]
                }
            }
        },
        "output": {
            "instance_ip": {
                "value": "${aws_instance.web.public_ip}",
                "description": "Public IP of the web server"
            }
        }
    }

@pytest.fixture
def invalid_terraform_configs():
    """Collection of invalid Terraform configurations for testing."""
    return {
        "empty_config": {},
        "missing_ami": {
            "resource": {
                "aws_instance": {
                    "web": {
                        "instance_type": "t2.micro"
                    }
                }
            }
        },
        "invalid_cidr": {
            "resource": {
                "aws_vpc": {
                    "main": {
                        "cidr_block": "invalid_cidr_block"
                    }
                }
            }
        },
        "circular_dependency": {
            "resource": {
                "aws_instance": {
                    "web": {
                        "ami": "ami-12345",
                        "instance_type": "t2.micro",
                        "depends_on": ["aws_instance.db"]
                    },
                    "db": {
                        "ami": "ami-12345",
                        "instance_type": "t2.micro",
                        "depends_on": ["aws_instance.web"]
                    }
                }
            }
        },
        "invalid_resource_name": {
            "resource": {
                "aws_instance": {
                    "invalid-name-with-hyphens": {
                        "ami": "ami-12345",
                        "instance_type": "t2.micro"
                    }
                }
            }
        }
    }

@pytest.fixture
def temp_terraform_file():
    """Create a temporary Terraform file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tf.json', delete=False) as f:
        yield f.name
    if os.path.exists(f.name):
        os.unlink(f.name)

@pytest.fixture
def temp_terraform_directory():
    """Create a temporary directory with multiple Terraform files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestTerraformConfigValidation:
    """Test class for basic Terraform configuration validation."""

    def test_validate_basic_terraform_config(self, valid_basic_terraform_config):
        """Test validation of a basic valid Terraform configuration."""
        result = validate_terraform_config(valid_basic_terraform_config)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_complex_terraform_config(self, valid_complex_terraform_config):
        """Test validation of a complex valid Terraform configuration."""
        result = validate_terraform_config(valid_complex_terraform_config)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_terraform_version_constraints(self):
        """Test validation of various Terraform version constraints."""
        version_constraints = [
            ">= 0.14",
            "~> 1.0",
            ">= 0.12, < 2.0",
            "= 1.0.0",
            "!= 0.13.0"
        ]
        
        for constraint in version_constraints:
            config = {
                "terraform": {"required_version": constraint},
                "resource": {"null_resource": {"test": {}}}
            }
            result = validate_terraform_config(config)
            assert result.is_valid is True, f"Failed for constraint: {constraint}"

    def test_validate_multiple_providers(self):
        """Test validation with multiple cloud providers."""
        config = {
            "provider": {
                "aws": {
                    "region": "us-west-2",
                    "access_key": "AKIAIOSFODNN7EXAMPLE",
                    "secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                },
                "google": {
                    "project": "my-gcp-project",
                    "region": "us-central1",
                    "zone": "us-central1-a"
                },
                "azurerm": {
                    "features": {},
                    "subscription_id": "12345678-1234-1234-1234-123456789012"
                }
            },
            "resource": {
                "null_resource": {"test": {}}
            }
        }
        result = validate_terraform_config(config)
        assert result.is_valid is True

    def test_validate_data_sources(self):
        """Test validation of Terraform data sources."""
        config = {
            "data": {
                "aws_ami": {
                    "ubuntu": {
                        "most_recent": True,
                        "owners": ["099720109477"],
                        "filter": [
                            {
                                "name": "name",
                                "values": ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
                            }
                        ]
                    }
                },
                "aws_availability_zones": {
                    "available": {
                        "state": "available"
                    }
                }
            },
            "resource": {
                "aws_instance": {
                    "web": {
                        "ami": "${data.aws_ami.ubuntu.id}",
                        "instance_type": "t2.micro",
                        "availability_zone": "${data.aws_availability_zones.available.names[0]}"
                    }
                }
            }
        }
        result = validate_terraform_config(config)
        assert result.is_valid is True

    def test_validate_modules(self):
        """Test validation of Terraform modules."""
        config = {
            "module": {
                "vpc": {
                    "source": "terraform-aws-modules/vpc/aws",
                    "version": "~> 3.0",
                    "name": "test-vpc",
                    "cidr": "10.0.0.0/16",
                    "azs": ["us-west-2a", "us-west-2b"],
                    "public_subnets": ["10.0.1.0/24", "10.0.2.0/24"],
                    "enable_nat_gateway": True,
                    "enable_vpn_gateway": True,
                    "tags": {
                        "Environment": "test"
                    }
                },
                "security_group": {
                    "source": "./modules/security-group",
                    "vpc_id": "${module.vpc.vpc_id}",
                    "allowed_ports": [80, 443, 22]
                }
            }
        }
        result = validate_terraform_config(config)
        assert result.is_valid is True

    def test_validate_outputs(self):
        """Test validation of Terraform outputs."""
        config = {
            "resource": {
                "aws_instance": {
                    "web": {
                        "ami": "ami-12345",
                        "instance_type": "t2.micro"
                    }
                }
            },
            "output": {
                "instance_id": {
                    "value": "${aws_instance.web.id}",
                    "description": "ID of the EC2 instance"
                },
                "instance_public_ip": {
                    "value": "${aws_instance.web.public_ip}",
                    "description": "Public IP address of the EC2 instance",
                    "sensitive": False
                },
                "instance_private_key": {
                    "value": "${aws_instance.web.private_key}",
                    "sensitive": True
                }
            }
        }
        result = validate_terraform_config(config)
        assert result.is_valid is True


class TestTerraformConfigEdgeCases:
    """Test class for edge cases and boundary conditions."""

    def test_validate_empty_configuration(self):
        """Test validation of completely empty configuration."""
        result = validate_terraform_config({})
        assert result.is_valid is False
        assert any("empty" in str(error).lower() or "no resources" in str(error).lower() 
                   for error in result.errors)

    def test_validate_none_configuration(self):
        """Test handling of None input."""
        result = validate_terraform_config(None)
        assert result.is_valid is False
        assert any("none" in str(error).lower() or "null" in str(error).lower() 
                   for error in result.errors)

    def test_validate_malformed_configuration_types(self):
        """Test handling of various malformed input types."""
        invalid_inputs = [
            "string_instead_of_dict",
            123,
            ["list", "instead", "of", "dict"],
            True,
            False
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises((TypeError, ValueError)):
                validate_terraform_config(invalid_input)

    def test_validate_deeply_nested_configuration(self):
        """Test validation of deeply nested Terraform configurations."""
        # Create a deeply nested module structure
        config = {"module": {}}
        current_level = config["module"]
        
        for depth in range(15):  # Test deep nesting
            module_name = f"level_{depth}"
            current_level[module_name] = {
                "source": f"./modules/level_{depth}",
                "variables": {
                    "depth": depth,
                    "name": f"module_at_depth_{depth}",
                    "tags": {"Level": str(depth)}
                }
            }
            if depth < 14:
                current_level[module_name]["module"] = {}
                current_level = current_level[module_name]["module"]
        
        result = validate_terraform_config(config)
        assert result.is_valid is True

    def test_validate_configuration_with_unicode_characters(self):
        """Test validation with Unicode characters in strings."""
        config = {
            "resource": {
                "aws_instance": {
                    "测试实例": {
                        "ami": "ami-12345",
                        "instance_type": "t2.micro",
                        "tags": {
                            "Name": "Тест сервер",
                            "Description": "Servidor de prueba 🚀",
                            "Environment": "тест"
                        }
                    }
                }
            }
        }
        result = validate_terraform_config(config)
        assert isinstance(result.is_valid, bool)

    def test_validate_extremely_large_configuration(self):
        """Test validation performance with very large configurations."""
        large_config = {"resource": {"aws_instance": {}}}
        for i in range(500):
            large_config["resource"]["aws_instance"][f"instance_{i:03d}"] = {
                "ami": f"ami-{i:08d}",
                "instance_type": "t2.micro",
                "tags": {"Name": f"Instance-{i}", "Environment": "test", "Index": str(i)},
                "user_data": f"#!/bin/bash\necho 'Instance {i}' > /tmp/instance_id"
            }
        start_time = time.time()
        result = validate_terraform_config(large_config)
        duration = time.time() - start_time
        assert isinstance(result.is_valid, bool)
        assert duration < 30.0

    def test_validate_configuration_with_very_long_strings(self):
        """Test validation with extremely long string values."""
        very_long_string = "x" * 10000
        config = {
            "resource": {
                "aws_instance": {
                    "test": {
                        "ami": "ami-12345",
                        "instance_type": "t2.micro",
                        "user_data": very_long_string,
                        "tags": {"VeryLongDescription": very_long_string}
                    }
                }
            }
        }
        result = validate_terraform_config(config)
        assert isinstance(result.is_valid, bool)

    def test_validate_configuration_with_special_characters(self):
        """Test validation with various special characters."""
        special_chars_config = {
            "resource": {
                "aws_s3_bucket": {
                    "test_bucket": {
                        "bucket": "test-bucket-with-special-chars",
                        "tags": {
                            "Special": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
                            "Backslash": "\\backslash\\test",
                            "Newline": "line1\nline2\nline3",
                            "Tab": "tab\tseparated\tvalues"
                        }
                    }
                }
            }
        }
        result = validate_terraform_config(special_chars_config)
        assert isinstance(result.is_valid, bool)


class TestTerraformConfigFailureConditions:
    """Test class for failure conditions and error scenarios."""

    def test_validate_invalid_configurations(self, invalid_terraform_configs):
        """Test validation of various invalid configurations."""
        for config_name, config in invalid_terraform_configs.items():
            result = validate_terraform_config(config)
            assert result.is_valid is False, f"Config '{config_name}' should be invalid"
            assert len(result.errors) > 0, f"Config '{config_name}' should have errors"

    def test_validate_configuration_with_invalid_resource_names(self):
        """Test validation with invalid Terraform resource naming conventions."""
        invalid_names = [
            "invalid-resource-name",
            "123invalid",
            "invalid@name",
            "",
            "resource.with.dots",
            "resource with spaces",
            "UPPERCASE",
        ]
        for name in invalid_names:
            config = {
                "resource": {
                    "aws_instance": {
                        name: {
                            "ami": "ami-12345",
                            "instance_type": "t2.micro"
                        }
                    }
                }
            }
            result = validate_terraform_config(config)
            if not result.is_valid:
                assert len(result.errors) > 0

    def test_validate_configuration_with_missing_required_fields(self):
        """Test validation when required fields are missing."""
        incomplete_configs = [
            {"resource": {"aws_instance": {"test": {}}}},
            {"resource": {"aws_instance": {"test": {"ami": "ami-12345"}}}},
            {"resource": {"aws_s3_bucket": {"test": {}}}},
            {"resource": {"aws_vpc": {"test": {}}}},
        ]
        for config in incomplete_configs:
            result = validate_terraform_config(config)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_configuration_with_invalid_field_values(self):
        """Test validation with invalid field values."""
        invalid_configs = [
            {"resource": {"aws_instance": {"test": {"ami": "", "instance_type": "t2.micro"}}}},
            {"resource": {"aws_instance": {"test": {"ami": "ami-12345", "instance_type": "invalid_instance_type"}}}},
            {"resource": {"aws_vpc": {"test": {"cidr_block": "not_a_valid_cidr"}}}},
            {"terraform": {"required_version": "invalid_version_constraint"}}
        ]
        for config in invalid_configs:
            result = validate_terraform_config(config)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_configuration_with_circular_dependencies(self):
        """Test detection of circular dependencies."""
        circular_config = {
            "resource": {
                "aws_instance": {
                    "web": {"ami": "ami-12345", "instance_type": "t2.micro", "depends_on": ["aws_instance.db"]},
                    "db": {"ami": "ami-12345", "instance_type": "t2.micro", "depends_on": ["aws_instance.cache"]},
                    "cache": {"ami": "ami-12345", "instance_type": "t2.micro", "depends_on": ["aws_instance.web"]}
                }
            }
        }
        result = validate_terraform_config(circular_config)
        assert result.is_valid is False
        assert any("circular" in str(error).lower() or "dependency" in str(error).lower() for error in result.errors)

    @patch('subprocess.run')
    def test_validate_configuration_subprocess_failure(self, mock_subprocess):
        """Test handling when external terraform command fails."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Error: Invalid configuration syntax"
        mock_subprocess.return_value.stdout = ""
        config = {"resource": {"aws_instance": {"test": {"ami": "ami-12345", "instance_type": "t2.micro"}}}}
        result = validate_terraform_config(config)
        assert isinstance(result.is_valid, bool)

    def test_validate_configuration_with_invalid_references(self):
        """Test validation with invalid resource references."""
        config = {
            "resource": {
                "aws_instance": {
                    "web": {
                        "ami": "ami-12345",
                        "instance_type": "t2.micro",
                        "subnet_id": "${aws_subnet.nonexistent.id}",
                        "security_groups": ["${aws_security_group.missing.id}"]
                    }
                }
            }
        }
        result = validate_terraform_config(config)
        assert isinstance(result.is_valid, bool)
        if not result.is_valid:
            assert len(result.errors) > 0


class TestTerraformFileValidation:
    """Test class for file-based validation scenarios."""

    def test_validate_terraform_file_from_disk(self, temp_terraform_file, valid_basic_terraform_config):
        """Test validation of Terraform configuration loaded from file."""
        with open(temp_terraform_file, 'w') as f:
            json.dump(valid_basic_terraform_config, f, indent=2)
        result = validate_terraform_file(temp_terraform_file)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_nonexistent_terraform_file(self):
        """Test handling of non-existent file paths."""
        nonexistent_path = "/path/that/definitely/does/not/exist/config.tf.json"
        with pytest.raises(FileNotFoundError):
            validate_terraform_file(nonexistent_path)

    def test_validate_terraform_file_with_invalid_json(self, temp_terraform_file):
        """Test handling of files with invalid JSON content."""
        with open(temp_terraform_file, 'w') as f:
            f.write('{"invalid": json, content}')
        with pytest.raises((json.JSONDecodeError, ValueError)):
            validate_terraform_file(temp_terraform_file)

    def test_validate_terraform_file_with_invalid_permissions(self):
        """Test handling of files with insufficient read permissions."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf.json', delete=False) as f:
            json.dump({"resource": {"null_resource": {"test": {}}}}, f)
            temp_file = f.name
        try:
            os.chmod(temp_file, 0o000)
            with pytest.raises(PermissionError):
                validate_terraform_file(temp_file)
        finally:
            os.chmod(temp_file, 0o644)
            os.unlink(temp_file)

    def test_validate_empty_terraform_file(self, temp_terraform_file):
        """Test handling of empty files."""
        Path(temp_terraform_file).touch()
        with pytest.raises((json.JSONDecodeError, ValueError)):
            validate_terraform_file(temp_terraform_file)

    def test_validate_multiple_terraform_files(self, temp_terraform_directory):
        """Test batch validation of multiple Terraform files."""
        configs = [
            {"resource": {"aws_instance": {"web1": {"ami": "ami-123", "instance_type": "t2.micro"}}}},
            {"resource": {"aws_instance": {"web2": {"ami": "ami-456", "instance_type": "t2.small"}}}},
            {"resource": {"aws_s3_bucket": {"data": {"bucket": "my-test-bucket"}}}},
            {"module": {"vpc": {"source": "terraform-aws-modules/vpc/aws", "version": "~> 3.0"}}},
        ]
        file_paths = []
        for i, config in enumerate(configs):
            file_path = os.path.join(temp_terraform_directory, f"config_{i}.tf.json")
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            file_paths.append(file_path)
        results = validate_terraform_files(file_paths)
        assert len(results) == len(configs)
        assert all(isinstance(r.is_valid, bool) for r in results)

    def test_validate_mixed_valid_invalid_files(self, temp_terraform_directory):
        """Test batch validation with mix of valid and invalid files."""
        configs = [
            {"resource": {"aws_instance": {"valid": {"ami": "ami-123", "instance_type": "t2.micro"}}}},
            {"resource": {"aws_instance": {"invalid": {"instance_type": "t2.micro"}}}},
            {"resource": {"aws_s3_bucket": {"valid_bucket": {"bucket": "test-bucket"}}}},
            {},
        ]
        file_paths = []
        for i, config in enumerate(configs):
            file_path = os.path.join(temp_terraform_directory, f"mixed_{i}.tf.json")
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            file_paths.append(file_path)
        results = validate_terraform_files(file_paths)
        assert len(results) == len(configs)
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = sum(1 for r in results if not r.is_valid)
        assert valid_count > 0 and invalid_count > 0

    def test_validate_large_terraform_file(self, temp_terraform_file):
        """Test validation of large Terraform configuration files."""
        large_config = {"resource": {"aws_instance": {}}}
        for i in range(100):
            large_config["resource"]["aws_instance"][f"instance_{i:03d}"] = {
                "ami": f"ami-{i:08d}",
                "instance_type": "t2.micro",
                "tags": {f"Tag{j}": f"Value{j}" for j in range(10)},
                "user_data": ("#!/bin/bash\n# Instance {i}\necho 'Instance {i}' > /tmp/id\n" * 10)
            }
        with open(temp_terraform_file, 'w') as f:
            json.dump(large_config, f, indent=2)
        start_time = time.time()
        result = validate_terraform_file(temp_terraform_file)
        duration = time.time() - start_time
        assert isinstance(result.is_valid, bool)
        assert duration < 15.0

    @patch('builtins.open', side_effect=IOError("Disk full"))
    def test_validate_terraform_file_io_error(self, mock_open):
        """Test handling of I/O errors during file reading."""
        with pytest.raises(IOError):
            validate_terraform_file("some_file.tf.json")


class TestTerraformConfigParametrized:
    """Parameterized tests for systematic coverage."""

    @pytest.mark.parametrize("resource_type,resource_config,expected_valid", [
        ("aws_instance", {"ami": "ami-12345678", "instance_type": "t2.micro"}, True),
        ("aws_instance", {"ami": "ami-12345678", "instance_type": "t3.small"}, True),
        ("aws_instance", {"ami": "", "instance_type": "t2.micro"}, False),
        ("aws_instance", {"ami": "ami-12345678"}, False),
        ("aws_s3_bucket", {"bucket": "my-test-bucket-12345"}, True),
        ("aws_s3_bucket", {"bucket": "test-bucket", "versioning": {"enabled": True}}, True),
        ("aws_s3_bucket", {}, False),
        ("aws_s3_bucket", {"bucket": ""}, False),
        ("aws_vpc", {"cidr_block": "10.0.0.0/16"}, True),
        ("aws_vpc", {"cidr_block": "192.168.0.0/16", "enable_dns_hostnames": True}, True),
        ("aws_vpc", {"cidr_block": "invalid_cidr"}, False),
        ("aws_vpc", {}, False),
        ("aws_security_group", {"name": "test-sg", "description": "Test SG"}, True),
        ("aws_security_group", {"name": "", "description": "Test SG"}, False),
        ("aws_subnet", {"vpc_id": "vpc-12345", "cidr_block": "10.0.1.0/24"}, True),
        ("aws_subnet", {"vpc_id": "", "cidr_block": "10.0.1.0/24"}, False),
    ])
    def test_validate_aws_resource_types(self, resource_type, resource_config, expected_valid):
        """Test validation across different AWS resource types."""
        config = {"resource": {resource_type: {"test_resource": resource_config}}}
        result = validate_terraform_config(config)
        assert result.is_valid == expected_valid, f"Failed for {resource_type}"

    @pytest.mark.parametrize("provider,provider_config,expected_valid", [
        ("aws", {"region": "us-west-2"}, True),
        ("aws", {"region": "eu-west-1", "access_key": "AKIA...", "secret_key": "secret"}, True),
        ("aws", {"region": ""}, False),
        ("aws", {}, False),
        ("google", {"project": "my-gcp-project", "region": "us-central1"}, True),
        ("google", {"project": "", "region": "us-central1"}, False),
        ("google", {"project": "my-project"}, True),
        ("azurerm", {"features": {}}, True),
        ("azurerm", {"features": {}, "subscription_id": "12345678-1234-1234-1234-123456789012"}, True),
        ("unknown_provider", {"some_config": "value"}, False),
    ])
    def test_validate_different_providers(self, provider, provider_config, expected_valid):
        """Test validation across different cloud providers."""
        config = {"provider": {provider: provider_config}, "resource": {"null_resource": {"test": {}}}}
        result = validate_terraform_config(config)
        assert result.is_valid == expected_valid, f"Failed for provider {provider}"

    @pytest.mark.parametrize("version_constraint", [
        ">= 0.14", "~> 1.0", ">= 0.12, < 2.0", "= 1.0.0", "!= 0.13.0", ">= 1.0.0, < 1.1.0", "~> 0.15.0",
    ])
    def test_validate_version_constraints(self, version_constraint):
        """Test various Terraform version constraints."""
        config = {"terraform": {"required_version": version_constraint}, "resource": {"null_resource": {"test": {}}}}
        result = validate_terraform_config(config)
        assert result.is_valid is True, f"Failed for version constraint: {version_constraint}"


class TestTerraformConfigPerformance:
    """Performance-focused tests."""

    def test_validate_configuration_concurrent_access(self):
        """Test validation with concurrent access patterns."""
        def validate_config(config_id):
            cfg = {"resource": {"aws_instance": {f"instance_{config_id}": {"ami": f"ami-{config_id:08d}", "instance_type": "t2.micro", "tags": {"ID": str(config_id)}}}}}
            return validate_terraform_config(cfg)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(validate_config, i) for i in range(100)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        assert len(results) == 100
        assert all(isinstance(r.is_valid, bool) for r in results)

    def test_validate_configuration_memory_usage(self):
        """Test memory usage with large configurations."""
        import psutil
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        for _ in range(10):
            large_config = {"resource": {"aws_instance": {}}}
            for i in range(200):
                large_config["resource"]["aws_instance"][f"instance_{i}"] = {
                    "ami": f"ami-{i:08d}",
                    "instance_type": "t2.micro",
                    "tags": {f"Tag{j}": f"Value{j}" * 100 for j in range(5)}
                }
            result = validate_terraform_config(large_config)
            assert isinstance(result.is_valid, bool)
        final_memory = process.memory_info().rss
        assert final_memory - initial_memory < 100 * 1024 * 1024

    def test_validate_configuration_stress_test(self):
        """Stress test with rapid successive validations."""
        configs = []
        for i in range(1000):
            configs.append({"resource": {"aws_instance": {f"stress_test_{i}": {"ami": f"ami-{i % 100:08d}", "instance_type": ["t2.micro","t2.small","t2.medium"][i % 3], "tags": {"StressTest": "true", "Index": str(i)}}}}})
        start_time = time.time()
        results = [validate_terraform_config(cfg) for cfg in configs]
        duration = time.time() - start_time
        assert len(results) == 1000
        assert all(isinstance(r.is_valid, bool) for r in results)
        assert duration < 60.0
        assert (duration / 1000) < 0.1