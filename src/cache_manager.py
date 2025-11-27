#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de cache para o processamento de imagens
Implementa cache em memória para evitar reprocessamento
"""

import hashlib
import time
import logging
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class ImageCache:
    """
    Cache em memória para resultados de processamento de imagens
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Inicializa o cache
        
        Args:
            max_size: Número máximo de itens no cache
            ttl_seconds: Tempo de vida dos itens em segundos
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = Lock()
        
        # Contadores para estatísticas
        self._hit_count = 0
        self._miss_count = 0
        
        logger.info(f"Cache inicializado: max_size={max_size}, ttl={ttl_seconds}s")
    
    def _generate_key(self, image_data: str) -> str:
        """
        Gera uma chave única para a imagem baseada no hash do conteúdo
        """
        # Usa apenas a parte base64 da imagem para gerar o hash
        if ',' in image_data:
            base64_part = image_data.split(',')[1]
        else:
            base64_part = image_data
            
        return hashlib.sha256(base64_part.encode()).hexdigest()[:16]
    
    def _is_expired(self, timestamp: float) -> bool:
        """
        Verifica se um item do cache expirou
        """
        return time.time() - timestamp > self.ttl_seconds
    
    def _cleanup_expired(self):
        """
        Remove itens expirados do cache
        """
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.access_times.items():
            if current_time - timestamp > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
        
        if expired_keys:
            logger.debug(f"Removidos {len(expired_keys)} itens expirados do cache")
    
    def _evict_lru(self):
        """
        Remove o item menos recentemente usado (LRU)
        """
        if not self.access_times:
            return
            
        # Encontra o item com timestamp mais antigo
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        self.cache.pop(oldest_key, None)
        self.access_times.pop(oldest_key, None)
        
        logger.debug(f"Item LRU removido: {oldest_key}")
    
    def get(self, image_data: str) -> Optional[Dict[str, Any]]:
        """
        Recupera um item do cache
        
        Args:
            image_data: Dados da imagem em base64
            
        Returns:
            Dados do cache ou None se não encontrado/expirado
        """
        with self.lock:
            key = self._generate_key(image_data)
            
            if key not in self.cache:
                self._miss_count += 1
                return None
            
            # Verifica se expirou
            if self._is_expired(self.access_times[key]):
                self.cache.pop(key, None)
                self.access_times.pop(key, None)
                logger.debug(f"Item expirado removido: {key}")
                self._miss_count += 1
                return None
            
            # Atualiza timestamp de acesso
            self.access_times[key] = time.time()
            self._hit_count += 1
            
            logger.debug(f"Cache hit: {key}")
            return self.cache[key]
    
    def set(self, image_data: str, result: Dict[str, Any]) -> None:
        """
        Armazena um item no cache
        
        Args:
            image_data: Dados da imagem em base64
            result: Resultado do processamento
        """
        with self.lock:
            key = self._generate_key(image_data)
            current_time = time.time()
            
            # Remove itens expirados antes de adicionar
            self._cleanup_expired()
            
            # Se o cache está cheio, remove o LRU
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            # Armazena o item
            self.cache[key] = result.copy()
            self.access_times[key] = current_time
            
            logger.debug(f"Item armazenado no cache: {key}")
    
    def clear(self) -> None:
        """
        Limpa todo o cache
        """
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            logger.info("Cache limpo")
    
    def stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        with self.lock:
            current_time = time.time()
            active_items = sum(1 for timestamp in self.access_times.values() 
                             if current_time - timestamp <= self.ttl_seconds)
            
            total_accesses = self._hit_count + self._miss_count
            hit_rate = self._hit_count / total_accesses if total_accesses > 0 else 0.0
            
            return {
                'total_items': len(self.cache),
                'active_items': active_items,
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds,
                'hit_count': self._hit_count,
                'miss_count': self._miss_count,
                'total_accesses': total_accesses,
                'hit_rate': round(hit_rate, 4)
            }

# Instância global do cache
image_cache = ImageCache(max_size=50, ttl_seconds=1800)  # 30 minutos TTL

def get_cached_result(image_data: str) -> Optional[Dict[str, Any]]:
    """
    Função de conveniência para recuperar resultado do cache
    """
    return image_cache.get(image_data)

def cache_result(image_data: str, result: Dict[str, Any]) -> None:
    """
    Função de conveniência para armazenar resultado no cache
    """
    image_cache.set(image_data, result)

def clear_cache() -> None:
    """
    Função de conveniência para limpar o cache
    """
    image_cache.clear()

def get_cache_stats() -> Dict[str, Any]:
    """
    Função de conveniência para obter estatísticas do cache
    """
    return image_cache.stats()
