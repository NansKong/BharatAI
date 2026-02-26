import fitz
from app.ai.resume_parser import extract_text_from_pdf_bytes, parse_resume


def _build_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_pdf_text_extraction_from_sample_pdf():
    pdf_bytes = _build_pdf_bytes("IIT Bombay B.Tech 2027 Python ML")

    extracted = extract_text_from_pdf_bytes(pdf_bytes)

    assert "IIT Bombay" in extracted
    assert "Python" in extracted


def test_parse_resume_extracts_skills_and_entities():
    pdf_bytes = _build_pdf_bytes(
        "B.Tech student at IIT Delhi graduating 2028. Skills: Python, ML, Deep Learning."
    )

    parsed = parse_resume(pdf_bytes)

    assert parsed["college"] is not None
    assert parsed["degree"] is not None
    assert parsed["graduation_year"] == 2028
    skills = parsed["skills"]
    assert "Python" in skills
    assert "Machine Learning" in skills
