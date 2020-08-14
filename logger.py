import logging


def get_logger(name):
    _logger = logging.Logger(name, level=logging.DEBUG)
    file_handler = logging.FileHandler('./tictacdrop.log')
    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    _logger.addHandler(file_handler)
    _logger.addHandler(stream_handler)

    return _logger