import json
import os
import argparse
import sys
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
import shutil
from pathlib import Path
import yaml

class ConfigManager:
    """
    A comprehensive Configuration Management System for handling different environment configurations.
    
    Features:
    - Multi-environment support (dev, test, staging, prod)
    - Automatic backup creation
    - Configuration validation
    - Template-based configuration generation
    - Command-line interface
    - Version control integration
    - Secure configuration handling
    """
    
    def __init__(self, config_path: str = "configs/", backup_path: str = "backups/"):
        """
        Initialize the Configuration Manager.
        
        Args:
            config_path: Directory where configuration files are stored
            backup_path: Directory where backup files are stored
        """
        self.config_path = Path(config_path)
        self.backup_path = Path(backup_path)
        self.current_env = "development"
        self.logger = self._setup_logging()
        
        # Create directories if they don't exist
        self.config_path.mkdir(exist_ok=True)
        self.backup_path.mkdir(exist_ok=True)
        
        # Initialize default environments if they don't exist
        self._initialize_default_configs()
        
        self.logger.info("ConfigManager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the configuration manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('config_manager.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def _initialize_default_configs(self):
        """Initialize default configuration files if they don't exist."""
        default_configs = {
            "development": {
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "myapp_dev",
                    "username": "dev_user",
                    "password": "dev_pass",
                    "pool_size": 5
                },
                "api": {
                    "base_url": "https://api.dev.myapp.com",
                    "timeout": 30,
                    "debug": True,
                    "rate_limit": 1000
                },
                "features": {
                    "payments_enabled": False,
                    "email_notifications": True,
                    "logging_level": "DEBUG",
                    "cache_enabled": True
                },
                "security": {
                    "jwt_secret": "dev_secret_key",
                    "encryption_key": "dev_encryption_key",
                    "ssl_enabled": False
                }
            },
            "testing": {
                "database": {
                    "host": "test-db.myapp.com",
                    "port": 5432,
                    "name": "myapp_test",
                    "username": "test_user",
                    "password": "test_pass",
                    "pool_size": 3
                },
                "api": {
                    "base_url": "https://api.test.myapp.com",
                    "timeout": 20,
                    "debug": True,
                    "rate_limit": 500
                },
                "features": {
                    "payments_enabled": True,
                    "email_notifications": False,
                    "logging_level": "INFO",
                    "cache_enabled": True
                },
                "security": {
                    "jwt_secret": "test_secret_key",
                    "encryption_key": "test_encryption_key",
                    "ssl_enabled": True
                }
            },
            "production": {
                "database": {
                    "host": "prod-db.myapp.com",
                    "port": 5432,
                    "name": "myapp_prod",
                    "username": "prod_user",
                    "password": "${DB_PASSWORD}",  # Environment variable
                    "pool_size": 20
                },
                "api": {
                    "base_url": "https://api.myapp.com",
                    "timeout": 10,
                    "debug": False,
                    "rate_limit": 10000
                },
                "features": {
                    "payments_enabled": True,
                    "email_notifications": True,
                    "logging_level": "ERROR",
                    "cache_enabled": True
                },
                "security": {
                    "jwt_secret": "${JWT_SECRET}",
                    "encryption_key": "${ENCRYPTION_KEY}",
                    "ssl_enabled": True
                }
            }
        }
        
        for env_name, config in default_configs.items():
            config_file = self.config_path / f"{env_name}.json"
            if not config_file.exists():
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                self.logger.info(f"Created default configuration for {env_name}")
    
    def load_config(self, environment: str) -> Dict[str, Any]:
        """
        Load configuration for a specific environment.
        
        Args:
            environment: Environment name (e.g., 'development', 'testing', 'production')
            
        Returns:
            Dictionary containing the configuration data
        """
        config_file = self.config_path / f"{environment}.json"
        
        if not config_file.exists():
            self.logger.error(f"Configuration file not found: {config_file}")
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)
                # Process environment variables
                config = self._process_environment_variables(config)
                self.logger.info(f"Loaded configuration for environment: {environment}")
                return config
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {config_file}")
            raise json.JSONDecodeError(f"Invalid JSON in {config_file}: {str(e)}", e.doc, e.pos)
    
    def _process_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process environment variables in configuration."""
        def process_dict(d):
            if isinstance(d, dict):
                return {k: process_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [process_dict(item) for item in d]
            elif isinstance(d, str) and d.startswith('${') and d.endswith('}'):
                env_var = d[2:-1]  # Remove ${ and }
                return os.getenv(env_var, d)  # Return original if env var not found
            else:
                return d
        
        return process_dict(config)
    
    def save_config(self, environment: str, config: Dict[str, Any], create_backup: bool = True) -> bool:
        """
        Save configuration for a specific environment.
        
        Args:
            environment: Environment name
            config: Configuration dictionary to save
            create_backup: Whether to create backup before saving
            
        Returns:
            True if successful, False otherwise
        """
        config_file = self.config_path / f"{environment}.json"
        
        try:
            # Validate configuration before saving
            is_valid, errors = self.validate_config(config)
            if not is_valid:
                self.logger.error(f"Invalid configuration: {errors}")
                return False
            
            # Create backup before saving
            if create_backup and config_file.exists():
                self.create_backup(environment)
            
            with open(config_file, 'w') as file:
                json.dump(config, file, indent=4)
                
            self.logger.info(f"Configuration saved for environment: {environment}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def create_backup(self, environment: str) -> bool:
        """
        Create a backup of the current configuration.
        
        Args:
            environment: Environment name
            
        Returns:
            True if backup created successfully, False otherwise
        """
        config_file = self.config_path / f"{environment}.json"
        
        if not config_file.exists():
            self.logger.warning(f"No configuration file to backup: {config_file}")
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{environment}_backup_{timestamp}.json"
            backup_file = self.backup_path / backup_filename
            
            shutil.copy2(config_file, backup_file)
            
            self.logger.info(f"Backup created: {backup_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return False
    
    def restore_backup(self, environment: str, backup_timestamp: str) -> bool:
        """
        Restore configuration from a backup.
        
        Args:
            environment: Environment name
            backup_timestamp: Timestamp of the backup to restore
            
        Returns:
            True if restore successful, False otherwise
        """
        backup_filename = f"{environment}_backup_{backup_timestamp}.json"
        backup_file = self.backup_path / backup_filename
        
        if not backup_file.exists():
            self.logger.error(f"Backup file not found: {backup_file}")
            return False
        
        try:
            config_file = self.config_path / f"{environment}.json"
            # Create current backup before restoring
            self.create_backup(environment)
            # Restore from backup
            shutil.copy2(backup_file, config_file)
            
            self.logger.info(f"Configuration restored from backup: {backup_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate configuration structure.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Define required structure
        required_structure = {
            "database": ["host", "port", "name", "username", "password"],
            "api": ["base_url", "timeout", "debug"],
            "features": ["payments_enabled", "email_notifications", "logging_level"],
            "security": ["jwt_secret", "encryption_key", "ssl_enabled"]
        }
        
        # Check for required sections
        for section, keys in required_structure.items():
            if section not in config:
                errors.append(f"Missing required section: {section}")
                continue
            
            # Check for required keys in each section
            for key in keys:
                if key not in config[section]:
                    errors.append(f"Missing required key: {section}.{key}")
        
        # Validate data types
        if "database" in config:
            db_config = config["database"]
            if "port" in db_config and not isinstance(db_config["port"], int):
                errors.append("database.port must be an integer")
        
        if "api" in config:
            api_config = config["api"]
            if "timeout" in api_config and not isinstance(api_config["timeout"], int):
                errors.append("api.timeout must be an integer")
            if "debug" in api_config and not isinstance(api_config["debug"], bool):
                errors.append("api.debug must be a boolean")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_config_value(self, environment: str, key_path: str) -> Any:
        """
        Get a specific configuration value using dot notation.
        
        Args:
            environment: Environment name
            key_path: Dot-separated path to the config value (e.g., 'database.host')
            
        Returns:
            Configuration value or None if not found
        """
        try:
            config = self.load_config(environment)
            keys = key_path.split('.')
            
            value = config
            for key in keys:
                value = value[key]
                
            return value
            
        except (KeyError, FileNotFoundError) as e:
            self.logger.error(f"Configuration value not found: {key_path}")
            return None
    
    def set_config_value(self, environment: str, key_path: str, value: Any) -> bool:
        """
        Set a specific configuration value using dot notation.
        
        Args:
            environment: Environment name
            key_path: Dot-separated path to the config value
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config = self.load_config(environment)
            keys = key_path.split('.')
            
            # Navigate to the parent of the target key
            current = config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the value
            current[keys[-1]] = value
            
            # Save the updated configuration
            return self.save_config(environment, config)
            
        except Exception as e:
            self.logger.error(f"Failed to set configuration value: {e}")
            return False
    
    def list_environments(self) -> List[str]:
        """
        List all available environments.
        
        Returns:
            List of environment names
        """
        environments = []
        
        for file in self.config_path.glob("*.json"):
            env_name = file.stem
            environments.append(env_name)
        
        return sorted(environments)
    
    def list_backups(self, environment: str = None) -> List[str]:
        """
        List all available backups.
        
        Args:
            environment: Filter by environment (optional)
            
        Returns:
            List of backup filenames
        """
        if environment:
            pattern = f"{environment}_backup_*.json"
        else:
            pattern = "*_backup_*.json"
        
        backups = []
        for file in self.backup_path.glob(pattern):
            backups.append(file.name)
        
        return sorted(backups, reverse=True)  # Most recent first
    
    def compare_configs(self, env1: str, env2: str) -> Dict[str, Any]:
        """
        Compare configurations between two environments.
        
        Args:
            env1: First environment
            env2: Second environment
            
        Returns:
            Dictionary containing differences
        """
        try:
            config1 = self.load_config(env1)
            config2 = self.load_config(env2)
            
            differences = {}
            
            def compare_dicts(d1, d2, path=""):
                for key in set(d1.keys()) | set(d2.keys()):
                    current_path = f"{path}.{key}" if path else key
                    
                    if key not in d1:
                        differences[current_path] = {"in_" + env2: d2[key], "in_" + env1: "MISSING"}
                    elif key not in d2:
                        differences[current_path] = {"in_" + env1: d1[key], "in_" + env2: "MISSING"}
                    elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                        compare_dicts(d1[key], d2[key], current_path)
                    elif d1[key] != d2[key]:
                        differences[current_path] = {"in_" + env1: d1[key], "in_" + env2: d2[key]}
            
            compare_dicts(config1, config2)
            return differences
            
        except Exception as e:
            self.logger.error(f"Failed to compare configurations: {e}")
            return {}
    
    def export_config(self, environment: str, format: str = "json") -> str:
        """
        Export configuration to different formats.
        
        Args:
            environment: Environment name
            format: Export format ('json', 'yaml', 'env')
            
        Returns:
            Exported configuration as string
        """
        try:
            config = self.load_config(environment)
            
            if format.lower() == "json":
                return json.dumps(config, indent=4)
            elif format.lower() == "yaml":
                return yaml.dump(config, default_flow_style=False)
            elif format.lower() == "env":
                # Convert to environment variables format
                env_vars = []
                def flatten_dict(d, prefix=""):
                    for key, value in d.items():
                        if isinstance(value, dict):
                            flatten_dict(value, f"{prefix}{key.upper()}_")
                        else:
                            env_vars.append(f"{prefix}{key.upper()}={value}")
                
                flatten_dict(config)
                return "\n".join(env_vars)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return ""


class ConfigManagerCLI:
    """Command Line Interface for Configuration Manager."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def create_parser(self):
        """Create argument parser for CLI."""
        parser = argparse.ArgumentParser(
            description="Configuration Management System CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python config_manager.py list                              # List all environments
  python config_manager.py load development                  # Load development config
  python config_manager.py get development database.host     # Get specific value
  python config_manager.py set development database.host localhost  # Set specific value
  python config_manager.py backup development                # Create backup
  python config_manager.py compare development production    # Compare configs
  python config_manager.py export development yaml           # Export to YAML
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # List command
        list_parser = subparsers.add_parser('list', help='List environments or backups')
        list_parser.add_argument('--backups', action='store_true', help='List backups')
        list_parser.add_argument('--environment', '-e', help='Filter backups by environment')
        
        # Load command
        load_parser = subparsers.add_parser('load', help='Load and display configuration')
        load_parser.add_argument('environment', help='Environment name')
        
        # Get command
        get_parser = subparsers.add_parser('get', help='Get configuration value')
        get_parser.add_argument('environment', help='Environment name')
        get_parser.add_argument('key', help='Configuration key (dot notation)')
        
        # Set command
        set_parser = subparsers.add_parser('set', help='Set configuration value')
        set_parser.add_argument('environment', help='Environment name')
        set_parser.add_argument('key', help='Configuration key (dot notation)')
        set_parser.add_argument('value', help='Value to set')
        
        # Backup command
        backup_parser = subparsers.add_parser('backup', help='Create backup')
        backup_parser.add_argument('environment', help='Environment name')
        
        # Restore command
        restore_parser = subparsers.add_parser('restore', help='Restore from backup')
        restore_parser.add_argument('environment', help='Environment name')
        restore_parser.add_argument('timestamp', help='Backup timestamp')
        
        # Compare command
        compare_parser = subparsers.add_parser('compare', help='Compare configurations')
        compare_parser.add_argument('env1', help='First environment')
        compare_parser.add_argument('env2', help='Second environment')
        
        # Export command
        export_parser = subparsers.add_parser('export', help='Export configuration')
        export_parser.add_argument('environment', help='Environment name')
        export_parser.add_argument('format', choices=['json', 'yaml', 'env'], 
                                  default='json', help='Export format')
        
        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate configuration')
        validate_parser.add_argument('environment', help='Environment name')
        
        return parser
    
    def run(self):
        """Run the CLI."""
        parser = self.create_parser()
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
        
        try:
            if args.command == 'list':
                if args.backups:
                    backups = self.config_manager.list_backups(args.environment)
                    if backups:
                        print("Available backups:")
                        for backup in backups:
                            print(f"  {backup}")
                    else:
                        print("No backups found")
                else:
                    environments = self.config_manager.list_environments()
                    print("Available environments:")
                    for env in environments:
                        print(f"  {env}")
            
            elif args.command == 'load':
                config = self.config_manager.load_config(args.environment)
                print(f"Configuration for {args.environment}:")
                print(json.dumps(config, indent=2))
            
            elif args.command == 'get':
                value = self.config_manager.get_config_value(args.environment, args.key)
                if value is not None:
                    print(f"{args.key}: {value}")
                else:
                    print(f"Key '{args.key}' not found in {args.environment}")
            
            elif args.command == 'set':
                # Try to parse value as JSON, fallback to string
                try:
                    value = json.loads(args.value)
                except json.JSONDecodeError:
                    value = args.value
                
                success = self.config_manager.set_config_value(args.environment, args.key, value)
                if success:
                    print(f"Set {args.key} = {value} in {args.environment}")
                else:
                    print(f"Failed to set {args.key} in {args.environment}")
            
            elif args.command == 'backup':
                success = self.config_manager.create_backup(args.environment)
                if success:
                    print(f"Backup created for {args.environment}")
                else:
                    print(f"Failed to create backup for {args.environment}")
            
            elif args.command == 'restore':
                success = self.config_manager.restore_backup(args.environment, args.timestamp)
                if success:
                    print(f"Restored {args.environment} from backup {args.timestamp}")
                else:
                    print(f"Failed to restore {args.environment} from backup {args.timestamp}")
            
            elif args.command == 'compare':
                differences = self.config_manager.compare_configs(args.env1, args.env2)
                if differences:
                    print(f"Differences between {args.env1} and {args.env2}:")
                    for key, diff in differences.items():
                        print(f"  {key}:")
                        for env, value in diff.items():
                            print(f"    {env}: {value}")
                else:
                    print(f"No differences found between {args.env1} and {args.env2}")
            
            elif args.command == 'export':
                exported = self.config_manager.export_config(args.environment, args.format)
                if exported:
                    print(exported)
                else:
                    print(f"Failed to export {args.environment} configuration")
            
            elif args.command == 'validate':
                config = self.config_manager.load_config(args.environment)
                is_valid, errors = self.config_manager.validate_config(config)
                if is_valid:
                    print(f"Configuration for {args.environment} is valid")
                else:
                    print(f"Configuration for {args.environment} has errors:")
                    for error in errors:
                        print(f"  - {error}")
        
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


# Main execution
if __name__ == "__main__":
    cli = ConfigManagerCLI()
    cli.run()