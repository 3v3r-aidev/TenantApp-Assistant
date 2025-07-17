from typing import Tuple, Dict, List
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
from extract_tenant_data import extract_images_from_pdf, call_gpt_vision_api

# === Placeholder for handwritten form GPT call ===
def call_handwritten_prompt(images: List[Image.Image]) -> Dict[str, str]:
    # You can later reuse call_gpt_vision_api() with a slightly tweaked system message
    return call_gpt_vision_api(images)  # Simplified for now

def extract_text_from_first_page(pdf_path: str | Path) -> str:
    try:
        with fitz.open(pdf_path) as doc:
            return doc[0].get_text().strip()
    except:
        return ""

def detect_form_type(text: str, ocr_used: bool = False) -> str:
    if ocr_used:
        return "handwritten_form"
    if "05-15-24" in text or "07-08-22" in text:
        return "standard_form"
    elif "2-1-18" in text or "Declawed?" in text:
        return "handwritten_form"
    return "unknown"

def extract_standard_form(images: List[Image.Image]) -> Dict[str, str]:
    return call_gpt_vision_api(images)

def extract_handwritten_form(images: List[Image.Image]) -> Dict[str, str]:
    return call_handwritten_prompt(images)

def extract_data_by_form_type(pdf_path: str | Path) -> Tuple[Dict[str, str], Dict]:
    images = extract_images_from_pdf(pdf_path)
    text = extract_text_from_first_page(pdf_path)

    form_type = detect_form_type(text, ocr_used=False)

    if form_type == "standard_form":
        return extract_standard_form(images), {}
    elif form_type == "handwritten_form":
        return extract_handwritten_form(images), {}
    else:
        return {}, {}
