#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Flask para processamento de gabaritos
Integra o web app com o script de análise de imagens
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import numpy as np
from imutils import contours
import base64
import io
import os
import json
import logging
import re
from datetime import datetime
from functools import wraps
from config import get_config, IMAGE_PROCESSING_CONFIG, VALIDATION_RULES
from image_processor import process_gabarito_image
from cache_manager import get_cached_result, cache_result, get_cache_stats
from gabarito_generator_v2 import generate_standard_gabarito_v2

# Carrega configurações
config = get_config()

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Configuração CORS baseada no ambiente
CORS(app, origins=config.CORS_ORIGINS)

# Aplica configurações do Flask
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = config.ALLOWED_EXTENSIONS
app.config['DEBUG'] = config.DEBUG

# Criar diretório de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ====================================================================================
# FUNÇÕES DE VALIDAÇÃO E SEGURANÇA
# ====================================================================================

def validate_base64_image(image_data):
    """
    Valida se a string base64 é uma imagem válida
    """
    try:
        # Verifica se tem o prefixo data:image
        if not image_data.startswith('data:image/'):
            return False, "Formato de imagem inválido"
        
        # Extrai o tipo MIME
        mime_match = re.match(r'data:image/([^;]+)', image_data)
        if not mime_match:
            return False, "Tipo MIME inválido"
        
        image_type = mime_match.group(1).lower()
        if image_type not in app.config['ALLOWED_EXTENSIONS']:
            return False, f"Tipo de imagem não suportado: {image_type}"
        
        # Verifica se tem a parte base64
        if ',' not in image_data:
            return False, "Formato base64 inválido"
        
        base64_part = image_data.split(',')[1]
        
        # Verifica se é base64 válido
        try:
            decoded = base64.b64decode(base64_part)
            if len(decoded) > app.config['MAX_CONTENT_LENGTH']:
                return False, "Imagem muito grande"
        except Exception:
            return False, "Base64 inválido"
        
        return True, "Válido"
        
    except Exception as e:
        return False, f"Erro na validação: {str(e)}"

def validate_json_data(data, required_fields):
    """
    Valida se os dados JSON contêm os campos obrigatórios
    """
    if not isinstance(data, dict):
        return False, "Dados devem ser um objeto JSON"
    
    for field in required_fields:
        if field not in data:
            return False, f"Campo obrigatório ausente: {field}"
    
    return True, "Válido"

def handle_errors(f):
    """
    Decorator para tratamento centralizado de erros
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro em {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor',
                'message': str(e) if app.debug else 'Erro interno do servidor'
            }), 500
    return decorated_function

# ====================================================================================
# FUNÇÕES DE PROCESSAMENTO DE IMAGEM
# ====================================================================================

def process_image(image_data, num_questions=None):
    """
    Processa uma imagem de gabarito e retorna as respostas detectadas
    """
    try:
        # Valida a imagem antes de processar
        is_valid, message = validate_base64_image(image_data)
        if not is_valid:
            raise Exception(f"Imagem inválida: {message}")
        
        logger.info("Iniciando processamento de imagem")
        
        # Decodifica a imagem base64
        image_bytes = base64.b64decode(image_data.split(',')[1])
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise Exception("Não foi possível decodificar a imagem")
        
        # Valida dimensões da imagem
        height, width = img.shape[:2]
        min_w, min_h = config.MIN_IMAGE_SIZE
        max_w, max_h = config.MAX_IMAGE_SIZE
        
        if width < min_w or height < min_h:
            raise Exception(f"Imagem muito pequena para processamento (mínimo: {min_w}x{min_h})")
        if width > max_w or height > max_h:
            raise Exception(f"Imagem muito grande para processamento (máximo: {max_w}x{max_h})")
        
        logger.info(f"Imagem decodificada: {width}x{height} pixels")
        
        # Verifica se o resultado está no cache
        # Nota: O cache deve considerar o num_questions também, mas por enquanto vamos manter simples
        # Se num_questions mudar, o conteúdo da imagem provavelmente é diferente ou irrelevante se for a mesma imagem
        cached_result = get_cached_result(image_data)
        if cached_result:
            logger.info("Resultado encontrado no cache")
            return cached_result
        
        # Processa a imagem usando o módulo especializado
        result = process_gabarito_image(img, num_questions)
        
        if result['success']:
            # Converte a imagem de resultado para base64
            _, buffer = cv2.imencode('.jpg', result['result_image'])
            result_image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            final_result = {
                'success': True,
                'answers': result['answers'],
                'result_image': f"data:image/jpeg;base64,{result_image_base64}",
                'total_questions': result['total_questions']
            }
            
            # Armazena no cache
            cache_result(image_data, final_result)
            
            return final_result
        else:
            return result
        
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ====================================================================================
# ROTAS DA API
# ====================================================================================

@app.route('/api/process', methods=['POST'])
@handle_errors
def process_gabarito():
    """
    Endpoint para processar uma imagem de gabarito
    """
    # Valida se é JSON
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Content-Type deve ser application/json'}), 400
    
    data = request.get_json()
    
    # Valida dados obrigatórios
    required_fields = ['image']
    is_valid, message = validate_json_data(data, required_fields)
    if not is_valid:
        return jsonify({'success': False, 'error': message}), 400
    
    # Valida se a imagem não está vazia
    if not data['image'] or not data['image'].strip():
        return jsonify({'success': False, 'error': 'Imagem não pode estar vazia'}), 400
    
    # Verifica se há gabarito de referência
    if 'gabarito' not in data:
        return jsonify({'success': False, 'error': 'Gabarito de referência não fornecido'}), 400
    
    gabarito = data['gabarito']
    if not gabarito or not gabarito.get('questions'):
        return jsonify({'success': False, 'error': 'Gabarito de referência inválido'}), 400
    
    logger.info("Processando gabarito")
    
    # Determina o número de questões do gabarito
    num_questions = len(gabarito['questions'])
    logger.info(f"Gabarito possui {num_questions} questões")
    
    result = process_image(data['image'], num_questions)
    
    if result['success']:
        # Compara com o gabarito selecionado
        student_answers = result['answers']
        correct_answers = {}
        
        # Converte o gabarito para o formato esperado
        for question in gabarito['questions']:
            correct_answers[question['id']] = question['correctAnswer']
        
        # Log de debug do gabarito recebido
        logger.info(f"Gabarito recebido: {gabarito}")
        logger.info(f"Questões do gabarito: {[{'id': q['id'], 'answer': q['correctAnswer']} for q in gabarito['questions'][:5]]}")
        
        # Log de debug para as primeiras 5 questões
        logger.info(f"Respostas do aluno: {dict(list(student_answers.items())[:5])}")
        logger.info(f"Gabarito correto: {dict(list(correct_answers.items())[:5])}")
        
        # Calcula a pontuação
        correct = 0
        total = len(correct_answers)
        details = {}
        
        for question_num, correct_answer in correct_answers.items():
            student_answer = student_answers.get(question_num, 'NÃO MARCADA')
            is_correct = student_answer == correct_answer
            if is_correct:
                correct += 1
            
            details[question_num] = {
                'student': student_answer,
                'correct': correct_answer,
                'is_correct': is_correct
            }
            
            # Log de debug para as primeiras 5 questões
            if question_num <= 5:
                logger.info(f"Questão {question_num}: Aluno={student_answer}, Correto={correct_answer}, Acertou={is_correct}")
        
        score = (correct / total) * 100 if total > 0 else 0
        
        logger.info(f"Comparação concluída: {correct}/{total} ({score:.2f}%)")
        
        # Adiciona os resultados da comparação ao resultado
        result['comparison'] = {
            'score': round(score, 2),
            'correct': correct,
            'total': total,
            'details': details
        }
        
        logger.info(f"Processamento concluído: {result['total_questions']} questões detectadas")
    else:
        logger.warning(f"Falha no processamento: {result['error']}")
    
    return jsonify(result)

@app.route('/api/generate-gabarito', methods=['POST'])
@handle_errors
def generate_gabarito():
    """
    Endpoint para gerar gabarito padronizado em PDF
    """
    # Valida se é JSON
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Content-Type deve ser application/json'}), 400
    
    data = request.get_json()
    
    # Valida dados obrigatórios
    if 'num_questions' not in data:
        return jsonify({'success': False, 'error': 'Campo num_questions é obrigatório'}), 400
    
    num_questions = data['num_questions']
    
    # Valida número de questões
    if not isinstance(num_questions, int) or num_questions < 1 or num_questions > 100:
        return jsonify({'success': False, 'error': 'Número de questões deve ser um inteiro entre 1 e 100'}), 400
    
    try:
        logger.info(f"Gerando gabarito com {num_questions} questões")
        
        # Gera o PDF
        pdf_content = generate_standard_gabarito_v2(num_questions)
        
        # Converte para base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        logger.info(f"Gabarito gerado com sucesso: {len(pdf_content)} bytes")
        
        return jsonify({
            'success': True,
            'pdf_content': pdf_base64,
            'num_questions': num_questions,
            'file_size': len(pdf_content),
            'message': f'Gabarito gerado com {num_questions} questões'
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar gabarito: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao gerar gabarito: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Endpoint para verificar se o servidor está funcionando
    """
    return jsonify({
        'status': 'ok',
        'message': 'Servidor de processamento funcionando',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """
    Endpoint para obter estatísticas do cache
    """
    try:
        stats = get_cache_stats()
        return jsonify({
            'success': True,
            'cache_stats': stats
        })
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/compare', methods=['POST'])
@handle_errors
def compare_answers():
    """
    Endpoint para comparar respostas do aluno com o gabarito
    """
    # Valida se é JSON
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Content-Type deve ser application/json'}), 400
    
    data = request.get_json()
    
    # Valida dados obrigatórios
    required_fields = VALIDATION_RULES['comparison']['required_fields']
    is_valid, message = validate_json_data(data, required_fields)
    if not is_valid:
        return jsonify({'success': False, 'error': message}), 400
    
    student_answers = data['student_answers']
    answer_key = data['answer_key']
    
    # Valida se são dicionários
    if not isinstance(student_answers, dict) or not isinstance(answer_key, dict):
        return jsonify({'success': False, 'error': 'Respostas e gabarito devem ser objetos'}), 400
    
    # Valida se o gabarito não está vazio
    if not answer_key:
        return jsonify({'success': False, 'error': 'Gabarito não pode estar vazio'}), 400
    
    logger.info(f"Comparando respostas: {len(student_answers)} respostas do aluno vs {len(answer_key)} do gabarito")
    
    # Calcula a pontuação
    correct = 0
    total = len(answer_key)
    details = {}
    
    for question_num, correct_answer in answer_key.items():
        # Valida se a questão tem resposta válida
        if not isinstance(question_num, (int, str)):
            continue
            
        student_answer = student_answers.get(question_num, 'NÃO MARCADA')
        is_correct = student_answer == correct_answer
        if is_correct:
            correct += 1
        
        details[question_num] = {
            'student': student_answer,
            'correct': correct_answer,
            'is_correct': is_correct
        }
    
    score = (correct / total) * 100 if total > 0 else 0
    
    logger.info(f"Comparação concluída: {correct}/{total} ({score:.2f}%)")
    
    return jsonify({
        'success': True,
        'score': round(score, 2),
        'correct': correct,
        'total': total,
        'details': details
    })

if __name__ == '__main__':
    # Configuração baseada no ambiente
    debug_mode = os.getenv('FLASK_DEBUG', str(config.DEBUG)).lower() == 'true'
    port = int(os.getenv('PORT', config.PORT))
    host = os.getenv('HOST', config.HOST)
    
    print("Iniciando servidor de processamento de gabaritos...")
    print(f"Servidor rodando em: http://{host}:{port}")
    print(f"Modo debug: {'Ativado' if debug_mode else 'Desativado'}")
    print(f"Ambiente: {os.getenv('FLASK_ENV', 'development')}")
    print("Endpoints disponíveis:")
    print("   - POST /api/process - Processar imagem")
    print("   - POST /api/compare - Comparar respostas")
    print("   - GET /api/health - Status do servidor")
    print("Configurações de segurança:")
    print(f"   - Tamanho máximo de upload: {config.MAX_CONTENT_LENGTH / (1024*1024):.1f}MB")
    print(f"   - Tipos de imagem permitidos: {', '.join(config.ALLOWED_EXTENSIONS)}")
    print(f"   - CORS restrito para: {', '.join(config.CORS_ORIGINS)}")
    print(f"   - Dimensões mínimas: {config.MIN_IMAGE_SIZE}")
    print(f"   - Dimensões máximas: {config.MAX_IMAGE_SIZE}")
    
    app.run(debug=debug_mode, host=host, port=port)
