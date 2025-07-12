import unittest
import json
import tempfile
import shutil
from pathlib import Path
import sys
import os
from copy import deepcopy

 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test suite for ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "configs"
        self.backup_path = Path(self.temp_dir) / "backups"
        
        self.config_manager = ConfigManager(
            config_path=str(self.config_path),
            backup_path=str(self.backup_path)
        )
         
        self.sample_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "test_db",
                "username": "test_user",
                "password": "test_pass"
            },
            "api": {
                "base_url": "https://api.test.com",
                "timeout": 30,
                "debug": True
            },
            "features": {
                "payments_enabled": False,
                "email_notifications": True,
                "logging_level": "DEBUG"
            },
            "security": {
                "jwt_secret": "test_secret",
                "encryption_key": "test_key",
                "ssl_enabled": False
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
    
        result = self.config_manager.save_config("test_env", self.sample_config)
        self.assertTrue(result)
        
   
        loaded_config = self.config_manager.load_config("test_env")
        self.assertEqual(loaded_config, self.sample_config)
    
    def test_config_validation(self):
        """Test configuration validation."""
         
        is_valid, errors = self.config_manager.validate_config(self.sample_config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
         
        invalid_config = {
            "api": {
                "base_url": "https://api.test.com",
                "timeout": 30,
                "debug": True
            }
        }
        is_valid, errors = self.config_manager.validate_config(invalid_config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_backup_creation(self):
        """Test backup creation."""
      
        self.config_manager.save_config("test_env", self.sample_config)
        
     
        result = self.config_manager.create_backup("test_env")
        self.assertTrue(result)
        
        
        backups = self.config_manager.list_backups("test_env")
        self.assertGreater(len(backups), 0)
    
    def test_get_config_value(self):
        """Test getting specific configuration values."""
       
        self.config_manager.save_config("test_env", self.sample_config)
        
   
        host = self.config_manager.get_config_value("test_env", "database.host")
        self.assertEqual(host, "localhost")
        
       
        non_existent = self.config_manager.get_config_value("test_env", "non.existent.key")
        self.assertIsNone(non_existent)
    
    def test_set_config_value(self):
        """Test setting specific configuration values."""
        
        self.config_manager.save_config("test_env", self.sample_config)
        
         
        result = self.config_manager.set_config_value("test_env", "database.host", "new-host")
        self.assertTrue(result)
        
       
        new_host = self.config_manager.get_config_value("test_env", "database.host")
        self.assertEqual(new_host, "new-host")
    
    def test_list_environments(self):
        """Test listing environments."""
         
        self.config_manager.save_config("dev", self.sample_config)
        self.config_manager.save_config("prod", self.sample_config)
        
       
        environments = self.config_manager.list_environments()
        self.assertIn("dev", environments)
        self.assertIn("prod", environments)
        self.assertIn("development", environments)  
    
    def test_compare_configs(self):
        """Test comparing configurations between environments."""
         
        config1 = deepcopy(self.sample_config)
        config2 = deepcopy(self.sample_config)
        config2["database"]["host"] = "different-host"

        
  
        self.config_manager.save_config("env1", config1)
        self.config_manager.save_config("env2", config2)
        
     
        differences = self.config_manager.compare_configs("env1", "env2")
        self.assertIn("database.host", differences)
        self.assertEqual(differences["database.host"]["in_env1"], "localhost")
        self.assertEqual(differences["database.host"]["in_env2"], "different-host")
    
    def test_export_config(self):
        """Test exporting configuration in different formats."""
        
        self.config_manager.save_config("test_env", self.sample_config)
        
         
        json_export = self.config_manager.export_config("test_env", "json")
        self.assertIsInstance(json_export, str)
        self.assertIn("database", json_export)
        
        
        yaml_export = self.config_manager.export_config("test_env", "yaml")
        self.assertIsInstance(yaml_export, str)
        self.assertIn("database:", yaml_export)
         
        env_export = self.config_manager.export_config("test_env", "env")
        self.assertIsInstance(env_export, str)
        self.assertIn("DATABASE_HOST=localhost", env_export)


if __name__ == "__main__":
    unittest.main()
