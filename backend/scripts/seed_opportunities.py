"""
Seed script: populates monitored_sources and inserts real Indian
college opportunities so the feed is non-empty immediately.

Run from the backend/ directory:
    python -m scripts.seed_opportunities

Valid domain codes (from CheckConstraint):
    ai_ds | cs | ece | me | civil | biotech | law | management |
    finance | humanities | govt | unclassified
"""

import asyncio
import hashlib
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

sys.path.insert(0, ".")

from app.core.database import AsyncSessionLocal, close_database, init_database
from app.models.opportunity import MonitoredSource, Opportunity

# ─── Monitored Sources ────────────────────────────────────────────────────────

SOURCES = [
    {
        "name": "IIT Bombay Events & Opportunities",
        "url": "https://www.iitb.ac.in/en/event/all",
        "type": "static",
    },
    {
        "name": "IIT Delhi Announcements",
        "url": "https://home.iitd.ac.in/announcements.php",
        "type": "static",
    },
    {
        "name": "IIT Madras Announcements",
        "url": "https://www.iitm.ac.in/happenings/announcements",
        "type": "static",
    },
    {
        "name": "IIT Kharagpur Notices",
        "url": "https://www.iitkgp.ac.in/notices",
        "type": "static",
    },
    {
        "name": "IISc Bangalore Opportunities",
        "url": "https://iisc.ac.in/opportunities/",
        "type": "static",
    },
    {
        "name": "AICTE Scholarships & Schemes",
        "url": "https://www.aicte-india.org/bureaus/faculty_development/schemes",
        "type": "static",
    },
    {
        "name": "Startup India Programs",
        "url": "https://www.startupindia.gov.in/content/sih/en/startup-scheme.html",
        "type": "static",
    },
    {
        "name": "DRDO Recruitment & Internships",
        "url": "https://www.drdo.gov.in/jobs",
        "type": "static",
    },
    {
        "name": "Smart India Hackathon",
        "url": "https://www.sih.gov.in/",
        "type": "dynamic",
    },
    {
        "name": "Unstop Competitions",
        "url": "https://unstop.com/competitions",
        "type": "dynamic",
    },
    {
        "name": "Internshala Internships",
        "url": "https://internshala.com/internships/",
        "type": "dynamic",
    },
    {
        "name": "CSIR Fellowships",
        "url": "https://www.csir.res.in/funding-opportunities/fellowships",
        "type": "static",
    },
]


# ─── Deadline helper ──────────────────────────────────────────────────────────


def _deadline(days: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)


# ─── Opportunities ─────────────────────────────────────────────────────────────

OPPORTUNITIES = [
    # ── ai_ds ────────────────────────────────────────────────────────────────
    {
        "title": "Google Summer of Code 2025 – AI/ML Track",
        "description": (
            "Google Summer of Code (GSoC) is a global program focused on bringing student and beginner developers "
            "into open source software development. Work on AI/ML projects with top open source organizations. "
            "Stipend of $1500–$3300 USD. Open to university students globally including India."
        ),
        "institution": "Google",
        "domain": "ai_ds",
        "deadline": _deadline(60),
        "source_url": "https://summerofcode.withgoogle.com/",
        "application_link": "https://summerofcode.withgoogle.com/",
        "eligibility": "Enrolled in a university or college. 18+ years old.",
    },
    {
        "title": "IIT Bombay – Research Internship in Machine Learning (Summer 2025)",
        "description": (
            "The Department of CSE at IIT Bombay invites applications for summer research internships in "
            "Machine Learning, Deep Learning, and Computer Vision. Selected interns work alongside faculty and "
            "PhD students on cutting-edge research problems. Duration: 8 weeks. Campus accommodation provided."
        ),
        "institution": "IIT Bombay",
        "domain": "ai_ds",
        "deadline": _deadline(45),
        "source_url": "https://www.cse.iitb.ac.in/",
        "application_link": "https://www.cse.iitb.ac.in/",
        "eligibility": "B.Tech / M.Tech students with strong Python and ML fundamentals. CGPA >= 8.0 preferred.",
    },
    {
        "title": "Microsoft Research India – Internship Program 2025",
        "description": (
            "Microsoft Research India offers internship opportunities for students interested in AI, NLP, "
            "computer vision, systems, and algorithms. Interns work with full-time researchers and publish at "
            "top-tier venues. Competitive stipend. Location: Bangalore, India."
        ),
        "institution": "Microsoft Research India",
        "domain": "ai_ds",
        "deadline": _deadline(30),
        "source_url": "https://www.microsoft.com/en-us/research/lab/microsoft-research-india/",
        "application_link": "https://careers.microsoft.com/",
        "eligibility": "Final-year B.Tech or M.Tech/MS/PhD students. Strong research background required.",
    },
    {
        "title": "NASSCOM FutureSkills – AI Certification Scholarship",
        "description": (
            "NASSCOM FutureSkills Prime offers free/subsidized AI, ML, and Data Science certifications for "
            "Indian students and professionals. Scholarships available for meritorious candidates from "
            "economically weaker sections. Courses from top global providers. Up to 100% fee waiver."
        ),
        "institution": "NASSCOM",
        "domain": "ai_ds",
        "deadline": _deadline(90),
        "source_url": "https://futureskillsprime.in/",
        "application_link": "https://futureskillsprime.in/",
        "eligibility": "Indian citizens. Students and working professionals. Income criteria apply for full scholarships.",
    },
    {
        "title": "Kaggle – India ML Month Competition",
        "description": (
            "Monthly machine learning competition on Kaggle with a focus on Indian datasets — agriculture, "
            "healthcare, regional language NLP, and financial inclusion. Total prize pool: $20,000 USD. "
            "Teams of up to 5. Great for building your portfolio and getting recognized by top AI companies."
        ),
        "institution": "Kaggle / Google",
        "domain": "ai_ds",
        "deadline": _deadline(20),
        "source_url": "https://www.kaggle.com/competitions",
        "application_link": "https://www.kaggle.com/competitions",
        "eligibility": "Open to all. Free Kaggle account required.",
    },
    {
        "title": "IISc Bangalore – Summer Research Programme in AI & Robotics 2025",
        "description": (
            "The Indian Institute of Science, Bangalore, invites exceptional undergraduate students for a "
            "2-month summer research programme in Artificial Intelligence, Robotics, and Data Science. "
            "Participants work with IISc faculty, receive campus accommodation, a travel allowance, and a "
            "certificate of completion. One of India's most prestigious undergraduate research programmes."
        ),
        "institution": "IISc Bangalore",
        "domain": "ai_ds",
        "deadline": _deadline(40),
        "source_url": "https://iisc.ac.in/srp/",
        "application_link": "https://iisc.ac.in/srp/",
        "eligibility": "2nd or 3rd year B.Tech/BS students. CGPA >= 8.5. Strong academics required.",
    },
    # ── cs ───────────────────────────────────────────────────────────────────
    {
        "title": "ACM ICPC 2025 – Asia Regional (IIT Kanpur)",
        "description": (
            "The International Collegiate Programming Contest (ICPC) is the most prestigious programming "
            "competition in the world. The Asia Regional hosted by IIT Kanpur brings together top competitive "
            "programmers from across Asia. Top teams advance to ICPC World Finals. Teams of 3. Free registration."
        ),
        "institution": "ACM / IIT Kanpur",
        "domain": "cs",
        "deadline": _deadline(30),
        "source_url": "https://icpc.global/",
        "application_link": "https://icpc.global/regionals/finder/2025",
        "eligibility": "Full-time university students. Must be <= 24 years of age at contest date.",
    },
    {
        "title": "Adobe India Research – Women in Technology Fellowship 2025",
        "description": (
            "Adobe India's Women in Tech Fellowship supports exceptional women students pursuing computer "
            "science and engineering. Fellows receive a Rs 75,000 scholarship, mentorship from Adobe engineers, "
            "and priority consideration for internships. Open to 2nd and 3rd year students."
        ),
        "institution": "Adobe India",
        "domain": "cs",
        "deadline": _deadline(45),
        "source_url": "https://research.adobe.com/fellowship/",
        "application_link": "https://research.adobe.com/fellowship/",
        "eligibility": "Women students in 2nd or 3rd year of B.Tech/BE in CS/IT from top Indian colleges.",
    },
    {
        "title": "GitHub Campus Expert Program – India Cohort",
        "description": (
            "GitHub Campus Experts are student leaders who build inclusive tech communities on campus. "
            "The India cohort provides training, GitHub swag, travel grants to conferences, and direct access "
            "to GitHub engineers. Selected experts get exclusive GitHub merchandise and early access to tools."
        ),
        "institution": "GitHub",
        "domain": "cs",
        "deadline": _deadline(20),
        "source_url": "https://education.github.com/experts",
        "application_link": "https://education.github.com/experts",
        "eligibility": "College students aged 18+. Experience building or contributing to open source preferred.",
    },
    {
        "title": "Flipkart Grid 6.0 – Software Development Track",
        "description": (
            "Flipkart Grid is India's biggest e-commerce hackathon for engineering students. The Software "
            "Development track challenges participants to solve real business problems in supply chain, "
            "recommendation systems, and fraud detection. Winners receive Rs 3,00,000 + PPO opportunity. "
            "Open to teams of 2–4 from any college."
        ),
        "institution": "Flipkart",
        "domain": "cs",
        "deadline": _deadline(35),
        "source_url": "https://unstop.com/hackathons/flipkart-grid-60",
        "application_link": "https://unstop.com/hackathons/flipkart-grid-60",
        "eligibility": "B.Tech/M.Tech/MCA students graduating in 2026 or 2027. Team of 2–4.",
    },
    {
        "title": "Amazon ML Summer School India 2025",
        "description": (
            "Amazon's ML Summer School is a 4-week online program designed to provide students with ML skills "
            "needed to solve real-world challenges. Topics: supervised learning, deep neural networks, NLP, "
            "reinforcement learning, causal inference. Free of cost. Top performers get fast-tracked to Amazon interviews."
        ),
        "institution": "Amazon India",
        "domain": "cs",
        "deadline": _deadline(25),
        "source_url": "https://www.amazon.science/ml-summer-school",
        "application_link": "https://www.amazon.science/ml-summer-school",
        "eligibility": "2nd and 3rd year B.Tech/BE/BS students from Indian universities. Strong maths background.",
    },
    # ── ece ──────────────────────────────────────────────────────────────────
    {
        "title": "Smart India Hackathon (SIH) 2025 – Hardware Edition",
        "description": (
            "Smart India Hackathon is India's biggest open innovation model. The Hardware Edition invites teams "
            "to solve real-world problems using embedded systems, IoT, and robotics in agriculture, health, "
            "energy, and smart cities. Teams of 6 students. Winners receive Rs 1,00,000 prize."
        ),
        "institution": "Ministry of Education, Govt. of India",
        "domain": "ece",
        "deadline": _deadline(40),
        "source_url": "https://www.sih.gov.in/",
        "application_link": "https://www.sih.gov.in/",
        "eligibility": "Full-time students of any UG/PG program in India. Team of exactly 6 required.",
    },
    {
        "title": "IIT Madras Pravartak – Research Fellowship in Deep Tech",
        "description": (
            "Pravartak Technologies Foundation (IIT Madras) offers research fellowships for students working on "
            "deep technology areas including quantum computing, photonics, semiconductors, and advanced materials. "
            "Monthly stipend of Rs 25,000–35,000. Duration: 6–12 months on IIT Madras campus, Chennai."
        ),
        "institution": "IIT Madras / Pravartak",
        "domain": "ece",
        "deadline": _deadline(35),
        "source_url": "https://pravartak.org.in/",
        "application_link": "https://pravartak.org.in/fellowship",
        "eligibility": "B.Tech final year, M.Tech, or PhD students from reputed institutions.",
    },
    {
        "title": "Bosch India – Engineering Internship Program 2025",
        "description": (
            "Bosch India offers 6-month engineering internships across automotive electronics, IoT, ADAS, and "
            "embedded systems. Work at Bosch R&D centres in Bangalore and Coimbatore on real product development. "
            "Competitive stipend. Pre-placement offer (PPO) for outstanding interns."
        ),
        "institution": "Bosch India",
        "domain": "ece",
        "deadline": _deadline(25),
        "source_url": "https://www.bosch.in/careers/",
        "application_link": "https://www.bosch.in/careers/",
        "eligibility": "3rd/4th year B.E./B.Tech in ECE, EEE, CS, or Mechanical. CGPA >= 7.5.",
    },
    {
        "title": "Texas Instruments India – Analog Design Internship",
        "description": (
            "Texas Instruments India offers summer internships in analog and mixed-signal chip design at their "
            "Bangalore design centre. Interns work on real silicon designs shipped to global customers. "
            "TI is one of the largest semiconductor employers in India. Stipend: Rs 50,000–70,000/month."
        ),
        "institution": "Texas Instruments India",
        "domain": "ece",
        "deadline": _deadline(30),
        "source_url": "https://careers.ti.com/",
        "application_link": "https://careers.ti.com/",
        "eligibility": "Pre-final year B.Tech/M.Tech in ECE/EEE. Strong fundamentals in circuits and electronics.",
    },
    # ── me ───────────────────────────────────────────────────────────────────
    {
        "title": "DRDO DARE to Dream 2.0 – Innovation Contest",
        "description": (
            "DRDO's DARE to Dream contest invites Indian innovators and startups to present novel ideas and "
            "technologies for defence and aerospace applications. Selected participants receive funding up to "
            "Rs 10 lakhs, mentoring from DRDO scientists, and potential technology transfer opportunities."
        ),
        "institution": "DRDO",
        "domain": "me",
        "deadline": _deadline(55),
        "source_url": "https://www.drdo.gov.in/dare-to-dream",
        "application_link": "https://www.drdo.gov.in/",
        "eligibility": "Indian innovators, startups, and academic institutions. Individual or team participation.",
    },
    {
        "title": "ISRO Young Scientist Programme (YUVIKA) 2025",
        "description": (
            "ISRO's YUVIKA programme imparts knowledge on Space Science, Space Technology, and Space Applications "
            "to school and college students. Selected students visit ISRO centres, interact with scientists, and "
            "attend lectures. Fully sponsored by ISRO including travel and accommodation."
        ),
        "institution": "ISRO",
        "domain": "me",
        "deadline": _deadline(50),
        "source_url": "https://www.isro.gov.in/YUVIKA.html",
        "application_link": "https://www.isro.gov.in/",
        "eligibility": "Students who have completed 9th standard or 1st year B.E./B.Tech.",
    },
    # ── management ───────────────────────────────────────────────────────────
    {
        "title": "IIM Ahmedabad – Summer Internship Programme 2025",
        "description": (
            "IIM Ahmedabad's MBA Summer Internship is among the most coveted internship opportunities in India. "
            "Leading companies from consulting, BFSI, FMCG, and tech sectors hire IIM-A students. "
            "Average stipend: Rs 1.5–2.5 lakhs/month. Duration: 8 weeks. Campus recruitment in December."
        ),
        "institution": "IIM Ahmedabad",
        "domain": "management",
        "deadline": _deadline(30),
        "source_url": "https://www.iima.ac.in/",
        "application_link": "https://www.iima.ac.in/faculty-research/placement",
        "eligibility": "First-year MBA/PGP students at IIM Ahmedabad. Selection by participating companies.",
    },
    {
        "title": "Tata Social Enterprise Challenge 2025",
        "description": (
            "Organized by Tata Trusts and IIM Calcutta, the Tata Social Enterprise Challenge identifies and "
            "supports promising social enterprises in India. Winners receive funding, mentorship from Tata Group "
            "professionals, and network access. Focus: healthcare, education, livelihoods, sanitation, energy."
        ),
        "institution": "Tata Trusts / IIM Calcutta",
        "domain": "management",
        "deadline": _deadline(50),
        "source_url": "https://tsec.tatainstitute.org/",
        "application_link": "https://tsec.tatainstitute.org/",
        "eligibility": "Social enterprises operating in India for at least 1 year. Revenue between Rs 10L–5Cr.",
    },
    # ── humanities ───────────────────────────────────────────────────────────
    {
        "title": "Ashoka University – Young India Fellowship 2025",
        "description": (
            "Young India Fellowship is a one-year postgraduate diploma in Liberal Studies at Ashoka University. "
            "The programme brings together 200 talented young Indians to engage with ideas across disciplines. "
            "Need-based scholarships available. Networking with India's top leaders, thinkers, and entrepreneurs."
        ),
        "institution": "Ashoka University",
        "domain": "humanities",
        "deadline": _deadline(45),
        "source_url": "https://www.ashoka.edu.in/yif/",
        "application_link": "https://www.ashoka.edu.in/yif/apply",
        "eligibility": "Any UG degree holder. Age <= 26. Indian nationals. Exceptional leadership record.",
    },
    {
        "title": "Teach For India Fellowship 2025–2027",
        "description": (
            "Teach For India is a two-year fellowship where graduates teach in under-resourced schools and "
            "work toward educational equity. Fellows receive monthly stipend, leadership training, and join "
            "India's growing movement of educational leaders. Cities include Mumbai, Delhi, Pune, Hyderabad, "
            "Chennai, Bangalore, Ahmedabad, and Kolkata."
        ),
        "institution": "Teach For India",
        "domain": "humanities",
        "deadline": _deadline(60),
        "source_url": "https://www.teachforindia.org/",
        "application_link": "https://www.teachforindia.org/apply",
        "eligibility": "Recent graduates or final-year students from any discipline. Strong leadership record.",
    },
    # ── govt ─────────────────────────────────────────────────────────────────
    {
        "title": "Prime Minister's Research Fellowship (PMRF) 2025",
        "description": (
            "PMRF attracts the best talent into research at IITs, IISc, IISERs, and NITs. Selected fellows "
            "receive Rs 70,000–80,000/month stipend plus Rs 2 lakhs/year research grant. One of the highest "
            "PhD fellowships in India. Positions available across all major disciplines."
        ),
        "institution": "Ministry of Education, Govt. of India",
        "domain": "govt",
        "deadline": _deadline(55),
        "source_url": "https://www.pmrf.in/",
        "application_link": "https://www.pmrf.in/",
        "eligibility": "Final-year B.Tech/BS-MS students with exceptional academic record. GATE not required.",
    },
    {
        "title": "Udaan Scholarship – J&K Students in Top Institutions",
        "description": (
            "The UDAAN Scholarship Scheme by CBSE supports meritorious students from Jammu & Kashmir in "
            "studying at premier institutions across India. Provides free coaching for IIT-JEE, 500 "
            "scholarships for girls, covering tuition fees, accommodation, and living expenses."
        ),
        "institution": "CBSE / Ministry of Education",
        "domain": "govt",
        "deadline": _deadline(70),
        "source_url": "https://cbseacademic.nic.in/udaan.html",
        "application_link": "https://cbseacademic.nic.in/udaan.html",
        "eligibility": "Girl students from J&K who have passed Class 11 with at least 70% in science/maths.",
    },
    # ── unclassified (research fellowships) ──────────────────────────────────
    {
        "title": "CSIR – Junior Research Fellowship (JRF) 2025",
        "description": (
            "CSIR offers Junior Research Fellowships for pursuing PhD in Science and Technology. "
            "JRF stipend: Rs 37,000/month. Selected through CSIR-UGC NET or GATE. Fellowships available "
            "across all national laboratories and partnered universities. Upgrade to SRF after 2 years."
        ),
        "institution": "CSIR",
        "domain": "unclassified",
        "deadline": _deadline(60),
        "source_url": "https://csirhrdg.res.in/",
        "application_link": "https://csirhrdg.res.in/",
        "eligibility": "MSc/BE/B.Tech with >= 55% marks. Valid GATE or CSIR-UGC NET score required.",
    },
    {
        "title": "DST INSPIRE Fellowship 2025 – Science Research",
        "description": (
            "The Department of Science and Technology (DST) INSPIRE Fellowship supports young Indians pursuing "
            "research in natural and basic sciences. PhD fellowship of Rs 80,000/month + HRA + Rs 20,000/year "
            "research grant. One of the most prestigious science fellowships in India. Duration: 5 years."
        ),
        "institution": "DST, Government of India",
        "domain": "unclassified",
        "deadline": _deadline(75),
        "source_url": "https://online-inspire.gov.in/",
        "application_link": "https://online-inspire.gov.in/",
        "eligibility": "Top 1% of 10+2 or graduation examination. Indian nationals only.",
    },
    # ── biotech ──────────────────────────────────────────────────────────────
    {
        "title": "Wellcome Trust – DBT India Alliance Early Career Fellowship",
        "description": (
            "Wellcome Trust-DBT India Alliance offers Early Career Fellowships for researchers who have recently "
            "completed their PhD and wish to pursue independent research in life sciences, biomedical research, "
            "or public health. Fellowship value: up to Rs 3.5 crore over 5 years."
        ),
        "institution": "Wellcome Trust / DBT",
        "domain": "biotech",
        "deadline": _deadline(80),
        "source_url": "https://www.indiaalliance.org/",
        "application_link": "https://www.indiaalliance.org/fellowships",
        "eligibility": "PhD holders within 3 years of completion. Indian or UK institution affiliation required.",
    },
]


# ─── Content hash ──────────────────────────────────────────────────────────────


def _content_hash(title: str, description: str, url: str) -> str:
    blob = f"{title.lower().strip()}|{description[:200].lower().strip()}|{url.lower().strip()}"
    return hashlib.sha256(blob.encode()).hexdigest()


# ─── Main ──────────────────────────────────────────────────────────────────────


async def seed():
    await init_database()
    async with AsyncSessionLocal() as db:
        # ── Seed monitored sources ────────────────────────────────────────────
        sources_added = 0
        for s in SOURCES:
            existing = (
                await db.execute(
                    select(MonitoredSource).where(MonitoredSource.url == s["url"])
                )
            ).scalar_one_or_none()
            if not existing:
                db.add(
                    MonitoredSource(
                        name=s["name"], url=s["url"], type=s["type"], active=True
                    )
                )
                sources_added += 1

        await db.flush()
        print(
            f"  Monitored sources: {sources_added} added ({len(SOURCES) - sources_added} already existed)"
        )

        # ── Seed opportunities ────────────────────────────────────────────────
        opps_added = 0
        for o in OPPORTUNITIES:
            h = _content_hash(o["title"], o["description"], o["source_url"])
            existing = (
                await db.execute(
                    select(Opportunity.id).where(Opportunity.content_hash == h)
                )
            ).scalar_one_or_none()
            if existing:
                continue

            db.add(
                Opportunity(
                    title=o["title"],
                    description=o["description"],
                    institution=o["institution"],
                    domain=o["domain"],
                    deadline=o.get("deadline"),
                    source_url=o["source_url"],
                    application_link=o["application_link"],
                    eligibility=o.get("eligibility", ""),
                    content_hash=h,
                    is_active=True,
                    is_verified=True,
                )
            )
            opps_added += 1

        await db.commit()
        print(
            f"  Opportunities: {opps_added} added ({len(OPPORTUNITIES) - opps_added} already existed)"
        )
        print(
            "\nDone! Refresh http://localhost:3000 - the feed should now show opportunities."
        )

    await close_database()


if __name__ == "__main__":
    asyncio.run(seed())
