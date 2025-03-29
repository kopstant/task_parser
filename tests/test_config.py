import unittest
from unittest.mock import patch
import os
from src.config import Config


class TestConfig(unittest.TestCase):

    @patch.dict(os.environ, {'TELEGRAM_TOKEN': 'dummy_token'})
    def test_telegram_token(self):
        config = Config()
        self.assertEqual(config.TELEGRAM_TOKEN, 'dummy_token')


    @patch.dict(os.environ, {'POSTGRES_HOST': 'db'})
    def test_postgres_host_default(self):
        config = Config()
        self.assertEqual(config.POSTGRES_HOST, 'db')

    @patch.dict(os.environ, {'POSTGRES_PORT': '5432'})
    def test_postgres_port(self):
        config = Config()
        self.assertEqual(config.POSTGRES_PORT, '5432')

    @patch.dict(os.environ, {'POSTGRES_USER': 'postgres'})
    def test_postgres_user(self):
        config = Config()
        self.assertEqual(config.POSTGRES_USER, 'postgres')

    @patch.dict(os.environ, {'POSTGRES_PASSWORD': 'b20d5fcd', 'POSTGRES_HOST': 'db'})
    def test_postgres_password(self):
        config = Config()
        self.assertEqual(config.POSTGRES_PASSWORD, 'b20d5fcd')


    @patch.dict(os.environ, {'POSTGRES_HOST': 'db', 'POSTGRES_USER': 'postgres', 'POSTGRES_PASSWORD': 'b20d5fcd'})
    def test_postgres_configuration(self):
        config = Config()
        self.assertEqual(config.POSTGRES_HOST, 'db')
        self.assertEqual(config.POSTGRES_USER, 'postgres')
        self.assertEqual(config.POSTGRES_PASSWORD, 'b20d5fcd')


if __name__ == '__main__':
    unittest.main()
