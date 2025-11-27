#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes para o módulo server (API endpoints)
"""

import pytest
import json
import base64
from src.server import app


@pytest.fixture
def client():
    """Fixture que fornece um cliente de teste do Flask"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Testes para o endpoint /api/health"""
    
    def test_health_check(self, client):
        """Testa se o endpoint de health check funciona"""
        response = client.get('/api/health')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['status'] == 'ok'
        assert 'timestamp' in data


class TestGenerateGabaritoEndpoint:
    """Testes para o endpoint /api/generate-gabarito"""
    
    def test_generate_gabarito_success(self, client):
        """Testa geração de gabarito com parâmetros válidos"""
        payload = {"num_questions": 40}
        response = client.post(
            '/api/generate-gabarito',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert 'pdf_content' in data
        assert data['num_questions'] == 40
    
    def test_generate_gabarito_invalid_number(self, client):
        """Testa geração com número inválido de questões"""
        payload = {"num_questions": 150}  # Acima do máximo (100)
        response = client.post(
            '/api/generate-gabarito',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data['success'] == False
    
    def test_generate_gabarito_missing_field(self, client):
        """Testa geração sem campo obrigatório"""
        payload = {}  # Sem num_questions
        response = client.post(
            '/api/generate-gabarito',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data['success'] == False
    
    def test_generate_gabarito_wrong_content_type(self, client):
        """Testa requisição com Content-Type incorreto"""
        response = client.post(
            '/api/generate-gabarito',
            data="num_questions=40",
            content_type='text/plain'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data['success'] == False


class TestProcessEndpoint:
    """Testes para o endpoint /api/process"""
    
    def test_process_missing_image(self, client):
        """Testa processamento sem imagem"""
        payload = {
            "gabarito": {
                "id": "test",
                "questions": [{"id": 1, "correctAnswer": "A"}]
            }
        }
        response = client.post(
            '/api/process',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data['success'] == False
    
    def test_process_missing_gabarito(self, client):
        """Testa processamento sem gabarito de referência"""
        payload = {
            "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
        }
        response = client.post(
            '/api/process',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data['success'] == False
    
    def test_process_invalid_json(self, client):
        """Testa requisição com JSON inválido"""
        response = client.post(
            '/api/process',
            data="{invalid json}",
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestCacheStatsEndpoint:
    """Testes para o endpoint /api/cache/stats"""
    
    def test_cache_stats(self, client):
        """Testa obtenção de estatísticas do cache"""
        response = client.get('/api/cache/stats')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert 'cache_stats' in data
        assert 'total_items' in data['cache_stats']
        assert 'hit_rate' in data['cache_stats']


class TestCompareEndpoint:
    """Testes para o endpoint /api/compare"""
    
    def test_compare_answers(self, client):
        """Testa comparação de respostas"""
        payload = {
            "student_answers": {"1": "A", "2": "B", "3": "C"},
            "answer_key": {"1": "A", "2": "B", "3": "D"}
        }
        response = client.post(
            '/api/compare',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert data['score'] == 66.67  # 2 de 3 corretas
        assert data['correct'] == 2
        assert data['total'] == 3
    
    def test_compare_missing_fields(self, client):
        """Testa comparação sem campos obrigatórios"""
        payload = {"student_answers": {"1": "A"}}  # Falta answer_key
        response = client.post(
            '/api/compare',
            data=json.dumps(payload),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data['success'] == False
