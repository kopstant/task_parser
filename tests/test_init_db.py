import pytest
from unittest.mock import patch, MagicMock, create_autospec
from sqlalchemy import text, create_engine
from src.database.init_db import init_db, main, check_db_connection
from src.database.base import Base, engine

@pytest.fixture
def mock_engine():
    mock = create_autospec(create_engine("sqlite:///:memory:"))
    mock_connection = MagicMock()
    mock_connection.execute.return_value = MagicMock()
    mock_connection.execute.return_value.scalar.return_value = 1
    mock.connect.return_value = mock_connection
    mock.connect.return_value.__enter__ = MagicMock(return_value=mock_connection)
    mock.connect.return_value.__exit__ = MagicMock(return_value=None)
    return mock

@pytest.fixture
def mock_base():
    mock = create_autospec(Base)
    mock.metadata = MagicMock()
    return mock

@pytest.fixture
def mock_parse():
    with patch('src.database.init_db.parse_and_save_problems', autospec=True) as mock:
        mock.return_value = {'status': 'success', 'count': 10}
        yield mock

@pytest.fixture
def mock_sys_exit():
    with patch('src.database.init_db.sys.exit', autospec=True) as mock:
        yield mock

def test_check_db_connection(mock_engine):
    """Тест проверки подключения к БД"""
    with patch('src.database.base.engine', mock_engine):
        # Вызываем функцию
        result = check_db_connection()
        
        # Проверяем результат
        assert result is True
        mock_engine.connect.assert_called_once()
        mock_engine.connect.return_value.__enter__.assert_called_once()
        mock_engine.connect.return_value.execute.assert_called_once_with(text("SELECT 1"))

def test_check_db_connection_failure(mock_engine):
    """Тест неудачного подключения к БД"""
    mock_engine.connect.side_effect = Exception("Connection error")
    
    with patch('src.database.base.engine', mock_engine):
        # Вызываем функцию
        result = check_db_connection()
        
        # Проверяем результат
        assert result is False
        mock_engine.connect.assert_called_once()

def test_init_db(mock_base, mock_engine):
    """Тест инициализации БД"""
    with patch('src.database.base.Base', mock_base), \
         patch('src.database.base.engine', mock_engine), \
         patch('src.database.init_db.check_db_connection', return_value=True):
        # Вызываем функцию
        init_db()
        
        # Проверяем, что таблицы были созданы
        mock_base.metadata.create_all.assert_called_once_with(mock_engine)

def test_main_success(mock_base, mock_parse):
    """Тест успешного выполнения main()"""
    with patch('src.database.base.Base', mock_base), \
         patch('src.database.init_db.init_db') as mock_init_db, \
         patch('src.database.init_db.check_db_connection', return_value=True), \
         patch('src.database.init_db.sys.exit') as mock_exit, \
         patch('src.database.init_db.parse_and_save_problems', return_value={'status': 'success', 'count': 10}):
        # Вызываем функцию
        main()
        
        # Проверяем вызовы
        mock_init_db.assert_called_once()
        mock_parse.assert_called_once()
        mock_exit.assert_called_once_with(0)

def test_main_error(mock_base, mock_parse, mock_sys_exit):
    """Тест обработки ошибки в main()"""
    # Настраиваем мок для имитации ошибки
    mock_base.metadata.create_all.side_effect = Exception("Database Error")
    
    # Вызываем функцию
    main()
    
    # Проверяем, что произошел выход с ошибкой
    mock_sys_exit.assert_called_once_with(1)

def test_main_timeout(mock_base, mock_parse, mock_sys_exit):
    """Тест таймаута в main()"""
    # Настраиваем мок для имитации таймаута
    def slow_parse(*args, **kwargs):
        import time
        time.sleep(301)  # Больше чем таймаут в 300 секунд
        return {'status': 'success'}
    
    mock_parse.side_effect = slow_parse
    
    # Вызываем функцию
    main()
    
    # Проверяем, что произошел выход с ошибкой
    mock_sys_exit.assert_called_once_with(1) 