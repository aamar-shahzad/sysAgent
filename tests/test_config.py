import unittest
from pathlib import Path
import os
import json
from sysagent.core.config import ConfigManager
from sysagent.types import Config, AgentConfig, SecurityConfig, LLMProvider

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("test_config_dir")
        self.test_dir.mkdir(exist_ok=True)
        self.manager = ConfigManager(config_dir=str(self.test_dir))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_create_default_config(self):
        config = self.manager._create_default_config()
        self.assertIsInstance(config, Config)
        self.assertIsInstance(config.agent, AgentConfig)
        self.assertIsInstance(config.security, SecurityConfig)
        self.assertEqual(config.agent.provider, LLMProvider.OPENAI)

    def test_save_and_load_config(self):
        config = self.manager.load_config()
        self.manager.save_config()
        
        new_manager = ConfigManager(config_dir=str(self.test_dir))
        loaded_config = new_manager.load_config()
        
        self.assertEqual(config.agent.model, loaded_config.agent.model)
        self.assertEqual(config.security.dry_run, loaded_config.security.dry_run)

if __name__ == '__main__':
    unittest.main() 