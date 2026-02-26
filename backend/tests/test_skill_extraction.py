from app.ai.resume_parser import extract_skills


def test_skill_extraction_accuracy_on_sample_resumes():
    samples = [
        (
            "Worked on ML pipelines with Python and PyTorch.",
            {"Machine Learning", "Python", "PyTorch"},
        ),
        ("Built REST APIs using FastAPI and PostgreSQL.", {"FastAPI", "PostgreSQL"}),
        (
            "Deployed services with Docker and Kubernetes on AWS.",
            {"Docker", "Kubernetes", "AWS"},
        ),
        ("Developed frontend in React and backend in Node.js.", {"React", "Node.js"}),
        ("Created analytics dashboards with Pandas and NumPy.", {"Pandas", "NumPy"}),
        ("Implemented NLP project for text classification.", {"NLP"}),
        ("Worked on VLSI design and embedded systems.", {"VLSI", "Embedded Systems"}),
        (
            "Prepared valuation models and finance reports in Excel.",
            {"Valuation", "Finance", "Excel"},
        ),
        ("Led product management strategy for campus startup.", {"Product Management"}),
        (
            "Contributed to computer vision and deep learning tasks.",
            {"Computer Vision", "Deep Learning"},
        ),
    ]

    matched = 0
    for text, expected in samples:
        found = set(extract_skills(text))
        if found.intersection(expected):
            matched += 1

    assert matched >= 9
