#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/1 11:59
@Author  : adamzh0u
@File    : const.py
"""

import glob
import os
import tomllib
from pathlib import Path

from loguru import logger

# Base config file that contains default settings
CONFIG_DIR = "./config"
# Environment variable to control which config to load
ENV = os.getenv("ENV", "dev")


def load_config(env: str = ENV):
    """
    Load configuration from the config directory.
    :param env: str, the environment to load the config for
    :return: dict, the loaded configuration
    """
    # 首先加载基础配置
    final_config = {}
    for file in glob.glob(os.path.join(CONFIG_DIR, "*.toml")):
        with open(file, "rb") as f:
            config = tomllib.load(f)
        final_config.update(config)
    return final_config


try:
    CONFIG = load_config(ENV)
except (TypeError, ValueError) as e:
    logger.error(f"Error loading configuration: {e}")
    raise e


def get_project_root():
    """Search upwards to find the project root directory."""
    current_path = Path.cwd()
    while True:
        if (
            (current_path / ".git").exists()
            or (current_path / ".project_root").exists()
            or (current_path / ".gitignore").exists()
        ):
            logger.info(f"PROJECT_ROOT set to {str(current_path)}")
            return current_path
        parent_path = current_path.parent
        if parent_path == current_path:
            # loop until top level and land cwd
            cwd = Path.cwd()
            logger.info(f"PROJECT_ROOT set to current working directory: {str(cwd)}")
            return cwd
        current_path = parent_path


def get_logger():
    return logger


ROOT = get_project_root()
PATH_DATA = ROOT / "data"
PATH_NOOTBOOKS = ROOT / "notebooks"
PATH_LOG = ROOT / "logs"

if __name__ == "__main__":
    print(CONFIG)

    # print(os.environ["PYTHONPATH"])
    # print(os.environ["PATH"])
    print(ROOT)
    # print(os.environ["ENV_PARM"])  # params in .env file
