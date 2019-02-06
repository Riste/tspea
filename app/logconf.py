import os
import json
import logging.config


def setup_logging(
        out_dir,
        default_path='logging.json',
        default_level=logging.INFO,
        env_key='LOG_CFG',
):
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config_content = f.read()
            config = json.loads(config_content.replace('@@out@@', out_dir))
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
