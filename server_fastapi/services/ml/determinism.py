import logging
import os
import random

import numpy as np

logger = logging.getLogger(__name__)


def set_global_seed(seed: int = 42):
    """
    Set global seed for all ML-related libraries to ensure determinism.
    (2026 Production Standard)
    """
    logger.info(f"Setting global ML seed: {seed}")

    # Python random
    random.seed(seed)

    # Numpy
    np.random.seed(seed)

    # OS level
    os.environ["PYTHONHASHSEED"] = str(seed)

    # TensorFlow
    try:
        import tensorflow as tf

        tf.random.set_seed(seed)
        # For GPU determinism (can impact performance)
        os.environ["TF_DETERMINISTIC_OPS"] = "1"
        os.environ["TF_CUDNN_DETERMINISTIC"] = "1"
        logger.debug("TensorFlow seed set.")
    except ImportError:
        pass

    # PyTorch
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        logger.debug("PyTorch seed set.")
    except ImportError:
        pass

    logger.info("Global ML determinism established.")
