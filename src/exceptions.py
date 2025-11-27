#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exceções customizadas para o sistema de correção de gabaritos
Fornece hierarquia de erros específicos para melhor tratamento
"""

class GabaritoProcessingError(Exception):
    """
    Exceção base para erros de processamento de gabarito
    Todas as exceções específicas devem herdar desta
    """
    pass


class ImageValidationError(GabaritoProcessingError):
    """
    Erro na validação da imagem de entrada
    
    Exemplos:
    - Formato de imagem inválido
    - Dimensões fora dos limites
    - Imagem corrompida
    - Tamanho de arquivo excedido
    """
    pass


class MarkerDetectionError(GabaritoProcessingError):
    """
    Erro na detecção de marcadores de alinhamento
    
    Exemplos:
    - Menos de 3 marcadores encontrados
    - Marcadores muito distorcidos
    - Marcadores não quadrados
    """
    def __init__(self, markers_found, markers_expected=4):
        self.markers_found = markers_found
        self.markers_expected = markers_expected
        message = f"Encontrados {markers_found} marcadores, esperado pelo menos 3 de {markers_expected}"
        super().__init__(message)


class BubbleDetectionError(GabaritoProcessingError):
    """
    Erro na detecção de bolhas de resposta
    
    Exemplos:
    - Número de bolhas incorreto
    - Bolhas muito pequenas ou grandes
    - Aspect ratio inválido
    """
    def __init__(self, bubbles_found, bubbles_expected):
        self.bubbles_found = bubbles_found
        self.bubbles_expected = bubbles_expected
        message = f"Encontradas {bubbles_found} bolhas, esperado {bubbles_expected}"
        super().__init__(message)


class PerspectiveTransformError(GabaritoProcessingError):
    """
    Erro na transformação de perspectiva
    
    Exemplos:
    - Pontos insuficientes para transformação
    - Matriz singular
    - Resultado inválido
    """
    pass


class AnswerExtractionError(GabaritoProcessingError):
    """
    Erro na extração de respostas
    
    Exemplos:
    - Marcação ambígua
    - Múltiplas respostas na mesma questão
    - Sem resposta detectada
    """
    def __init__(self, question_number, reason="Marcação ambígua"):
        self.question_number = question_number
        self.reason = reason
        message = f"Questão {question_number}: {reason}"
        super().__init__(message)


class GabaritoGenerationError(GabaritoProcessingError):
    """
    Erro na geração de gabarito PDF
    
    Exemplos:
    - Número de questões inválido
    - Falha ao criar PDF
    - Buffer de memória insuficiente
    """
    pass


class CacheError(Exception):
    """
    Erro relacionado ao cache
    
    Exemplos:
    - Falha ao armazenar no cache
    - Falha ao recuperar do cache
    - Cache corrompido
    """
    pass


class ConfigurationError(Exception):
    """
    Erro de configuração do sistema
    
    Exemplos:
    - Variável de ambiente ausente
    - Configuração inválida
    - Arquivo de config não encontrado
    """
    pass


class APIValidationError(Exception):
    """
    Erro de validação de entrada da API
    
    Exemplos:
    - Campo obrigatório ausente
    - Tipo de dados incorreto
    - Valor fora do intervalo permitido
    """
    def __init__(self, field, reason):
        self.field = field
        self.reason = reason
        message = f"Campo '{field}': {reason}"
        super().__init__(message)
