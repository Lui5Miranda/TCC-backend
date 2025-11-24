#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de gabaritos padronizados em PDF
Cria gabaritos otimizados para leitura automática
"""

import os
import io
import logging
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import black, white, lightgrey
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime

logger = logging.getLogger(__name__)

class GabaritoGenerator:
    """
    Classe para gerar gabaritos padronizados em PDF
    """
    
    def __init__(self):
        self.page_width, self.page_height = A4
        self.margin = 2*cm
        self.bubble_size = 4*mm
        self.bubble_spacing = 8*mm
        self.question_spacing = 12*mm
        
    def generate_gabarito_pdf(self, num_questions, filename=None):
        """
        Gera um gabarito padronizado em PDF
        
        Args:
            num_questions (int): Número de questões (máximo 100)
            filename (str): Nome do arquivo (opcional)
            
        Returns:
            bytes: Conteúdo do PDF gerado
        """
        if num_questions > 100:
            raise ValueError("Número máximo de questões é 100")
        if num_questions < 1:
            raise ValueError("Número mínimo de questões é 1")
            
        # Cria buffer para o PDF
        buffer = io.BytesIO()
        
        # Cria o documento PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        
        # Conteúdo do documento
        story = []
        
        # Título "RESPOSTAS" no canto superior esquerdo
        title_style_left = ParagraphStyle(
            'CustomTitleLeft',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_LEFT,
            textColor=colors.black
        )
        
        story.append(Paragraph("RESPOSTAS", title_style_left))
        story.append(Spacer(1, 10))
        
        # Gera as questões
        questions_data = self._generate_questions_data(num_questions)
        questions_table = self._create_questions_table(questions_data)
        story.append(questions_table)
        
        # Adiciona instruções
        story.append(Spacer(1, 30))
        instructions = self._create_instructions()
        story.append(instructions)
        
        # Constrói o PDF
        doc.build(story, onFirstPage=self._add_corner_markers)
        
        # Retorna o conteúdo
        buffer.seek(0)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Gabarito gerado com {num_questions} questões")
        return pdf_content
    
    def _generate_questions_data(self, num_questions):
        """
        Gera dados das questões para o gabarito
        """
        questions = []
        alternatives = ['A', 'B', 'C', 'D', 'E']
        
        for i in range(1, num_questions + 1):
            question_data = {
                'number': i,
                'alternatives': alternatives
            }
            questions.append(question_data)
            
        return questions
    
    def _create_questions_table(self, questions_data):
        """
        Cria tabela com as questões do gabarito no formato específico com bolinhas
        """
        # Divide as questões em 3 colunas
        questions_per_column = len(questions_data) // 3
        if len(questions_data) % 3 > 0:
            questions_per_column += 1
            
        # Cria dados para 3 colunas
        col1_data = []
        col2_data = []
        col3_data = []
        
        for i, question in enumerate(questions_data):
            question_num = f"{question['number']:02d}"
            row_data = [f"{question_num} -"]
            
            # Adiciona as alternativas A, B, C, D, E com bolinhas
            for alt in question['alternatives']:
                row_data.append(f"({alt})")
            
            # Distribui nas colunas
            if i < questions_per_column:
                col1_data.append(row_data)
            elif i < questions_per_column * 2:
                col2_data.append(row_data)
            else:
                col3_data.append(row_data)
        
        # Preenche colunas vazias para manter alinhamento
        max_rows = max(len(col1_data), len(col2_data), len(col3_data))
        
        while len(col1_data) < max_rows:
            col1_data.append(['', '', '', '', '', ''])
        while len(col2_data) < max_rows:
            col2_data.append(['', '', '', '', '', ''])
        while len(col3_data) < max_rows:
            col3_data.append(['', '', '', '', '', ''])
        
        # Cria tabela com 3 colunas
        table_data = []
        for i in range(max_rows):
            row = col1_data[i] + col2_data[i] + col3_data[i]
            table_data.append(row)
        
        # Larguras das colunas (6 colunas por seção = 18 colunas total)
        col_widths = [1.2*cm] * 6 + [1.2*cm] * 6 + [1.2*cm] * 6
        
        table = Table(table_data, colWidths=col_widths)
        
        # Estilo da tabela
        table_style = TableStyle([
            # Alinhamento
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Fonte
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            
            # Espaçamento
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            
            # Bordas entre colunas principais
            ('LINEBEFORE', (6, 0), (6, -1), 1, colors.black),
            ('LINEBEFORE', (12, 0), (12, -1), 1, colors.black),
        ])
        
        table.setStyle(table_style)
        return table
    
    def _create_instructions(self):
        """
        Cria seção de instruções
        """
        styles = getSampleStyleSheet()
        
        instruction_style = ParagraphStyle(
            'Instructions',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT,
            textColor=colors.black
        )
        
        instructions_text = """
        <b>INSTRUÇÕES PARA PREENCHIMENTO:</b><br/>
        1. Marque apenas uma alternativa por questão<br/>
        2. Use caneta preta ou azul<br/>
        3. Preencha completamente o círculo da alternativa escolhida<br/>
        4. Não marque mais de uma alternativa por questão<br/>
        5. Mantenha o gabarito limpo e sem rasuras<br/>
        <br/>
        <b>DICAS PARA MELHOR LEITURA AUTOMÁTICA:</b><br/>
        • Use círculos bem preenchidos<br/>
        • Evite marcas fora dos círculos<br/>
        • Mantenha o gabarito plano durante a digitalização<br/>
        • Use boa iluminação ao fotografar<br/>
        """
        
        return Paragraph(instructions_text, instruction_style)
    
    def _add_corner_markers(self, canvas, doc):
        """
        Adiciona marcadores de canto pretos para alinhamento
        """
        # Marcador superior direito
        canvas.setFillColor(colors.black)
        canvas.rect(doc.width - 2*cm, doc.height - 2*cm, 0.5*cm, 0.5*cm, fill=1)
        
        # Marcador inferior esquerdo
        canvas.rect(0, 0, 0.5*cm, 0.5*cm, fill=1)

def generate_standard_gabarito(num_questions):
    """
    Função principal para gerar gabarito padronizado
    
    Args:
        num_questions (int): Número de questões (1-100)
        
    Returns:
        bytes: Conteúdo do PDF gerado
    """
    try:
        generator = GabaritoGenerator()
        pdf_content = generator.generate_gabarito_pdf(num_questions)
        
        logger.info(f"Gabarito padronizado gerado com {num_questions} questões")
        return pdf_content
        
    except Exception as e:
        logger.error(f"Erro ao gerar gabarito: {str(e)}")
        raise
