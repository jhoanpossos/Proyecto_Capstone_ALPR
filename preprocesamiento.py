import cv2
import pytesseract
import pandas as pd
import re

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def preprocesar_placa(roi):
    try:
        gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gauss = cv2.GaussianBlur(gris, (5, 5), 0)
        umbral = cv2.adaptiveThreshold(
            gauss, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        return umbral
    except Exception:
        return None

def detectar_texto(img_preprocesada):
    try:
        if img_preprocesada is None: return None, 0
        config = "--psm 8 --oem 3"
        data = pytesseract.image_to_data(img_preprocesada, config=config, output_type=pytesseract.Output.DATAFRAME)
        data = data[data.conf > 0]
        
        if not data.empty:
            texto_detectado = "".join(data['text'].astype(str))
            texto_normalizado = re.sub(r'[^A-Z0-9]', '', texto_detectado.upper())
            confianza_promedio = data['conf'].mean()
            return texto_normalizado, confianza_promedio
        else:
            return None, 0
    except Exception:
        return None, 0