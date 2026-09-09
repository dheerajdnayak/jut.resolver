# JUT Resolver – Real-Time Question Resolution System

A full‑stack Flask application for managing student question submissions, lecturer voting, and real‑time discussions. Built for the **JnanaSudha Unit Test (JUT)** workflow – students upload questions, lecturers vote on corrections/grace, and admins finalize updates – all with live updates, dark mode, and camera capture.

---

## Features

- **Student Submission** – Upload a question image (or take a photo directly), provide JUT number, subject (Physics/Chemistry/Maths), and optional text.
- **Public Feed** – All active questions are displayed on the homepage with real‑time public comments (no login required).
- **Lecturer Portal** – Sign up, log in, and see only questions from your subject. Vote using **5 options**: `GRACE`, `1)`, `2)`, `3)`, `4)`, plus a **NUMERICAL** option for fill‑in‑the‑blank (FIB) questions.
- **Real‑Time Features** – Public comments and lecturer discussions update instantly via WebSockets – no page refresh needed.
- **Admin Dashboard** – View aggregated vote counts, see numerical values submitted by lecturers, mark questions as *updated*, and permanently delete resolved posts.
- **Dark Mode** – Toggle between light and dark themes; preference is saved in browser storage.
- **Mobile‑Ready** – Built with Bootstrap 5, responsive design, and camera capture using `getUserMedia`.

---

## Tech Stack

| Layer        | Technology                                     |
|--------------|------------------------------------------------|
| Backend      | Python 3, Flask, Flask‑SQLAlchemy, Flask‑Login |
| Real‑time    | Flask‑SocketIO, Eventlet                       |
| Database     | SQLite (production-ready with PostgreSQL/MySQL)|
| Frontend     | Bootstrap 5, Font Awesome, vanilla JavaScript |
| Authentication| Bcrypt (password hashing)                      |

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Git (optional)

### Clone & Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/jut-resolver.git
cd jut-resolver

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt