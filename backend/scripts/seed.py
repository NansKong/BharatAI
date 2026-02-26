"""
Database seed script for development.
Run: docker compose exec backend python scripts/seed.py
"""
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.security import hash_password
from app.models.incoscore import IncoScoreHistory
from app.models.opportunity import MonitoredSource, Opportunity
from app.models.user import Profile, User
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


def build_student_template(idx: int) -> dict:
    templates = [
        {
            "name": "Arjun Sharma",
            "college": "IIT Bombay",
            "degree": "B.Tech CSE",
            "skills": ["Python", "Machine Learning", "FastAPI"],
        },
        {
            "name": "Priya Patel",
            "college": "NIT Trichy",
            "degree": "B.Tech ECE",
            "skills": ["VLSI", "Embedded Systems", "C++"],
        },
        {
            "name": "Rahul Verma",
            "college": "IISc Bangalore",
            "degree": "M.Tech AI",
            "skills": ["Deep Learning", "Computer Vision", "PyTorch"],
        },
        {
            "name": "Ananya Singh",
            "college": "IIM Ahmedabad",
            "degree": "MBA",
            "skills": ["Finance", "Strategy", "Excel"],
        },
        {
            "name": "Karthik Nair",
            "college": "IIIT Hyderabad",
            "degree": "B.Tech CS",
            "skills": ["Web Dev", "React", "Node.js"],
        },
    ]
    t = templates[idx % len(templates)]
    return {
        "name": f"{t['name']} {idx + 1}",
        "email": f"student{idx + 1}@example.com",
        "college": t["college"],
        "degree": t["degree"],
        "year": (idx % 4) + 1,
        "skills": t["skills"],
    }


async def seed() -> None:
    async with SessionLocal() as db:
        print("Starting database seed...")

        # Admin users (5)
        admins_data = [
            {
                "name": "BharatAI Admin 1",
                "email": "admin1@bharatai.in",
                "college": "IIT Bombay",
            },
            {
                "name": "BharatAI Admin 2",
                "email": "admin2@bharatai.in",
                "college": "IIT Delhi",
            },
            {
                "name": "BharatAI Admin 3",
                "email": "admin3@bharatai.in",
                "college": "IISc Bangalore",
            },
            {
                "name": "BharatAI Admin 4",
                "email": "admin4@bharatai.in",
                "college": "NIT Trichy",
            },
            {
                "name": "BharatAI Admin 5",
                "email": "admin5@bharatai.in",
                "college": "IIIT Hyderabad",
            },
        ]
        for admin_data in admins_data:
            admin = User(
                id=uuid.uuid4(),
                name=admin_data["name"],
                email=admin_data["email"],
                hashed_password=hash_password("Admin@123"),
                role="admin",
                college=admin_data["college"],
                is_active=True,
            )
            db.add(admin)
            db.add(Profile(user_id=admin.id))
            print(f"  Admin: {admin.email} / Admin@123")

        # Student users (20)
        seeded_students: list[User] = []
        for idx in range(20):
            student_data = build_student_template(idx)
            student = User(
                id=uuid.uuid4(),
                name=student_data["name"],
                email=student_data["email"],
                hashed_password=hash_password("Student@123"),
                role="student",
                college=student_data["college"],
                degree=student_data["degree"],
                year=student_data["year"],
                is_active=True,
            )
            db.add(student)
            db.add(
                Profile(
                    user_id=student.id,
                    skills=student_data["skills"],
                    interests=["AI", "Research"],
                )
            )
            seeded_students.append(student)
            print(f"  Student: {student.email} / Student@123")

        # Monitored sources (8)
        sources = [
            {
                "name": "IIT Bombay Events",
                "url": "https://www.iitb.ac.in/new/content/events",
                "type": "static",
            },
            {
                "name": "IIT Delhi Opportunities",
                "url": "https://home.iitd.ac.in/opportunities",
                "type": "static",
            },
            {
                "name": "IISc Announcements",
                "url": "https://www.iisc.ac.in/announcements/",
                "type": "static",
            },
            {
                "name": "AICTE Scholarships",
                "url": "https://www.aicte-india.org/schemes",
                "type": "static",
            },
            {
                "name": "Startup India Programs",
                "url": "https://startupindia.gov.in/content/sih/en/initiatives.html",
                "type": "static",
            },
            {
                "name": "DRDO Careers",
                "url": "https://www.drdo.gov.in/careers",
                "type": "static",
            },
            {
                "name": "Smart India Hackathon",
                "url": "https://www.sih.gov.in/",
                "type": "dynamic",
            },
            {
                "name": "Unstop Competitions",
                "url": "https://unstop.com/hackathons",
                "type": "dynamic",
            },
        ]
        for source in sources:
            ms = MonitoredSource(
                **source, id=uuid.uuid4(), interval_minutes=30, active=True
            )
            db.add(ms)
            print(f"  Source: {ms.name}")

        # Opportunities (10)
        now = datetime.now(timezone.utc)
        opportunities_data = [
            {
                "title": "Smart India Hackathon 2025",
                "description": "India's biggest hackathon. Build solutions for national problems.",
                "institution": "AICTE",
                "domain": "cs",
                "deadline": now + timedelta(days=30),
            },
            {
                "title": "DRDO Research Internship",
                "description": "6-month research internship in defence technologies.",
                "institution": "DRDO",
                "domain": "ece",
                "deadline": now + timedelta(days=15),
            },
            {
                "title": "PM Research Fellowship 2025",
                "description": "Fellowship for PhD students pursuing research in science and technology.",
                "institution": "Ministry of Education",
                "domain": "ai_ds",
                "deadline": now + timedelta(days=45),
            },
            {
                "title": "IISc Summer Research Programme",
                "description": "8-week summer research internship at IISc Bangalore.",
                "institution": "IISc",
                "domain": "cs",
                "deadline": now + timedelta(days=20),
            },
            {
                "title": "ISRO Young Scientist Programme",
                "description": "YUVIKA programme for school and college students in space science.",
                "institution": "ISRO",
                "domain": "ece",
                "deadline": now + timedelta(days=60),
            },
            {
                "title": "NASSCOM AI Scholarship",
                "description": "Scholarship for students pursuing AI and ML courses.",
                "institution": "NASSCOM",
                "domain": "ai_ds",
                "deadline": now + timedelta(days=10),
            },
            {
                "title": "IIM Ahmedabad Social Innovation Grant",
                "description": "Funding for MBA students working on social impact projects.",
                "institution": "IIM Ahmedabad",
                "domain": "management",
                "deadline": now + timedelta(days=25),
            },
            {
                "title": "Law Ministry Research Fellowship",
                "description": "Research fellowship for law students on constitutional law.",
                "institution": "Ministry of Law",
                "domain": "law",
                "deadline": now + timedelta(days=35),
            },
            {
                "title": "DBT BioCare Scholarship",
                "description": "For biotechnology students from disadvantaged backgrounds.",
                "institution": "DBT India",
                "domain": "biotech",
                "deadline": now + timedelta(days=50),
            },
            {
                "title": "Google India Developer Scholarship",
                "description": "Scholarship plus mentorship for developers in India.",
                "institution": "Google",
                "domain": "cs",
                "deadline": now + timedelta(days=18),
            },
        ]

        for idx, opportunity_data in enumerate(opportunities_data):
            opportunity = Opportunity(
                **opportunity_data,
                id=uuid.uuid4(),
                source_url=f"https://example.com/opp/{idx}",
                content_hash=f"seed_hash_{idx}_{uuid.uuid4().hex[:8]}",
                is_active=True,
                classification_confidence=0.92,
            )
            db.add(opportunity)
            print(f"  Opportunity: {opportunity.title[:50]}")

        # InCoScore history entries (20)
        domains = ["ai_ds", "cs", "ece", "management", "law", "biotech"]
        for idx, student in enumerate(seeded_students):
            total_score = float(120 + ((idx + 1) * 31) % 780)
            components = {
                "hackathon": int(total_score * 0.25),
                "research": int(total_score * 0.30),
                "certifications": int(total_score * 0.20),
                "community": int(total_score * 0.10),
                "coding": int(total_score * 0.15),
            }
            db.add(
                IncoScoreHistory(
                    id=uuid.uuid4(),
                    user_id=student.id,
                    total_score=total_score,
                    domain=domains[idx % len(domains)],
                    components_json=json.dumps(components),
                )
            )

        await db.commit()
        print("Seed complete")
        print("  Admin login: admin1@bharatai.in / Admin@123")
        print("  Student login: student1@example.com / Student@123")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
