# ====================================================================================
# SCRIPT DE EXTRAÇÃO DE RESPOSTAS DE GABARITOS
# Versão FINAL E DEFINITIVA - Com Relatórios Visuais de Depuração
# ====================================================================================

# --- 0. IMPORTAÇÃO DAS BIBLIOTECAS ---
import cv2
import numpy as np
from imutils import contours

# ====================================================================================
# 1. FUNÇÕES AUXILIARES (sem alterações)
# ====================================================================================
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]; rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]; rect[3] = pts[np.argmax(diff)]
    return rect

def four_point_transform(image, pts):
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

# ====================================================================================
# 2. SCRIPT PRINCIPAL
# ====================================================================================

# --- ETAPA 1: ALINHAMENTO DA IMAGEM ---
try:
    print("--- ETAPA 1: ALINHANDO A IMAGEM ---")
    img = cv2.imread("../../assets/images/prova.jpg")
    if img is None: raise FileNotFoundError("Arquivo 'prova.jpg' não encontrado.")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh_align = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    cnts, _ = cv2.findContours(thresh_align.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    marker_contours = []
    for c in cnts:
        area = cv2.contourArea(c); peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        if len(approx) == 4 and area > 100:
            (x, y, w, h) = cv2.boundingRect(approx)
            aspect_ratio = w / float(h)
            if 0.8 <= aspect_ratio <= 1.2: marker_contours.append(approx)
    if len(marker_contours) < 3: raise Exception(f"Erro Crítico: Encontrados apenas {len(marker_contours)} marcadores.")
    if len(marker_contours) > 4: marker_contours = sorted(marker_contours, key=cv2.contourArea, reverse=True)[:4]
    points = []
    for c in marker_contours:
        M = cv2.moments(c)
        if M["m00"] != 0: points.append((int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])))
        else: (x, y, w, h) = cv2.boundingRect(c); points.append((x + w // 2, y + h // 2))
    if len(points) == 3:
        print("Aviso: Encontrados 3 marcadores. Estimando a posição do 4º.")
        P = np.array(points, dtype=np.float32)
        dists = [np.linalg.norm(P[i] - P[(i+1)%3]) + np.linalg.norm(P[i] - P[(i+2)%3]) for i in range(3)]
        p_center_idx = np.argmin(dists)
        p_others_idx = [i for i in range(3) if i != p_center_idx]
        missing_point = P[p_others_idx[0]] - P[p_center_idx] + P[p_others_idx[1]]
        points.append(tuple(missing_point.astype(int)))
    screenCnt = np.array(points, dtype="float32")
    paper_aligned = four_point_transform(img, screenCnt)
    warped_gray = cv2.cvtColor(paper_aligned, cv2.COLOR_BGR2GRAY)
    cv2.imwrite("prova_alinhada.jpg", paper_aligned)
    print("✅ Alinhamento concluído com sucesso.")

except Exception as e:
    print(f"ERRO NA ETAPA DE ALINHAMENTO: {e}"); exit()

# --- ETAPA 2: EXTRAÇÃO DAS RESPOSTAS POR ORDENAÇÃO GEOMÉTRICA ---
try:
    print("\n--- ETAPA 2: EXTRAINDO RESPOSTAS POR ORDENAÇÃO GEOMÉTRICA ---")
    
    thresh = cv2.adaptiveThreshold(warped_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 5)
    cv2.imwrite("prova_alinhada_thresh.jpg", thresh)
    
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    question_cnts = []
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ar = w / float(h)
        if w >= 18 and h >= 18 and 0.8 <= ar <= 1.2:
            question_cnts.append(c)

    print(f"Encontradas {len(question_cnts)} bolhas potenciais na página inteira.")
    if len(question_cnts) >= 200:
        question_cnts = sorted(question_cnts, key=cv2.contourArea, reverse=True)[:200]
        print(f"INFO: Ruído removido. Restaram {len(question_cnts)} bolhas.")

    if len(question_cnts) != 200:
        raise Exception(f"Não foi possível isolar as 200 bolhas. Encontradas: {len(question_cnts)}.")

    # >>>>> NOVA IMAGEM DE DEBUG 1: MOSTRAR TODAS AS BOLHAS ENCONTRADAS <<<<<
    debug_bolhas_img = paper_aligned.copy()
    cv2.drawContours(debug_bolhas_img, question_cnts, -1, (255, 0, 0), 2) # Desenha em azul
    cv2.imwrite("prova_debug_bolhas_detectadas.jpg", debug_bolhas_img)
    print("INFO: Imagem de debug com todas as 200 bolhas detectadas foi salva.")
    # >>>>> FIM DO DEBUG 1 <<<<<

    (question_cnts, _) = contours.sort_contours(question_cnts, method="left-to-right")

    sorted_cnts = []
    chunk_size = 75
    # Este loop inteligente separa as 3 colunas, mesmo que a última seja menor
    for i in range(0, len(question_cnts), chunk_size):
        chunk = question_cnts[i:i + chunk_size]
        (coluna_ordenada, _) = contours.sort_contours(chunk, method="top-to-bottom")
        sorted_cnts.extend(coluna_ordenada)
        if i + chunk_size >= 150: # Depois da segunda coluna, o tamanho do chunk muda
            chunk_size = 50 
    
    print("INFO: Bolhas ordenadas com sucesso por colunas.")

    alternativas = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E"}
    respostas_marcadas = {}
    
    # Prepara a imagem para o resultado visual final
    resultado_visual_img = paper_aligned.copy()

    for (q, i) in enumerate(np.arange(0, len(sorted_cnts), 5)):
        cnts_por_questao = contours.sort_contours(sorted_cnts[i:i + 5])[0]
        
        pontuacoes = []
        for (j, c) in enumerate(cnts_por_questao):
            mask = np.zeros(thresh.shape, dtype="uint8")
            cv2.drawContours(mask, [c], -1, 255, -1)
            mask = cv2.bitwise_and(thresh, thresh, mask=mask)
            total = cv2.countNonZero(mask)
            pontuacoes.append(total)
        
        sorted_scores = sorted(pontuacoes, reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0] > (sorted_scores[1] * 1.5):
            indice_marcado = pontuacoes.index(sorted_scores[0])
            respostas_marcadas[q + 1] = alternativas[indice_marcado]

            # >>>>> NOVA IMAGEM DE DEBUG 2: DESENHA O CÍRCULO NA RESPOSTA ESCOLHIDA <<<<<
            # Calcula o centro e o raio da bolha marcada para desenhar um círculo
            (x, y, w, h) = cv2.boundingRect(cnts_por_questao[indice_marcado])
            centro_x = x + w // 2
            centro_y = y + h // 2
            raio = w // 2
            # Desenha um círculo ciano (azul claro) com espessura 2
            cv2.circle(resultado_visual_img, (centro_x, centro_y), raio, (255, 255, 0), 2)
            # >>>>> FIM DO DEBUG 2 <<<<<

        else:
            respostas_marcadas[q + 1] = "DUVIDA / NULA"
        
except Exception as e:
    print(f"ERRO NA ETAPA DE EXTRAÇÃO: {e}"); exit()

# Salva a imagem com os resultados visuais
cv2.imwrite("prova_resultado_visual.jpg", resultado_visual_img)
print("INFO: Imagem de resultado visual salva como 'prova_resultado_visual.jpg'.")

# --- ETAPA 3: EXIBIÇÃO DO RESULTADO ---
print("\n--- ETAPA 3: RESPOSTAS ENCONTRADAS ---")
for i in range(1, 41):
    resposta = respostas_marcadas.get(i, "NAO ENCONTRADA")
    print(f"Questão {i:02d}: {resposta}")

print("\n\n✅ Extração finalizada com sucesso! O projeto está concluído.")