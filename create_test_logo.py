#!/usr/bin/env python3
"""
Cria uma logo de teste para demonstrar o sistema de integração
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_test_logo():
    """Cria uma logo de teste simples"""
    
    # Criar imagem 200x100 com fundo branco
    width, height = 200, 100
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Desenhar borda
    draw.rectangle([2, 2, width-3, height-3], outline='#2E7D32', width=3)
    
    # Desenhar formas geométricas simples
    # Círculo verde
    draw.ellipse([15, 20, 45, 50], fill='#4CAF50', outline='#2E7D32', width=2)
    
    # Retângulo azul
    draw.rectangle([55, 25, 85, 45], fill='#2196F3', outline='#1976D2', width=2)
    
    # Triângulo laranja
    draw.polygon([(95, 45), (110, 20), (125, 45)], fill='#FF9800', outline='#F57C00')
    
    # Texto da empresa
    try:
        # Tentar usar fonte padrão
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    except:
        font_large = None
        font_small = None
    
    # Nome da empresa
    company_text = "CROSS TRANSPORT"
    if font_large:
        draw.text((15, 60), company_text, fill='#2E7D32', font=font_large)
    else:
        draw.text((15, 60), company_text, fill='#2E7D32')
    
    # Slogan
    slogan_text = "LOGÍSTICA PROFISSIONAL"
    if font_small:
        draw.text((15, 75), slogan_text, fill='#666666', font=font_small)
    else:
        draw.text((15, 75), slogan_text, fill='#666666')
    
    # Salvar a logo
    logo_path = "static/uploads/logos/test_logo.png"
    os.makedirs(os.path.dirname(logo_path), exist_ok=True)
    img.save(logo_path, "PNG")
    
    print(f"Logo de teste criada: {logo_path}")
    print(f"Dimensões: {width}x{height}px")
    
    return logo_path

if __name__ == "__main__":
    create_test_logo()