#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de gabaritos padronizados em PDF - Versão 2
Cria gabaritos idênticos à imagem com bolinhas e quadrados
"""

import os
import io
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import black, white
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

logger = logging.getLogger(__name__)

class GabaritoGeneratorV2:
    """
    Classe para gerar gabaritos padronizados em PDF - Versão 2
    """
    
    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 2*cm
        
    def generate_gabarito_pdf(self, num_questions):
        """
        Gera um gabarito padronizado em PDF com bolinhas e quadrados
        """
        if num_questions > 100:
            raise ValueError("Número máximo de questões é 100")
        if num_questions < 1:
            raise ValueError("Número mínimo de questões é 1")
            
        # Cria buffer para o PDF
        buffer = io.BytesIO()
        
        # Cria o canvas
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Desenha o gabarito
        self._draw_gabarito(c, num_questions)
        
        # Finaliza o PDF
        c.save()
        
        # Retorna o conteúdo
        buffer.seek(0)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Gabarito gerado com {num_questions} questões")
        return pdf_content
    
    def _draw_gabarito(self, c, num_questions):
        """
        Desenha o gabarito completo
        """
        # Desenha os 4 quadrados pretos nos cantos
        self._draw_corner_markers(c)
        
        # Desenha o título "RESPOSTAS"
        self._draw_title(c)
        
        # Desenha as questões com bolinhas
        self._draw_questions(c, num_questions)
    
    def _draw_corner_markers(self, c):
        """
        Desenha os 4 quadrados pretos nos cantos
        """
        marker_size = 0.4*cm
        
        # Quadrado superior direito
        c.setFillColor(colors.black)
        c.rect(self.page_width - 1.5*cm, self.page_height - 1.5*cm, marker_size, marker_size, fill=1)
        
        # Quadrado superior esquerdo
        c.rect(1.1*cm, self.page_height - 1.5*cm, marker_size, marker_size, fill=1)
        
        # Quadrado inferior direito
        c.rect(self.page_width - 1.5*cm, 1.1*cm, marker_size, marker_size, fill=1)
        
        # Quadrado inferior esquerdo
        c.rect(1.1*cm, 1.1*cm, marker_size, marker_size, fill=1)
    
    def _draw_title(self, c):
        """
        Desenha o título "RESPOSTAS"
        """
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(colors.black)
        c.drawString(1.3*cm, self.page_height - 2.2*cm, "RESPOSTAS")
    
    def _draw_questions(self, c, num_questions):
        """
        Desenha as questões com bolinhas
        """
        # Configurações exatas como na imagem
        left_margin = 1.3*cm  # Margem esquerda (após quadrado)
        right_margin = 1.5*cm  # Margem direita (antes do quadrado)
        available_width = self.page_width - left_margin - right_margin
        
        start_x = left_margin
        start_y = self.page_height - 3.5*cm
        end_y = 1.5*cm  # Altura mínima para os quadrados inferiores
        question_spacing = 0.5*cm
        column_spacing = available_width / 3  # Divide o espaço disponível em 3 colunas iguais
        bubble_size = 0.5*cm  # Bolinhas do tamanho da imagem
        bubble_spacing = 0.6*cm
        
        # Calcula o espaço vertical disponível
        available_height = start_y - end_y
        questions_per_column = (num_questions + 2) // 3
        
        # Ajusta o espaçamento para ficar exatamente como na imagem
        if questions_per_column > 0:
            question_spacing = available_height / questions_per_column
            question_spacing = max(0.5*cm, min(question_spacing, 0.6*cm))  # Limita entre 0.5cm e 0.6cm
        
        for col in range(3):
            col_x = start_x + col * column_spacing
            
            for row in range(questions_per_column):
                question_num = row + 1 + col * questions_per_column
                
                if question_num > num_questions:
                    break
                
                y_pos = start_y - row * question_spacing
                
                # Desenha o número da questão
                c.setFont("Helvetica-Bold", 11)
                c.drawString(col_x, y_pos, f"{question_num:02d} -")
                
                # Desenha as bolinhas A, B, C, D, E - exatamente como na imagem
                bubble_start_x = col_x + 1.4*cm
                bubble_center_y = y_pos + 0.1*cm  # Alinhamento vertical
                
                for i, letter in enumerate(['A', 'B', 'C', 'D', 'E']):
                    bubble_center_x = bubble_start_x + i * bubble_spacing
                    
                    # Desenha o círculo (bolinha) - tamanho exato da imagem
                    c.setStrokeColor(colors.black)
                    c.setFillColor(colors.white)
                    c.circle(bubble_center_x, bubble_center_y, bubble_size/2, fill=1, stroke=1)
                    
                    # Desenha a letra dentro da bolinha - tamanho exato
                    c.setFont("Helvetica-Bold", 9)
                    c.setFillColor(colors.black)
                    c.drawCentredString(bubble_center_x, bubble_center_y - 0.1*cm, letter)

def generate_standard_gabarito_v2(num_questions):
    """
    Função principal para gerar gabarito padronizado - Versão 2
    """
    try:
        generator = GabaritoGeneratorV2()
        pdf_content = generator.generate_gabarito_pdf(num_questions)
        
        logger.info(f"Gabarito padronizado v2 gerado com {num_questions} questões")
        return pdf_content
        
    except Exception as e:
        logger.error(f"Erro ao gerar gabarito v2: {str(e)}")
        raise
