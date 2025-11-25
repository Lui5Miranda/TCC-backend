#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações do servidor de processamento de gabaritos
"""

import os
from typing import Set, Dict, Any

class Config:
    """Configuração base"""
    
    # Configurações de segurança
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024  # 64MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Configurações de processamento de imagem
    MIN_IMAGE_SIZE = (100, 100)
    MAX_IMAGE_SIZE = (8000, 8000)
    EXPECTED_BUBBLES = 200
    MIN_BUBBLE_SIZE = 18
    ASPECT_RATIO_RANGE = (0.8, 1.2)
    
    # Configurações de logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configurações de servidor
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = False

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"]

class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    # Em produção, especificar origens exatas
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else ["http://localhost:3000"]

class TestingConfig(Config):
    """Configuração para testes"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB para testes
    EXPECTED_BUBBLES = 10  # Menos bolhas para testes

def get_config() -> Config:
    """Retorna a configuração baseada no ambiente"""
    env = os.getenv('FLASK_ENV', 'development').lower()
    
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    return configs.get(env, DevelopmentConfig)()

# Configurações específicas do processamento de imagem
IMAGE_PROCESSING_CONFIG = {
    'alignment': {
        'blur_kernel': (5, 5),
        'threshold_method': 'OTSU',
        'min_marker_area': 100,
        'marker_aspect_ratio': (0.8, 1.2),
        'min_markers': 3,
        'max_markers': 4
    },
    'bubble_detection': {
        'adaptive_threshold': {
            'max_value': 255,
            'method': 'ADAPTIVE_THRESH_GAUSSIAN_C',
            'threshold_type': 'THRESH_BINARY_INV',
            'block_size': 25,
            'c': 5
        },
        'min_size': 18,
        'aspect_ratio': (0.8, 1.2),
        'expected_count': 200
    },
    'scoring': {
        'confidence_threshold': 1.5,  # Multiplicador para confiança
        'min_alternatives': 5
    }
}

# Configurações de validação
VALIDATION_RULES = {
    'image': {
        'required_fields': ['image'],
        'max_size_mb': 16,
        'min_dimensions': (100, 100),
        'max_dimensions': (4000, 4000)
    },
    'comparison': {
        'required_fields': ['student_answers', 'answer_key'],
        'max_questions': 1000
    }
}
