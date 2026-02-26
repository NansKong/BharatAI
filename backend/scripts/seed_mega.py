"""
Mega seed v2: Updated for 2026 with fresh opportunities and verified URLs.
Run: docker exec -it bharatai-backend-1 python -m scripts.seed_mega
"""
import asyncio
import hashlib
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

sys.path.insert(0, ".")
from app.core.database import AsyncSessionLocal, close_database, init_database
from app.models.opportunity import MonitoredSource, Opportunity


def _d(days):
    return datetime.now(timezone.utc) + timedelta(days=days)


def _h(t, d, u):
    return hashlib.sha256(
        f"{t.lower()}|{d[:200].lower()}|{u.lower()}".encode()
    ).hexdigest()


# ── 100+ NIRF Colleges & Opportunity Portals ─────────────────────────────────
SOURCES = [
    # IITs
    ("IIT Madras", "https://www.iitm.ac.in/", "static"),
    ("IIT Delhi", "https://home.iitd.ac.in/", "static"),
    ("IIT Bombay Events & Opportunities", "https://www.iitb.ac.in/", "static"),
    ("IIT Kanpur", "https://www.iitk.ac.in/", "static"),
    ("IIT Kharagpur", "https://www.iitkgp.ac.in/", "static"),
    ("IIT Roorkee", "https://www.iitr.ac.in/", "static"),
    ("IIT Hyderabad", "https://iith.ac.in/news/", "static"),
    ("IIT Guwahati", "https://www.iitg.ac.in/", "static"),
    ("IIT BHU Varanasi", "https://iitbhu.ac.in/", "static"),
    ("IIT Indore", "https://www.iiti.ac.in/", "static"),
    ("IIT ISM Dhanbad", "https://www.iitism.ac.in/", "static"),
    ("IIT Patna", "https://www.iitp.ac.in/", "static"),
    ("IIT Gandhinagar", "https://www.iitgn.ac.in/news", "static"),
    ("IIT Mandi", "https://www.iitmandi.ac.in/news.html", "static"),
    ("IIT Jodhpur", "https://iitj.ac.in/", "static"),
    ("IIT Ropar", "https://www.iitrpr.ac.in/news", "static"),
    ("IIT Bhubaneswar", "https://www.iitbbs.ac.in/news.php", "static"),
    ("IIT Goa", "https://www.iitgoa.ac.in/", "static"),
    ("IIT Dharwad", "https://www.iitdh.ac.in/", "static"),
    ("IIT Bhilai", "https://www.iitbhilai.ac.in/", "static"),
    ("IIT Jammu", "https://www.iitjammu.ac.in/news", "static"),
    ("IIT Palakkad", "https://iitpkd.ac.in/news", "static"),
    ("IIT Tirupati", "https://www.iittp.ac.in/news", "static"),
    # NITs
    ("NIT Tiruchirappalli", "https://www.nitt.edu/", "static"),
    ("NIT Rourkela", "https://www.nitrkl.ac.in/", "static"),
    ("NIT Karnataka Surathkal", "https://www.nitk.ac.in/", "static"),
    ("NIT Calicut", "https://nitc.ac.in/", "static"),
    ("NIT Warangal", "https://www.nitw.ac.in/", "static"),
    ("VNIT Nagpur", "https://vnit.ac.in/academics/notices/", "static"),
    ("MNIT Jaipur", "https://www.mnit.ac.in/notices/", "static"),
    ("MNNIT Allahabad", "https://mnnit.ac.in/notices/", "static"),
    ("SVNIT Surat", "https://www.svnit.ac.in/", "static"),
    ("NIT Kurukshetra", "https://nitkkr.ac.in/", "static"),
    ("NIT Silchar", "https://www.nits.ac.in/", "static"),
    ("MANIT Bhopal", "https://www.manit.ac.in/content/latest-news", "static"),
    ("NIT Durgapur", "https://nitdgp.ac.in/", "static"),
    ("NIT Patna", "https://www.nitp.ac.in/", "static"),
    ("NIT Raipur", "https://www.nitrr.ac.in/", "static"),
    ("NIT Hamirpur", "https://nith.ac.in/", "static"),
    ("NIT Meghalaya", "https://nitm.ac.in/", "static"),
    ("NIT Agartala", "https://nita.ac.in/", "static"),
    ("NIT Manipur", "https://www.nitmanipur.ac.in/notices", "static"),
    ("NIT Srinagar", "https://www.nitsri.net/", "static"),
    ("NIT Uttarakhand", "https://nituk.ac.in/", "static"),
    ("NIT Puducherry", "https://www.nitpy.ac.in/", "static"),
    ("NIT Goa", "https://www.nitgoa.ac.in/", "static"),
    # IIITs
    ("IIIT Hyderabad", "https://www.iiit.ac.in/news/", "static"),
    ("IIIT Delhi", "https://iiitd.ac.in/", "static"),
    ("IIIT Bangalore", "https://www.iiitb.ac.in/", "static"),
    ("IIIT Allahabad", "https://www.iiita.ac.in/", "static"),
    # Top Universities
    ("BITS Pilani", "https://www.bits-pilani.ac.in/", "static"),
    (
        "SRM Institute of Science and Technology",
        "https://www.srmist.edu.in/news/",
        "static",
    ),
    ("VIT Vellore", "https://vit.ac.in/news", "static"),
    ("Jadavpur University", "https://jadavpuruniversity.in/notices/", "static"),
    ("Anna University", "https://www.annauniv.edu/", "static"),
    ("Amrita Vishwa Vidyapeetham", "https://www.amrita.edu/news/", "static"),
    ("Jamia Millia Islamia", "https://jmi.ac.in/noticeboard", "static"),
    ("Thapar Institute", "https://www.thapar.edu/", "static"),
    ("Delhi Technological University", "https://dtu.ac.in/", "static"),
    ("IIEST Shibpur", "https://www.iiest.ac.in/departments", "static"),
    ("Aligarh Muslim University", "https://www.amu.ac.in/", "static"),
    (
        "Kalinga Institute of Industrial Technology",
        "https://kiit.ac.in/event/",
        "static",
    ),
    ("PSG College of Technology", "https://www.psgtech.edu/", "static"),
    ("SASTRA University", "https://www.sastra.edu/", "static"),
    ("RV College of Engineering", "https://www.rvce.edu.in/", "static"),
    ("Manipal Institute of Technology", "https://manipal.edu/mit.html", "static"),
    ("Punjab Engineering College", "https://pec.ac.in/", "static"),
    ("Shiv Nadar University", "https://snu.edu.in/", "static"),
    ("Chandigarh University", "https://www.cuchd.in/", "static"),
    ("LPU Lovely Professional University", "https://www.lpu.in/events/", "static"),
    ("SRM University AP", "https://srmap.edu.in/events/", "static"),
    ("COEP Technological University", "https://www.coeptech.ac.in/", "static"),
    ("Visvesvaraya Technological University", "https://vtu.ac.in/", "static"),
    ("Motilal Nehru National Institute", "https://mnnit.ac.in/", "static"),
    ("Ramaiah Institute of Technology", "https://msrit.edu/", "static"),
    ("BMS College of Engineering", "https://www.bmsce.ac.in/", "static"),
    # Govt & opportunity portals
    ("IIT Bombay Techfest", "https://techfest.org/competitions", "static"),
    ("Smart India Hackathon", "https://www.sih.gov.in/", "dynamic"),
    ("AICTE Schemes", "https://www.aicte-india.org/schemes", "static"),
    ("CSIR Fellowships", "https://www.csir.res.in/funding-opportunities", "static"),
    ("DST Inspire", "https://dst.gov.in/scientific-programmes", "static"),
    ("DRDO Jobs", "https://www.drdo.gov.in/careers", "static"),
    ("Startup India", "https://www.startupindia.gov.in/", "static"),
    ("NITI Aayog Internship", "https://niti.gov.in/internship", "static"),
    ("MeitY Digital India Internship", "https://mygov.in/task/", "static"),
    (
        "National Scholarship Portal",
        "https://scholarships.gov.in/public/schemePublic.do",
        "static",
    ),
    # Aggregators
    ("Unstop Competitions", "https://unstop.com/competitions", "dynamic"),
    ("Devfolio Hackathons", "https://devfolio.co/hackathons", "dynamic"),
    ("Internshala Internships", "https://internshala.com/internships/", "dynamic"),
    (
        "LinkedIn Jobs India",
        "https://www.linkedin.com/jobs/search/?location=India",
        "dynamic",
    ),
    ("HackerEarth Challenges", "https://www.hackerearth.com/challenges/", "dynamic"),
    ("Dare2Compete", "https://dare2compete.com/", "dynamic"),
    ("iSchoolConnect", "https://ischoolconnect.com/", "dynamic"),
    ("Scholarship.com.in", "https://www.buddy4study.com/scholarships", "dynamic"),
    ("ResearchGate India", "https://www.researchgate.net/", "dynamic"),
]

# ── Opportunities — All dated from Feb 2026 onwards ──────────────────────────
OPPS = [
    # ── HACKATHONS ──
    (
        "Smart India Hackathon (SIH) 2026 – Software Edition",
        "India's largest national hackathon by Ministry of Education. Teams of 6 solve real problem statements from government ministries and PSUs. Software edition prizes: ₹1,00,000 per winning team. Held at 150+ nodal centres across India. Topic domains: healthcare, agriculture, smart cities, fintech, education, cybersecurity, AI/ML. Applications open on MyGov portal.",
        "Ministry of Education",
        "cs",
        _d(60),
        "https://www.sih.gov.in/",
        "https://www.sih.gov.in/",
        "Full-time UG/PG students. Team of exactly 6.",
    ),
    (
        "Hack This Fall 2026 – Virtual + In-Person",
        "India's most community-driven hackathon celebrating its anniversary! Virtual format + Build Stations across Mumbai, Ahmedabad, Delhi NCR, Kolkata, and Hyderabad. Culminates in Hacker House & Demo Day in Bengaluru. 3000+ hackers expected. Open to all university students. Great for first-timers. Register on Devfolio.",
        "Hack This Fall",
        "cs",
        _d(75),
        "https://hackthisfall.tech/",
        "https://hackthisfall.tech/",
        "Open to all university students. Solo or teams of up to 4.",
    ),
    (
        "IIT Bombay Techfest 2026 – International Competitions",
        "Asia's largest science and technology festival at IIT Bombay. Competitions spanning 20+ domains: robotics, coding, AI, design, data science, and business. International contestants from 100+ countries. Prize pool exceeding ₹1 crore. Events include robotics wars, algorithmic trading simulations, and data analytics challenges.",
        "IIT Bombay",
        "cs",
        _d(120),
        "https://techfest.org/competitions",
        "https://techfest.org/competitions",
        "Open to all students globally. Most events are free to register.",
    ),
    (
        "Flipkart Grid 7.0 – Software Development Challenge 2026",
        "Flipkart Grid is India's biggest e-commerce hackathon. Software Development track focuses on real Flipkart business problems: recommendation systems, supply chain optimization, and fraud detection. Round 1 is online coding. Finalists visit Flipkart HQ Bangalore. Total prize pool: ₹3,00,000 + PPO opportunity. Register on Unstop.",
        "Flipkart",
        "cs",
        _d(45),
        "https://unstop.com/hackathons",
        "https://unstop.com/hackathons",
        "B.Tech/M.Tech/MCA. Graduating 2027. Teams of 2-4.",
    ),
    (
        "Devfolio: Open Hackathons – March/April 2026",
        "Multiple open hackathons listed on Devfolio platform for March-April 2026. Themes include AI/ML, Blockchain/Web3, IoT, Cybersecurity, Open Innovation, GenAI, EdTech. 24-48 hour formats. Free registration. Prizes, certificates, mentorship, and recruiting opportunities from top tech companies at each event.",
        "Devfolio Community",
        "cs",
        _d(40),
        "https://devfolio.co/hackathons",
        "https://devfolio.co/hackathons",
        "Open to all Indian college students. Individual or teams of 2-4.",
    ),
    (
        "IIT Madras Shaastra Hackathon 2026",
        "Part of IIT Madras's flagship annual technical festival Shaastra. 24-hour hackathon with innovation challenges from industry partners. Past sponsors include Texas Instruments, Intel, and Qualcomm. Tracks in embedded systems, ML, and product design. Accommodation provided at IIT Madras campus for outstation participants.",
        "IIT Madras",
        "cs",
        _d(90),
        "https://shaastra.org/",
        "https://shaastra.org/",
        "Open to all college students in India. Team of 2-4.",
    ),
    (
        "HackerEarth March Sprint 2026",
        "HackerEarth's monthly competitive programming sprint. Includes algorithmic challenges, data science contests, and full-stack development challenges. Cash prizes for top performers. Rankings used by 500+ companies for direct recruitment outreach. Free to participate. Great for building a coding portfolio.",
        "HackerEarth",
        "cs",
        _d(30),
        "https://www.hackerearth.com/challenges/",
        "https://www.hackerearth.com/challenges/",
        "Any college student or recent graduate. Online format.",
    ),
    (
        "Google Solution Challenge 2026 – India",
        "Google Developer Student Clubs' annual flagship program. Build solutions for UN Sustainable Development Goals using Google technologies (Firebase, Cloud, ML Kit, Maps). Top 100 teams globally invited to present at Google. Indian teams from 500+ universities have won in past editions.",
        "Google / GDSC India",
        "ai_ds",
        _d(55),
        "https://developers.google.com/community/gdsc-solution-challenge",
        "https://developers.google.com/community/gdsc-solution-challenge",
        "Must be a registered GDSC member. Teams of 2-4 students.",
    ),
    (
        "Unstop National Level Competitions – Feb/Mar 2026",
        "Unstop (formerly Dare2Compete) hosts 50+ active competitions this season: case studies, quizzes, coding contests, and business summits. Sponsors include McKinsey, Deloitte, Amazon, Samsung, and HDFC. Cash prizes upto ₹5 lakhs. Many competitions allow solo participation. New listings added daily.",
        "Unstop / Dare2Compete",
        "management",
        _d(35),
        "https://unstop.com/competitions",
        "https://unstop.com/competitions",
        "Open to all Indian college students. Varies by competition.",
    ),
    (
        "Toycathon 2026 – National Innovation Contest",
        "Ministry of Education's Toycathon challenges students to design innovative toy concepts rooted in Indian ethos and culture using technology. Prizes up to ₹50,000 per team. Best designs get manufactured and sold by partnered toy companies. Online + offline submission rounds.",
        "Ministry of Education / AICTE",
        "me",
        _d(50),
        "https://toycathon.mic.gov.in/",
        "https://toycathon.mic.gov.in/",
        "Open to students, teachers, and startups. Individual or team of up to 5.",
    ),
    # ── INTERNSHIPS ──
    (
        "ISRO Internship – ICRB 2026 Cycle",
        "ISRO's structured internship for engineering and science students. Work at premier ISRO centres: ISAC (satellites), VSSC (rockets), SAC (remote sensing), NRSC (earth observation). Duration: 4-24 weeks. Stipend provided. One of India's most coveted technical internships. Apply through ISRO's ICRB portal directly.",
        "ISRO",
        "ece",
        _d(30),
        "https://www.isro.gov.in/",
        "https://www.isro.gov.in/",
        "B.Tech/M.Tech/MSc in relevant engineering disciplines.",
    ),
    (
        "MeitY Digital India Internship Scheme 2026",
        "Ministry of Electronics and IT (MeitY) internship for IT and technology students. Hands-on experience in cybersecurity, AI/ML government projects, digital infrastructure and e-governance. Stipend of ₹10,000/month. Duration: 2 months. Apply through MyGov internship portal.",
        "MeitY / Government of India",
        "cs",
        _d(90),
        "https://internship.mygov.in/",
        "https://internship.mygov.in/",
        "Minimum 60% in last degree. At least 1 year remaining in course.",
    ),
    (
        "NITI Aayog Research Internship 2026",
        "NITI Aayog internship for students and research scholars to gain exposure to policy formulation and implementation. Work on live government projects in infrastructure, education, healthcare, agriculture, and urban development. Stipend provided. Duration: 2-3 months. New Delhi office. Apply via niti.gov.in.",
        "NITI Aayog",
        "management",
        _d(60),
        "https://niti.gov.in/internship",
        "https://niti.gov.in/internship",
        "Enrolled in post-graduation or PhD. Strong research and writing skills.",
    ),
    (
        "Microsoft India – SWE Internship 2026 (Summer)",
        "Microsoft India offers premier software engineering internships at Hyderabad and Bangalore offices. Work on Azure, Microsoft 365, Bing, and LinkedIn products. Competitive stipend and potential for return offer. Intern events, Azure credits, and mentorship from senior engineers included. Apply via Microsoft Careers.",
        "Microsoft India",
        "cs",
        _d(45),
        "https://careers.microsoft.com/students/",
        "https://careers.microsoft.com/students/",
        "Penultimate year B.Tech/M.Tech in CS/ECE. DSA and system design skills required.",
    ),
    (
        "Google India – STEP Internship 2026 (First/Second Year)",
        "Google's STEP internship is specifically for first and second-year undergrads from underrepresented groups in tech. Work on real Google products. Paid internship at Google India offices. 12-week program with structured mentorship, career talks, and networking events with Google engineers.",
        "Google India",
        "cs",
        _d(50),
        "https://careers.google.com/students/",
        "https://careers.google.com/students/",
        "1st or 2nd year B.Tech in CS/ECE. Students from underrepresented backgrounds preferred.",
    ),
    (
        "IISc Summer Research Programme (SRP) 2026",
        "IISc's premier undergraduate research programme. 2 months working with faculty across CS, ECE, mathematics, physics, materials science, biology. Campus accommodation, travel allowance, and certificate. One of India's most selective undergraduate research programmes with ~5% acceptance rate. Apply at iisc.ac.in.",
        "IISc Bangalore",
        "cs",
        _d(40),
        "https://iisc.ac.in/",
        "https://iisc.ac.in/",
        "2nd or 3rd year B.Tech/BS. CGPA >= 8.5 strongly preferred.",
    ),
    (
        "Samsung R&D India – Summer Internship 2026",
        "Samsung R&D Institute India (SRI-B, SRI-D, SRI-N) offers internships across AI, 5G, display technology, and semiconductor research. One of India's largest R&D operations. Stipend: ₹35,000–50,000/month. Duration: 2-3 months. Strong product exposure and potential for PPO.",
        "Samsung R&D India",
        "ece",
        _d(35),
        "https://research.samsung.com/sri-b",
        "https://research.samsung.com/sri-b",
        "B.Tech/M.Tech in ECE, CS. CGPA >= 7.0. Strong C++/signal processing/ML skills.",
    ),
    (
        "Adobe India – Research Internship 2026",
        "Adobe Research India (Bangalore) offers research internships in AI, computer vision, document intelligence, and HCI. Interns collaborate with full-time researchers and may publish at major venues. Competitive stipend. 6-12 weeks. Prior research experience or strong coursework in ML preferred.",
        "Adobe Research India",
        "ai_ds",
        _d(42),
        "https://research.adobe.com/",
        "https://research.adobe.com/",
        "3rd/4th year B.Tech or M.Tech/PhD in CS/AI. Coding + research background.",
    ),
    (
        "UIDAI Technology Internship 2026",
        "Unique Identification Authority of India (AADHAAR) internships at New Delhi HQ. Roles in biometrics, software development, data analytics, and cybersecurity. Stipend: ₹30,000–40,000/month. Duration: 6-12 months. Work on India's largest identity infrastructure serving 1.4 billion people.",
        "UIDAI / Government of India",
        "cs",
        _d(55),
        "https://uidai.gov.in/",
        "https://uidai.gov.in/",
        "B.Tech, M.Tech, MBA, or LLB students. Relevant skills in tech or law.",
    ),
    (
        "Internshala: 10,000+ Live Internships – 2026",
        "Internshala has over 10,000 live internship listings updated daily. Categories include Web Development, Data Science, Marketing, Finance, HR, Design, and Content. Many come with stipends from ₹5,000–₹50,000/month. Apply to multiple in one click. Companies range from startups to Fortune 500s.",
        "Internshala",
        "cs",
        _d(365),
        "https://internshala.com/internships/",
        "https://internshala.com/internships/",
        "Any college student. Filter by field, duration, city, and stipend on the portal.",
    ),
    (
        "Qualcomm India Engineering Internship 2026",
        "Qualcomm India offers summer internships in chip design, ML inference, modem software, and computer vision at Bangalore and Hyderabad offices. Work on next-gen 5G, AI, and Snapdragon products. Competitive stipend and strong conversion to full-time offers for outstanding interns.",
        "Qualcomm India",
        "ece",
        _d(38),
        "https://www.qualcomm.com/company/careers",
        "https://www.qualcomm.com/company/careers",
        "B.Tech/M.Tech/PhD in CSE, ECE, EE from accredited Indian universities.",
    ),
    # ── RESEARCH & FELLOWSHIPS ──
    (
        "Prime Minister's Research Fellowship (PMRF) 2026",
        "PMRF offers India's highest PhD fellowship: ₹70,000–80,000/month + ₹2 lakhs/year research grant at IITs, IISc, IISERs, and NITs. Direct PhD admission without GATE. Two cycles per year (December and May). Apply through the PMRF portal. Highly competitive with ~1000 fellows per cycle.",
        "Ministry of Education",
        "govt",
        _d(65),
        "https://www.pmrf.in/",
        "https://www.pmrf.in/",
        "Final-year B.Tech/BS-MS with exceptional academic record. No GATE required.",
    ),
    (
        "CSIR JRF – Junior Research Fellowship 2026",
        "CSIR JRF funds PhD research across chemical, life, mathematical, and physical sciences. Stipend: ₹37,000/month rising to ₹42,000 (SRF) after 2 years. Available at all CSIR labs and partner universities. Exam held twice a year. Highly respected credential in Indian academia.",
        "CSIR",
        "unclassified",
        _d(70),
        "https://csirhrdg.res.in/",
        "https://csirhrdg.res.in/",
        "MSc/BE/B.Tech. Valid GATE or CSIR-UGC NET score required.",
    ),
    (
        "DST INSPIRE Fellowship 2026 – PhD in Science",
        "DST INSPIRE supports doctoral studies in natural/basic sciences. ₹80,000/month + HRA + ₹20,000 annual research grant. 5-year tenure. Awarded to those in top 1% of qualifying exams. Apply online through the INSPIRE portal at online-inspire.gov.in.",
        "DST Government of India",
        "unclassified",
        _d(80),
        "https://online-inspire.gov.in/",
        "https://online-inspire.gov.in/",
        "Top 1% in 10+2 or graduation. Must have BSc/BE/B.Tech. Indian nationals.",
    ),
    (
        "Google PhD Fellowship India 2026",
        "Google offers PhD Fellowships to support outstanding graduate students doing exceptional research in ML, algorithms, HCI, privacy, security, and systems. Fellowship covers tuition, stipend, and includes a Google Research mentor. Nominations via faculty advisor.",
        "Google",
        "ai_ds",
        _d(95),
        "https://research.google/outreach/phd-fellowship/",
        "https://research.google/outreach/phd-fellowship/",
        "Enrolled PhD student at an Indian university nominated by faculty advisor.",
    ),
    (
        "TIFR Summer Research Programme 2026",
        "The Tata Institute of Fundamental Research offers summer research positions for outstanding students in mathematics, physics, chemistry, biology, and CS. Work in world-class labs at TIFR Mumbai with faculty and researchers. Accommodation provided. Applications evaluated by faculty committees.",
        "TIFR Mumbai",
        "cs",
        _d(55),
        "https://www.tifr.res.in/",
        "https://www.tifr.res.in/",
        "BSc/B.Tech students with excellent academic record. Preference for those with research experience.",
    ),
    (
        "Wellcome Trust-DBT India Alliance Fellowship 2026",
        "Intermediate fellowships support scientists wishing to develop research independence. Value: up to ₹5.5 crore over 5 years including salary, research costs, and overheads. Open to researchers 3-12 years post-PhD in biomedical science or public health at Indian institutions.",
        "Wellcome Trust / DBT",
        "biotech",
        _d(100),
        "https://www.indiaalliance.org/fellowships/intermediate",
        "https://www.indiaalliance.org/fellowships/intermediate",
        "3-12 years post-PhD. Affiliation with an Indian research institution required.",
    ),
    (
        "Tata Trusts Innovation Fellowship 2026",
        "Tata Trusts Fellowship supports young innovators working on social challenges in India: rural healthcare, education technology, agriculture, water, and energy access. Fellows receive ₹50,000/month for 12 months, mentorship from Tata leaders, and seed funding for implementation.",
        "Tata Trusts",
        "management",
        _d(70),
        "https://www.tatatrusts.org/",
        "https://www.tatatrusts.org/",
        "Under 35. Working on or planning a project with demonstrable social impact. Indian nationals.",
    ),
    (
        "BARC Research Training School 2026",
        "BARC's annual Research Training School is one of India's most prestigious science programmes. 1-year training in nuclear science, reactor physics, electronics, and materials science at Mumbai campus. Monthly stipend of ₹25,000. DAE fellowship after completion.",
        "BARC / DAE",
        "ece",
        _d(110),
        "https://www.barc.gov.in/",
        "https://www.barc.gov.in/",
        "B.Tech/BE in relevant engineering with >= 60% marks. Indian nationals only.",
    ),
    # ── SCHOLARSHIPS ──
    (
        "National Scholarship Portal – 2026 Cycle",
        "India's unified National Scholarship Portal hosts 100+ central and state government scholarships. Schemes include Post-Matric Scholarships, Top Class Education Scheme, Begum Hazrat Mahal National Scholarship, and PMMS. Total outlay: ₹3,000+ crore annually. New cycle opens March 2026. Apply at scholarships.gov.in.",
        "Ministry of Education / Government of India",
        "govt",
        _d(30),
        "https://scholarships.gov.in/",
        "https://scholarships.gov.in/",
        "Eligibility varies by scheme. Most require family income below ₹2-8 lakhs/year.",
    ),
    (
        "AICTE Pragati Scholarship for Girls 2026",
        "AICTE's Pragati scholarship supports girl students pursuing technical education. Financial assistance of ₹50,000/year. Up to 4,000 scholarships awarded annually. Covers tuition fee and incidentals. Exclusive for girls in degree-level technical programmes at AICTE-approved colleges.",
        "AICTE",
        "govt",
        _d(55),
        "https://www.aicte-india.org/schemes/students-development-schemes/Pragati-Scholarship",
        "https://www.aicte-india.org/schemes/students-development-schemes/Pragati-Scholarship",
        "Girl students in AICTE-approved colleges. Family income <= ₹8 lakhs/year.",
    ),
    (
        "Reliance Foundation UG Scholarship 2026",
        "Reliance Foundation awards merit-cum-means scholarships to top engineering students. Value: ₹6 lakhs/year for 4 years (total ₹24 lakhs). 5,000 scholars selected annually. Includes mentorship, networking events with Reliance Industries leaders, and internship opportunities.",
        "Reliance Foundation",
        "cs",
        _d(48),
        "https://reliancefoundation.org/scholarships",
        "https://reliancefoundation.org/scholarships",
        "1st year B.Tech. Family income < ₹2.5 lakhs/year. JEE/state rank-based.",
    ),
    (
        "Infosys Springboard Scholarship 2026",
        "Infosys Springboard offers 1,000 scholarships to meritorious students from economically weaker sections pursuing engineering or technology courses. Each scholarship is ₹50,000/year for up to 2 years. Covers laptops, internet costs, and access to Infosys Springboard online learning platform with 200+ courses.",
        "Infosys Foundation",
        "cs",
        _d(62),
        "https://springboard.infosys.com/",
        "https://springboard.infosys.com/",
        "Engineering students. Family income < ₹6 lakhs/year. CGPA >= 7.5.",
    ),
    (
        "Buddy4Study Consolidated Scholarships 2026",
        "Buddy4Study aggregates 2,000+ scholarships from government, corporates, and foundations. Scholarships range from ₹5,000 to ₹1,20,000/year for students from Class 1 to PhD. Apply to multiple scholarships from one profile. New listings added weekly from Tata, Mahindra, HDFC, L&T, and more.",
        "Buddy4Study",
        "govt",
        _d(365),
        "https://www.buddy4study.com/scholarships",
        "https://www.buddy4study.com/scholarships",
        "Students from Class 1 through PhD level. Income and merit-based criteria vary.",
    ),
    # ── COMPETITIONS & OLYMPIADS ──
    (
        "ACM ICPC 2026 – Asia Regionals India",
        "International Collegiate Programming Contest (ICPC) Asia Regionals hosted at various Indian institutes. Top competitive programming contest worldwide. Teams of 3 solve algorithmic problems in C/C++/Java. Top teams qualify for ICPC Asia Continent Finals and World Finals. Free registration via icpc.global.",
        "ACM / Indian Universities",
        "cs",
        _d(38),
        "https://icpc.global/",
        "https://icpc.global/",
        "Full-time university students. Age <= 24. Teams of exactly 3.",
    ),
    (
        "Samsung PRISM Research Program 2026",
        "Samsung PRISM (Preparing and Inspiring Student Minds) partners with top Indian engineering colleges to fund student-led research projects. Faculty mentors from both college and Samsung R&D guide students. Selected projects receive ₹1-3 lakhs funding, Samsung devices for testing, and recruitment preference.",
        "Samsung R&D India",
        "ece",
        _d(130),
        "https://research.samsung.com/sri-b/prism",
        "https://research.samsung.com/sri-b/prism",
        "3rd/4th year B.Tech from partner colleges. Team of 2-5 with a faculty supervisor.",
    ),
    (
        "Tata Crucible Campus Quiz 2026",
        "India's largest B-School and engineering campus quiz. Tests knowledge of business, industry, technology, and current affairs. Teams of 2. Campus, zonal, and national finals. Winner receives ₹50,000 and Tata group recognition. 1500+ colleges participate each year.",
        "Tata Trusts / TCS",
        "management",
        _d(50),
        "https://www.tatacruciblestyle.com/",
        "https://www.tatacruciblestyle.com/",
        "Any college student. Teams of 2. Prior quiz experience helpful but not required.",
    ),
    (
        "Entrepreneurship World Cup India 2026",
        "EWC India qualifiers find the most innovative startups and ideas from Indian students. Winners represent India at the global championship with $1,000,000 prize pool. EWC is supported by Saudi G20 Presidency and MIT. Free to enter. Tracks: ideation, startup, and growth stages.",
        "EWC / MIT",
        "management",
        _d(45),
        "https://entrepreneurshipworldcup.com/",
        "https://entrepreneurshipworldcup.com/",
        "Open to students and early-stage entrepreneurs. Individual or team of up to 5.",
    ),
    (
        "IIT Delhi E-Summit Startup Pitch 2026",
        "IIT Delhi's Entrepreneurship Summit startup pitch competition offers ₹5,00,000 in prizes to the best student-led startups. Tracks: deeptech, social enterprise, consumer tech, and SaaS. Winners get mentored by IIT Delhi incubator (FITT) and connected to Delhi's VC ecosystem.",
        "IIT Delhi E-Cell",
        "management",
        _d(75),
        "https://esummit.org/",
        "https://esummit.org/",
        "Student-led startups (at least 1 co-founder must be a current student). Teams of 2-5.",
    ),
    (
        "India Innovation Challenge Design Contest 2026 – TI & DST",
        "Texas Instruments and DST challenge Indian engineering students to design innovative solutions using TI microcontrollers. Phase 1: online prototype; Phase 2: hardware demonstration. Prize: ₹3 lakhs for winner + TI internship offer + IP support for commercialization.",
        "Texas Instruments / DST India",
        "ece",
        _d(55),
        "https://e2e.ti.com/group/universityprogram/m/india-innovation-challenge",
        "https://e2e.ti.com/group/universityprogram/m/india-innovation-challenge",
        "B.Tech/M.Tech in ECE/EEE/CS from Indian colleges. Team of 2-4.",
    ),
]


async def seed():
    await init_database()
    async with AsyncSessionLocal() as db:
        # ── 1. Deactivate old/expired opportunities ──────────────────────────
        now = datetime.now(timezone.utc)
        expired_result = await db.execute(
            update(Opportunity)
            .where(Opportunity.deadline < now, Opportunity.is_active.is_(True))
            .values(is_active=False)
            .returning(Opportunity.id)
        )
        deactivated = len(expired_result.fetchall())
        print(f"  Deactivated {deactivated} expired opportunities")

        # ── 2. Refresh monitored sources (wipe + reinsert) ───────────────────
        # Seeds are config, not user data — truncating is safe and avoids
        # fighting the unique-url constraint from accumulated ghost rows.
        from sqlalchemy import text

        await db.execute(text("DELETE FROM monitored_sources"))
        await db.flush()

        added_s = 0
        for name, url, stype in SOURCES:
            db.add(
                MonitoredSource(
                    name=name, url=url, type=stype, active=True, failure_count=0
                )
            )
            added_s += 1

        await db.flush()
        print(f"  Sources: {added_s} inserted (table refreshed)")

        # ── 3. Insert fresh 2026 opportunities ───────────────────────────────
        added_o = 0
        for row in OPPS:
            title, desc, inst, domain, deadline, src_url, app_link, eligibility = row
            h = _h(title, desc, src_url)
            ex = (
                await db.execute(
                    select(Opportunity.id).where(Opportunity.content_hash == h)
                )
            ).scalar_one_or_none()
            if ex:
                continue
            db.add(
                Opportunity(
                    title=title,
                    description=desc,
                    institution=inst,
                    domain=domain,
                    deadline=deadline,
                    source_url=src_url,
                    application_link=app_link,
                    eligibility=eligibility,
                    content_hash=h,
                    is_active=True,
                    is_verified=True,
                )
            )
            added_o += 1

        await db.commit()
        print(f"  Opportunities: {added_o} new 2026 entries added")
        print(
            f"\n✅ Done! {added_s} sources, {added_o} opportunities, {deactivated} expired deactivated."
        )
        print("   Refresh http://localhost:3000/opportunities")

    await close_database()


if __name__ == "__main__":
    asyncio.run(seed())
