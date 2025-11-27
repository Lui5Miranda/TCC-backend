#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para o módulo cache_manager
"""

import pytest
import time
from src.cache_manager import ImageCache


class TestImageCache:
    """Testes para a classe ImageCache"""
    
    def setup_method(self):
        """Configuração executada antes de cada teste"""
        self.cache = ImageCache(max_size=3, ttl_seconds=2)
    
    def test_cache_initialization(self):
        """Testa se o cache é inicializado corretamente"""
        assert self.cache.max_size == 3
        assert self.cache.ttl_seconds == 2
        assert len(self.cache.cache) == 0
        assert self.cache._hit_count == 0
        assert self.cache._miss_count == 0
    
    def test_cache_set_and_get(self):
        """Testa armazenamento e recuperação básica"""
        image_data = "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
        result = {"success": True, "data": "test"}
        
        # Armazena no cache
        self.cache.set(image_data, result)
        
        # Recupera do cache
        cached_result = self.cache.get(image_data)
        
        assert cached_result is not None
        assert cached_result["success"] == True
        assert cached_result["data"] == "test"
    
    def test_cache_miss(self):
        """Testa quando item não está no cache"""
        image_data = "data:image/jpeg;base64,nonexistent"
        result = self.cache.get(image_data)
        
        assert result is None
        assert self.cache._miss_count == 1
    
    def test_cache_hit_count(self):
        """Testa contagem de hits"""
        image_data = "data:image/jpeg;base64,/9j/test"
        result = {"success": True}
        
        self.cache.set(image_data, result)
        
        # Primeiro acesso
        self.cache.get(image_data)
        assert self.cache._hit_count == 1
        
        # Segundo acesso
        self.cache.get(image_data)
        assert self.cache._hit_count == 2
    
    def test_cache_ttl_expiration(self):
        """Testa se itens expiram após TTL"""
        image_data = "data:image/jpeg;base64,ttl_test"
        result = {"success": True}
        
        self.cache.set(image_data, result)
        
        # Imediatamente após adicionar, deve estar no cache
        assert self.cache.get(image_data) is not None
        
        # Aguarda expiração
        time.sleep(2.1)
        
        # Após TTL, deve retornar None
        assert self.cache.get(image_data) is None
    
    def test_cache_lru_eviction(self):
        """Testa remoção LRU quando cache está cheio"""
        # Adiciona 3 itens (limite do cache)
        for i in range(3):
            self.cache.set(f"data:image/jpeg;base64,item{i}", {"id": i})
        
        # Acessa item 0 e 1 para tornar item 2 o LRU
        self.cache.get("data:image/jpeg;base64,item0")
        self.cache.get("data:image/jpeg;base64,item1")
        
        # Adiciona novo item, deve remover item2 (LRU)
        self.cache.set("data:image/jpeg;base64,item3", {"id": 3})
        
        # Item 2 deve ter sido removido
        assert self.cache.get("data:image/jpeg;base64,item2") is None
        # Outros itens devem existir
        assert self.cache.get("data:image/jpeg;base64,item0") is not None
        assert self.cache.get("data:image/jpeg;base64,item3") is not None
    
    def test_cache_clear(self):
        """Testa limpeza do cache"""
        # Adiciona alguns itens
        for i in range(2):
            self.cache.set(f"data:image/jpeg;base64,clear{i}", {"id": i})
        
        # Limpa o cache
        self.cache.clear()
        
        # Verifica se está vazio
        assert len(self.cache.cache) == 0
        assert self.cache.get("data:image/jpeg;base64,clear0") is None
    
    def test_cache_stats(self):
        """Testa estatísticas do cache"""
        # Adiciona item
        self.cache.set("data:image/jpeg;base64,stats", {"data": "test"})
        
        # Acessa (hit)
        self.cache.get("data:image/jpeg;base64,stats")
        
        # Tenta acessar item inexistente (miss)
        self.cache.get("data:image/jpeg;base64,nonexistent")
        
        stats = self.cache.stats()
        
        assert stats['total_items'] == 1
        assert stats['max_size'] == 3
        assert stats['hit_count'] == 1
        assert stats['miss_count'] == 1
        assert stats['total_accesses'] == 2
        assert stats['hit_rate'] == 0.5  # 1 hit / 2 total
    
    def test_cache_generate_key_consistency(self):
        """Testa se a geração de chave é consistente"""
        image_data = "data:image/jpeg;base64,/9j/test"
        
        key1 = self.cache._generate_key(image_data)
        key2 = self.cache._generate_key(image_data)
        
        assert key1 == key2
    
    def test_cache_different_images_different_keys(self):
        """Testa se imagens diferentes geram chaves diferentes"""
        image1 = "data:image/jpeg;base64,ABC123"
        image2 = "data:image/jpeg;base64,XYZ789"
        
        key1 = self.cache._generate_key(image1)
        key2 = self.cache._generate_key(image2)
        
        assert key1 != key2
