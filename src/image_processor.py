#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de processamento de imagens de gabaritos
Contém as funções principais para análise e extração de respostas
"""

import cv2
import numpy as np
from imutils import contours
import logging
from config import IMAGE_PROCESSING_CONFIG

logger = logging.getLogger(__name__)

def order_points(pts):
    """
    Ordena os pontos em ordem: top-left, top-right, bottom-right, bottom-left
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]; rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]; rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
    """
    Aplica transformação de perspectiva usando 4 pontos
    """
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.linalg.norm(br - bl); widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.linalg.norm(tr - br); heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped

def detect_markers(image):
    """
    Detecta marcadores de alinhamento na imagem
    """
    config = IMAGE_PROCESSING_CONFIG['alignment']
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, config['blur_kernel'], 0)
    thresh_align = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    cnts, _ = cv2.findContours(thresh_align.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    marker_contours = []
    for c in cnts:
        area = cv2.contourArea(c)
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        
        if len(approx) == 4 and area > config['min_marker_area']:
            (x, y, w, h) = cv2.boundingRect(approx)
            aspect_ratio = w / float(h)
            if config['marker_aspect_ratio'][0] <= aspect_ratio <= config['marker_aspect_ratio'][1]:
                marker_contours.append(approx)
    
    if len(marker_contours) < config['min_markers']:
        raise Exception(f"Erro Crítico: Encontrados apenas {len(marker_contours)} marcadores.")
    
    if len(marker_contours) > config['max_markers']:
        marker_contours = sorted(marker_contours, key=cv2.contourArea, reverse=True)[:config['max_markers']]
    
    return marker_contours

def get_marker_points(marker_contours):
    """
    Extrai pontos centrais dos marcadores
    """
    points = []
    for c in marker_contours:
        M = cv2.moments(c)
        if M["m00"] != 0:
            points.append((int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])))
        else:
            (x, y, w, h) = cv2.boundingRect(c)
            points.append((x + w // 2, y + h // 2))
    
    # Se encontrou apenas 3 marcadores, estima o 4º
    if len(points) == 3:
        logger.warning("Encontrados 3 marcadores. Estimando a posição do 4º.")
        P = np.array(points, dtype=np.float32)
        dists = [np.linalg.norm(P[i] - P[(i+1)%3]) + np.linalg.norm(P[i] - P[(i+2)%3]) for i in range(3)]
        p_center_idx = np.argmin(dists)
        p_others_idx = [i for i in range(3) if i != p_center_idx]
        missing_point = P[p_others_idx[0]] - P[p_center_idx] + P[p_others_idx[1]]
        points.append(tuple(missing_point.astype(int)))
    
    return points

def align_image(image):
    """
    Alinha a imagem usando os marcadores detectados
    """
    logger.info("Detectando marcadores de alinhamento")
    marker_contours = detect_markers(image)
    
    logger.info("Extraindo pontos dos marcadores")
    points = get_marker_points(marker_contours)
    
    logger.info("Aplicando transformação de perspectiva")
    screenCnt = np.array(points, dtype="float32")
    paper_aligned = four_point_transform(image, screenCnt)
    
    return paper_aligned

def detect_bubbles(aligned_image, num_questions=None):
    """
    Detecta bolhas de resposta na imagem alinhada
    """
    config = IMAGE_PROCESSING_CONFIG['bubble_detection']
    
    # Determina o número esperado de bolhas
    expected_count = config['expected_count']
    if num_questions:
        expected_count = num_questions * 5
        logger.info(f"Usando número dinâmico de bolhas: {expected_count} ({num_questions} questões * 5)")
    
    # Converte para escala de cinza
    warped_gray = cv2.cvtColor(aligned_image, cv2.COLOR_BGR2GRAY)
    
    # MELHORIA 1: Aplica CLAHE para normalizar iluminação
    # CLAHE = Contrast Limited Adaptive Histogram Equalization
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    warped_gray = clahe.apply(warped_gray)
    logger.info("CLAHE aplicado para normalização de iluminação")
    
    # MELHORIA 2: Aplica GaussianBlur para reduzir ruído
    warped_gray = cv2.GaussianBlur(warped_gray, (5, 5), 0)
    
    # Threshold adaptativo
    thresh = cv2.adaptiveThreshold(
        warped_gray, 
        config['adaptive_threshold']['max_value'],
        getattr(cv2, config['adaptive_threshold']['method']),
        getattr(cv2, config['adaptive_threshold']['threshold_type']),
        config['adaptive_threshold']['block_size'],
        config['adaptive_threshold']['c']
    )
    
    # MELHORIA 3: Morfologia para limpar ruído
    kernel = np.ones((3,3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    logger.info("Operações morfológicas aplicadas")
    
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    question_cnts = []
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        if (w >= config['min_size'] and h >= config['min_size'] and 
            config['aspect_ratio'][0] <= ar <= config['aspect_ratio'][1]):
            question_cnts.append(c)
    
    logger.info(f"Encontradas {len(question_cnts)} bolhas potenciais")
    
    # MELHORIA 4: Reconstrução de Grade (Grid Reconstruction)
    # Tenta recuperar bolhas perdidas baseando-se na distância média
    try:
        question_cnts = reconstruct_missing_bubbles(question_cnts)
        logger.info(f"Após reconstrução de grade: {len(question_cnts)} bolhas")
    except Exception as e:
        logger.error(f"Erro na reconstrução de grade: {e}")
    
    if len(question_cnts) >= expected_count:
        question_cnts = sorted(question_cnts, key=cv2.contourArea, reverse=True)[:expected_count]
        logger.info(f"Ruído removido. Restaram {len(question_cnts)} bolhas.")
    
    if len(question_cnts) != expected_count:
        # Se não encontrou o número exato, mas encontrou algo próximo e múltiplo de 5, tenta prosseguir
        if num_questions and len(question_cnts) > 0 and len(question_cnts) % 5 == 0:
             logger.warning(f"Número de bolhas ({len(question_cnts)}) diferente do esperado ({expected_count}), mas é múltiplo de 5. Tentando processar.")
        else:
             # Última tentativa: se faltam poucas, tenta prosseguir assim mesmo para não travar
             if len(question_cnts) > expected_count * 0.9:
                 logger.warning(f"Faltam algumas bolhas ({len(question_cnts)}/{expected_count}), mas prosseguindo.")
             else:
                 raise Exception(f"Não foi possível isolar as {expected_count} bolhas. Encontradas: {len(question_cnts)}.")
    
    return question_cnts, thresh

def reconstruct_missing_bubbles(cnts):
    """
    Reconstrói bolhas perdidas analisando a grade e distâncias médias
    """
    if not cnts:
        return []
        
    # 1. Agrupa por linhas (Y)
    # Ordena por Y
    boxes = [cv2.boundingRect(c) for c in cnts]
    zipped = sorted(zip(cnts, boxes), key=lambda b: b[1][1])
    cnts_sorted, boxes_sorted = zip(*zipped)
    
    rows = []
    current_row = []
    last_y = -1
    avg_h = np.mean([b[3] for b in boxes])
    
    # Threshold vertical: metade da altura média
    y_threshold = avg_h * 0.5
    
    for c, box in zip(cnts_sorted, boxes_sorted):
        x, y, w, h = box
        if last_y == -1 or abs(y - last_y) < y_threshold:
            current_row.append((c, box))
            # Atualiza Y médio da linha
            last_y = (last_y * len(current_row) + y) / (len(current_row) + 1) if last_y != -1 else y
        else:
            rows.append(current_row)
            current_row = [(c, box)]
            last_y = y
    if current_row:
        rows.append(current_row)
        
    final_cnts = []
    
    # 2. Processa cada linha para achar buracos
    for row in rows:
        # Ordena por X
        row.sort(key=lambda b: b[1][0])
        
        # Se a linha tem poucas bolhas, ignora (pode ser ruído)
        if len(row) < 2:
            final_cnts.extend([c for c, _ in row])
            continue
            
        # Calcula largura média e distância média
        widths = [b[2] for c, b in row]
        avg_width = np.median(widths)
        
        xs = [b[0] for c, b in row]
        gaps = []
        for i in range(len(xs) - 1):
            # Distância entre início de uma e início da próxima
            dist = xs[i+1] - xs[i]
            gaps.append(dist)
            
        if not gaps:
            final_cnts.extend([c for c, _ in row])
            continue
            
        median_step = np.median(gaps)
        
        # Reconstrói a linha preenchendo lacunas
        reconstructed_row = []
        
        for i in range(len(row)):
            curr_c, curr_box = row[i]
            reconstructed_row.append(curr_c)
            
            if i < len(row) - 1:
                curr_x = curr_box[0]
                next_x = row[i+1][1][0]
                
                dist = next_x - curr_x
                
                # Se a distância é aprox 2x o passo (ou mais), falta bolha
                # Tolerância: 1.5x o passo
                if dist > median_step * 1.5:
                    missing_count = int(round(dist / median_step)) - 1
                    
                    if missing_count > 0:
                        # logger.info(f"Detectado(s) {missing_count} bolha(s) faltando na linha Y={curr_box[1]}")
                        for m in range(missing_count):
                            # Cria bolha sintética
                            new_x = int(curr_x + (median_step * (m + 1)))
                            new_y = curr_box[1]
                            new_w = int(avg_width)
                            new_h = curr_box[3]
                            
                            # Cria contorno retangular
                            pt1 = [new_x, new_y]
                            pt2 = [new_x + new_w, new_y]
                            pt3 = [new_x + new_w, new_y + new_h]
                            pt4 = [new_x, new_y + new_h]
                            
                            synthetic_cnt = np.array([[pt1], [pt2], [pt3], [pt4]], dtype=np.int32)
                            reconstructed_row.append(synthetic_cnt)
                            
        final_cnts.extend(reconstructed_row)
        
    return final_cnts

def sort_bubbles_by_columns(bubbles):
    """
    Ordena as bolhas por colunas (esquerda para direita, cima para baixo)
    """
    (question_cnts, _) = contours.sort_contours(bubbles, method="left-to-right")
    
    sorted_cnts = []
    chunk_size = 75
    for i in range(0, len(question_cnts), chunk_size):
        chunk = question_cnts[i:i + chunk_size]
        (coluna_ordenada, _) = contours.sort_contours(chunk, method="top-to-bottom")
        sorted_cnts.extend(coluna_ordenada)
        if i + chunk_size >= 150:
            chunk_size = 50
    
    logger.info("Bolhas ordenadas com sucesso por colunas")
    return sorted_cnts

def extract_answers(sorted_bubbles, thresh_image, aligned_image):
    """
    Extrai as respostas marcadas das bolhas ordenadas
    ABORDAGEM: Comparação RELATIVA com filtros de iluminação (CLAHE + Morfologia)
    """
    config = IMAGE_PROCESSING_CONFIG['scoring']
    alternativas = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"}
    respostas_marcadas = {}
    
    # Prepara a imagem para o resultado visual final
    resultado_visual_img = aligned_image.copy()
    
    logger.info(f"Processando {len(sorted_bubbles)} bolhas em grupos de 5")
    logger.info("Usando comparação RELATIVA com threshold dinâmico")
    
    for (q, i) in enumerate(np.arange(0, len(sorted_bubbles), 5)):
        cnts_por_questao = contours.sort_contours(sorted_bubbles[i:i + 5])[0]
        
        # Conta pixels BRANCOS (marcados) em cada bolha
        pontuacoes = []
        for c in cnts_por_questao:
            mask = np.zeros(thresh_image.shape, dtype="uint8")
            cv2.drawContours(mask, [c], -1, 255, -1)
            mask_filled = cv2.bitwise_and(thresh_image, thresh_image, mask=mask)
            total = cv2.countNonZero(mask_filled)
            pontuacoes.append(total)
        
        # Log das pontuações
        logger.info(f"Questão {q + 1} - Pontuações: {pontuacoes}")
        
        # Ordena pontuações
        sorted_scores = sorted(pontuacoes, reverse=True)
        
        # Calcula estatísticas
        max_score = sorted_scores[0]
        second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0
        mean_score = np.mean(pontuacoes)
        std_score = np.std(pontuacoes)
        
        # ALGORITMO DE DETECÇÃO:
        # 1. A maior pontuação deve ser significativamente maior que a segunda
        # 2. A maior pontuação deve estar acima da média + desvio padrão
        
        # Calcula ratio
        ratio = max_score / second_score if second_score > 0 else float('inf')
        
        # Threshold dinâmico: quanto maior o desvio padrão, mais confiável
        base_threshold = 1.15  # Mais sensível (era 1.4)
        
        # Condições para detectar marcação:
        # 1. Ratio > threshold (destaque em relação à segunda)
        # 2. Pontuação absoluta significativa (> 10% acima da média)
        is_marked = (
            ratio > base_threshold and 
            max_score > (mean_score * 1.1) and
            max_score > 50  # Mínimo absoluto reduzido
        )
        
        if is_marked:
            indice_marcado = pontuacoes.index(max_score)
            resposta = alternativas[indice_marcado]
            logger.info(f"Questão {q + 1} - ✓ DETECTADA: {resposta} | Score: {max_score} vs {second_score} | Ratio: {ratio:.2f} | Média: {mean_score:.1f}")
            
            # Desenha TODAS as bolhas
            for (j, c) in enumerate(cnts_por_questao):
                (x, y, w, h) = cv2.boundingRect(c)
                centro_x = x + w // 2
                centro_y = y + h // 2
                raio = max(w, h) // 2
                
                if j == indice_marcado:
                    # 🟡 AMARELO para bolha MARCADA
                    cv2.circle(resultado_visual_img, (centro_x, centro_y), raio, (0, 255, 255), 3)
                else:
                    # 🟢 VERDE para bolhas NÃO MARCADAS
                    cv2.circle(resultado_visual_img, (centro_x, centro_y), raio, (0, 255, 0), 2)
        else:
            resposta = "NÃO MARCADA"
            logger.info(f"Questão {q + 1} - ✗ NÃO MARCADA | Score: {max_score} vs {second_score} | Ratio: {ratio:.2f} | Média: {mean_score:.1f}")
            
            # Desenha todas em VERDE
            for c in cnts_por_questao:
                (x, y, w, h) = cv2.boundingRect(c)
                centro_x = x + w // 2
                centro_y = y + h // 2
                raio = max(w, h) // 2
                cv2.circle(resultado_visual_img, (centro_x, centro_y), raio, (0, 255, 0), 2)
        
        # SEMPRE registra a resposta
        respostas_marcadas[q + 1] = resposta
    
    logger.info(f"Total de respostas registradas: {len(respostas_marcadas)}")
    logger.info(f"Amostra: {dict(list(respostas_marcadas.items())[:10])}")
    return respostas_marcadas, resultado_visual_img

def process_gabarito_image(image, num_questions=None):
    """
    Processa uma imagem de gabarito completa
    """
    try:
        logger.info(f"Iniciando processamento de gabarito (Questões esperadas: {num_questions if num_questions else 'Padrão'})")
        
        # Alinha a imagem
        aligned_image = align_image(image)
        
        # Detecta bolhas
        bubbles, thresh = detect_bubbles(aligned_image, num_questions)
        
        # Ordena bolhas por colunas
        sorted_bubbles = sort_bubbles_by_columns(bubbles)
        
        # Extrai respostas
        answers, result_image = extract_answers(sorted_bubbles, thresh, aligned_image)
        
        logger.info(f"Processamento concluído: {len(answers)} questões detectadas")
        
        return {
            'success': True,
            'answers': answers,
            'result_image': result_image,
            'total_questions': len(answers)
        }
        
    except Exception as e:
        logger.error(f"Erro no processamento: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
