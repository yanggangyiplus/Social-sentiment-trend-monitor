"""
랜덤 시드 고정 모듈
"""
import random
import numpy as np
import torch


def set_seed(seed: int = 42):
    """
    모든 랜덤 시드 고정
    
    Args:
        seed: 시드 값
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

