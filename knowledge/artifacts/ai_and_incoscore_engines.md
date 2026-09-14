# AI Classification, Personalization & InCoScore Engines (`BharatAI`)

## 1. Domain Classifier Engine (`backend/app/ai/classifier.py`)

The platform classifies scraped opportunities into 11 academic domain categories:
* `AI/DS` (`ai_ds`)
* `Computer Science` (`cs`)
* `Electronics and Communication` (`ece`)
* `Mechanical Engineering` (`me`)
* `Civil Engineering` (`civil`)
* `Biotechnology` (`biotech`)
* `Law` (`law`)
* `Management` (`management`)
* `Finance` (`finance`)
* `Humanities` (`humanities`)
* `Government and Policy` (`govt_policy`)

### Execution Details:
* **Model**: Zero-shot classification via `facebook/bart-large-mnli` (lazy-loaded singleton pattern).
* **Threshold Gating**:
  * Primary domain allocated if top confidence score $> 0.60$. Otherwise set to `unclassified` for admin review queue (`GET /api/v1/admin/opportunities/unclassified`).
  * Secondary domain allocated if second score $\ge \text{threshold} \times 0.50$ (i.e. $\ge 0.30$).

---

## 2. Personalization & Relevance Scoring (`backend/app/ai/personalization.py`)

The personalized feed calculates a dynamic relevance score for each opportunity per user using a 4-component weighted formula:

$$\text{Relevance Score} = 0.4 \times \text{Interest Match} + 0.3 \times \text{Skill Match} + 0.2 \times \text{Engagement} + 0.1 \times \text{Deadline Urgency}$$

### Component Logic:
1. **Interest Match ($40\%$)**: Cosine similarity between student profile interest vectors and opportunity embedding vectors generated via `sentence-transformers/all-MiniLM-L6-v2`.
2. **Skill Similarity ($30\%$)**: FAISS vector nearest-neighbor search matching extracted resume skills against opportunity requirements.
3. **Engagement ($20\%$)**: Historical user interaction rate (clicks, bookmarking, and applications submitted in similar domain categories).
4. **Deadline Urgency ($10\%$)**: Sigmoid time-decay scoring prioritizing upcoming application deadlines.
5. **Cold-Start Fallback**: New users with zero profile metadata or resume uploads receive top opportunities sorted strictly by deadline urgency.
6. **Caching**: Personalized feeds are cached per-user in Redis (TTL 15 minutes) and automatically invalidated upon profile edits or new opportunity ingestions (`bust_feed_cache`).

---

## 3. Resume Extraction & Skill Parsing (`backend/app/ai/resume_parser.py`)

* **PDF Extraction**: Primary parsing via `pdfplumber` with fallback to `PyMuPDF`. Max upload size 5MB (`application/pdf`).
* **NLP Pipeline**: spaCy Named Entity Recognition (NER) combined with a custom canonical skills dictionary matcher (e.g., standardizing `"ML"`, `"Machine Learning"`, and `"machine-learning"` $\rightarrow$ `"Machine Learning"`).
* **Entity Extraction**: Auto-detects institution/college name, degree program, and graduation year from resume text to pre-populate user profile.

---

## 4. InCoScore Computation Engine (`backend/app/ai/incoscore.py`)

The **InCoScore** is a pure, deterministic scoring system ranking student academic and extra-curricular merit on a scale of **0 to 1,000 points**.

### Point Breakdown Taxonomy:

| Category | Sub-Type / Criteria | Points |
| :--- | :--- | :--- |
| **Hackathons** | 1st Place / Winner<br>2nd Place<br>3rd Place<br>Participant | 100 pts<br>70 pts<br>50 pts<br>10 pts |
| **Research Internships** | Verified research internship (capped at max 3) | 80 pts each (Max 240 pts) |
| **Publications** | Peer-reviewed (IEEE, ACM, Springer, Elsevier)<br>Preprint / Unpublished | 120 pts<br>40 pts |
| **Competitions** | National level<br>State level<br>College level | 90 pts<br>50 pts<br>20 pts |
| **Certifications** | Industry-recognized (AWS, GCP, Azure, ML, PyTorch, Databricks)<br>NPTEL / General | 60 pts<br>30 pts |
| **Coding Ratings** | Platform rating bands (LeetCode, CodeForces) stored in `points_claimed` | 0 – 100 pts |
| **Community Impact** | Platform post contributions | 0.5 pts per post (Capped at 50 pts) |

### Domain Multipliers:
Score component sub-totals are scaled dynamically based on the student's declared primary domain:
* **AI/DS (`ai_ds`)**: Coding $\times 1.2$, Research Internship $\times 1.2$.
* **Computer Science (`cs`)**: Coding $\times 1.1$.
* **Management (`management`)**: Competition $\times 1.2$, Community $\times 1.1$.
* **Finance (`finance`)**: Competition $\times 1.1$.

### Milestone Badges:
* **100 pts**: *Rising Star*
* **300 pts**: *Domain Explorer*
* **500 pts**: *Achiever*
* **750 pts**: *Elite Scholar*
* **1000 pts**: *InCo Legend*
* **Special**: *First Hackathon*, *Published Researcher*.

---

## 5. Anti-Gaming & Verification Safety Controls

1. **Verification Gate**: Only achievements marked `verified=True` by an admin accumulate points toward the user's InCoScore. Unverified entries submit 0 points.
2. **Velocity Limits**: Submission of $>5$ achievements in 24 hours triggers an immediate 429 rate limit and flags the account for manual admin review.
3. **Duplicate Submission Guard**: Rejects identical title + date submissions ($409 \text{ Conflict}$).
4. **Audit Trail**: Every score calculation creates an immutable snapshot record in `incoscore_history`.
