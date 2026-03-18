"""
SQLite database initialization, schema, seed data, and CRUD operations.
"""
import sqlite3
import hashlib
import os
from config import DATABASE_PATH, DATA_DIR, DAYS, START_HOUR, END_HOUR


def get_connection():
    """Get a database connection with row_factory enabled."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    """Simple SHA-256 password hashing."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def check_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


# ─── Schema ───────────────────────────────────────────────────────────────────

def init_db():
    """Create all tables if they don't exist, then seed initial data."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS instructors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            short_name TEXT,
            status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive'))
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            units INTEGER NOT NULL DEFAULT 3,
            subject_type TEXT DEFAULT 'Lecture' CHECK(subject_type IN ('Lecture', 'Laboratory', 'PE'))
        );

        CREATE TABLE IF NOT EXISTS instructor_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instructor_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            FOREIGN KEY (instructor_id) REFERENCES instructors(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            UNIQUE(instructor_id, subject_id)
        );

        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            year_level INTEGER NOT NULL,
            UNIQUE(name, year_level)
        );

        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            section TEXT NOT NULL,
            FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
            UNIQUE(program_id, section)
        );

        CREATE TABLE IF NOT EXISTS block_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            FOREIGN KEY (block_id) REFERENCES blocks(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            UNIQUE(block_id, subject_id)
        );

        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            building TEXT NOT NULL,
            room_type TEXT DEFAULT 'Classroom' CHECK(room_type IN ('Classroom', 'Laboratory', 'AVR'))
        );

        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT NOT NULL,
            start_hour INTEGER NOT NULL,
            end_hour INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'Generated' CHECK(status IN ('Generated', 'Active', 'Archived'))
        );

        CREATE TABLE IF NOT EXISTS schedule_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER NOT NULL,
            block_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            instructor_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            time_slot_id INTEGER NOT NULL,
            FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
            FOREIGN KEY (block_id) REFERENCES blocks(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (instructor_id) REFERENCES instructors(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id),
            FOREIGN KEY (time_slot_id) REFERENCES time_slots(id)
        );
    """)

    conn.commit()

    # Check if data already seeded
    count = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        seed_data(conn)

    conn.close()


def seed_data(conn):
    """Insert initial seed data."""
    cursor = conn.cursor()

    # ── Default admin user ──
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)",
        ("admin", "admin@sltcfpdi.edu.ph", hash_password("admin123"), "System Administrator")
    )

    # ── Subjects ──
    subjects = [
        ("GE1", "General Education 1", 3, "Lecture"),
        ("GE2", "General Education 2", 3, "Lecture"),
        ("GE3", "General Education 3", 3, "Lecture"),
        ("GE4", "General Education 4", 3, "Lecture"),
        ("PE1", "Physical Education 1", 2, "PE"),
        ("PE2", "Physical Education 2", 2, "PE"),
        ("TECHVOC101", "Tech-Voc 101", 3, "Laboratory"),
        ("TECHVOC104", "Tech-Voc 104", 3, "Laboratory"),
        ("EIM1", "Electrical Installation & Maintenance 1", 3, "Laboratory"),
        ("CSS", "Computer Systems Servicing", 3, "Laboratory"),
        ("EDUC4", "Education 4", 3, "Lecture"),
        ("EDUC33", "Education 33", 3, "Lecture"),
        ("EDUC34", "Education 34", 3, "Lecture"),
        ("Arts101", "Arts 101", 3, "Lecture"),
        ("Psych1", "Psychology 1", 3, "Lecture"),
        ("Psych2", "Psychology 2", 3, "Lecture"),
    ]
    cursor.executemany(
        "INSERT INTO subjects (code, name, units, subject_type) VALUES (?, ?, ?, ?)",
        subjects
    )

    # ── Instructors with subject assignments ──
    instructors_data = [
        ("Mr. J. Dela Cruz", "Dela Cruz", ["GE1", "GE2", "PE1", "PE2"]),
        ("Mr. E. Legaspi", "Legaspi", ["TECHVOC101", "EIM1", "GE4"]),
        ("Ms. L. Neri", "Neri", ["EDUC4", "EDUC33", "EDUC34", "GE4"]),
        ("Mrs. N. Soriano", "Soriano", ["Arts101", "Psych1", "Psych2"]),
        ("Mr. A. Llamido", "Llamido", ["TECHVOC104", "CSS", "GE3"]),
    ]
    for full_name, short_name, subj_codes in instructors_data:
        cursor.execute(
            "INSERT INTO instructors (full_name, short_name) VALUES (?, ?)",
            (full_name, short_name)
        )
        instr_id = cursor.lastrowid
        for code in subj_codes:
            sub_id = cursor.execute(
                "SELECT id FROM subjects WHERE code = ?", (code,)
            ).fetchone()[0]
            cursor.execute(
                "INSERT INTO instructor_subjects (instructor_id, subject_id) VALUES (?, ?)",
                (instr_id, sub_id)
            )

    # ── Programs & Blocks ──
    programs_blocks = [
        ("BEED", 1, ["A", "B", "C"]),
        ("BEED", 2, ["A", "B", "C"]),
        ("BTVTED", 1, ["A", "B"]),
        ("BTVTED", 2, ["A"]),
    ]
    for prog_name, year, sections in programs_blocks:
        cursor.execute(
            "INSERT INTO programs (name, year_level) VALUES (?, ?)",
            (prog_name, year)
        )
        prog_id = cursor.lastrowid
        for sec in sections:
            cursor.execute(
                "INSERT INTO blocks (program_id, section) VALUES (?, ?)",
                (prog_id, sec)
            )

    # ── Rooms ──
    rooms = [
        ("Room 1", "Building A", "Classroom"),
        ("Room 2", "Building A", "Classroom"),
        ("Room 3", "Building A", "Classroom"),
        ("Room 1", "Building B", "Classroom"),
        ("Lab 1", "Building B", "Laboratory"),
        ("Lab 2", "Building B", "Laboratory"),
        ("AVR", "Building C", "AVR"),
    ]
    cursor.executemany(
        "INSERT INTO rooms (name, building, room_type) VALUES (?, ?, ?)",
        rooms
    )

    # ── Time Slots (Mon-Sat, 8AM-5PM, 1-hour slots) ──
    for day in DAYS:
        for hour in range(START_HOUR, END_HOUR):
            cursor.execute(
                "INSERT INTO time_slots (day, start_hour, end_hour) VALUES (?, ?, ?)",
                (day, hour, hour + 1)
            )

    conn.commit()


# ─── CRUD: Users ──────────────────────────────────────────────────────────────

def authenticate_user(username: str, password: str):
    """Returns user row if credentials are valid, else None."""
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if user and check_password(password, user["password_hash"]):
        return dict(user)
    return None


def register_user(username: str, email: str, password: str, full_name: str):
    """Register a new user. Returns (success: bool, message: str)."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)",
            (username, email, hash_password(password), full_name)
        )
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError as e:
        conn.close()
        if "username" in str(e):
            return False, "Username already exists."
        elif "email" in str(e):
            return False, "Email already registered."
        return False, "Registration failed."


# ─── CRUD: Instructors ────────────────────────────────────────────────────────

def get_all_instructors():
    conn = get_connection()
    rows = conn.execute("""
        SELECT i.id, i.full_name, i.short_name, i.status,
               GROUP_CONCAT(s.code, ', ') as subjects
        FROM instructors i
        LEFT JOIN instructor_subjects isub ON i.id = isub.instructor_id
        LEFT JOIN subjects s ON isub.subject_id = s.id
        GROUP BY i.id
        ORDER BY i.full_name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_instructor(instructor_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM instructors WHERE id = ?", (instructor_id,)).fetchone()
    subjects = conn.execute("""
        SELECT s.id, s.code, s.name FROM subjects s
        JOIN instructor_subjects isub ON s.id = isub.subject_id
        WHERE isub.instructor_id = ?
    """, (instructor_id,)).fetchall()
    conn.close()
    if row:
        result = dict(row)
        result["subject_list"] = [dict(s) for s in subjects]
        return result
    return None


def add_instructor(full_name: str, short_name: str, subject_ids: list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO instructors (full_name, short_name) VALUES (?, ?)",
        (full_name, short_name)
    )
    instr_id = cursor.lastrowid
    for sid in subject_ids:
        cursor.execute(
            "INSERT OR IGNORE INTO instructor_subjects (instructor_id, subject_id) VALUES (?, ?)",
            (instr_id, sid)
        )
    conn.commit()
    conn.close()
    return instr_id


def update_instructor(instructor_id: int, full_name: str, short_name: str, status: str, subject_ids: list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE instructors SET full_name=?, short_name=?, status=? WHERE id=?",
        (full_name, short_name, status, instructor_id)
    )
    cursor.execute("DELETE FROM instructor_subjects WHERE instructor_id=?", (instructor_id,))
    for sid in subject_ids:
        cursor.execute(
            "INSERT OR IGNORE INTO instructor_subjects (instructor_id, subject_id) VALUES (?, ?)",
            (instructor_id, sid)
        )
    conn.commit()
    conn.close()


def delete_instructor(instructor_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    # Remove related schedule entries referencing this instructor
    cursor.execute("DELETE FROM schedule_entries WHERE instructor_id = ?", (instructor_id,))
    # Remove instructor-subject links
    cursor.execute("DELETE FROM instructor_subjects WHERE instructor_id = ?", (instructor_id,))
    # Now delete the instructor
    cursor.execute("DELETE FROM instructors WHERE id = ?", (instructor_id,))
    conn.commit()
    conn.close()


# ─── CRUD: Subjects ──────────────────────────────────────────────────────────

def get_all_subjects():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM subjects ORDER BY code").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_subject(code: str, name: str, units: int, subject_type: str):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO subjects (code, name, units, subject_type) VALUES (?, ?, ?, ?)",
            (code, name, units, subject_type)
        )
        conn.commit()
        conn.close()
        return True, "Subject added."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Subject code already exists."


def delete_subject(subject_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
    conn.commit()
    conn.close()


# ─── CRUD: Blocks ─────────────────────────────────────────────────────────────

def get_all_blocks():
    conn = get_connection()
    rows = conn.execute("""
        SELECT b.id, p.name as program, p.year_level, b.section,
               p.name || ' ' || p.year_level || '-' || b.section as block_name
        FROM blocks b
        JOIN programs p ON b.program_id = p.id
        ORDER BY p.name, p.year_level, b.section
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_block_with_subjects(block_id: int):
    conn = get_connection()
    block = conn.execute("""
        SELECT b.id, p.name as program, p.year_level, b.section,
               p.name || ' ' || p.year_level || '-' || b.section as block_name
        FROM blocks b JOIN programs p ON b.program_id = p.id
        WHERE b.id = ?
    """, (block_id,)).fetchone()
    subjects = conn.execute("""
        SELECT s.id, s.code, s.name, s.units, s.subject_type
        FROM subjects s
        JOIN block_subjects bs ON s.id = bs.subject_id
        WHERE bs.block_id = ?
    """, (block_id,)).fetchall()
    conn.close()
    if block:
        result = dict(block)
        result["subjects"] = [dict(s) for s in subjects]
        return result
    return None


def assign_subject_to_block(block_id: int, subject_id: int):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO block_subjects (block_id, subject_id) VALUES (?, ?)",
            (block_id, subject_id)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def remove_subject_from_block(block_id: int, subject_id: int):
    conn = get_connection()
    conn.execute(
        "DELETE FROM block_subjects WHERE block_id = ? AND subject_id = ?",
        (block_id, subject_id)
    )
    conn.commit()
    conn.close()


def add_block(program_name: str, year_level: int, section: str):
    """Add a new block. Creates the program if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Get or create program
        prog = cursor.execute(
            "SELECT id FROM programs WHERE name = ? AND year_level = ?",
            (program_name, year_level)
        ).fetchone()
        if prog:
            prog_id = prog[0]
        else:
            cursor.execute(
                "INSERT INTO programs (name, year_level) VALUES (?, ?)",
                (program_name, year_level)
            )
            prog_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO blocks (program_id, section) VALUES (?, ?)",
            (prog_id, section)
        )
        conn.commit()
        conn.close()
        return True, "Block added successfully."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Block with this program/section already exists."


def delete_block(block_id: int):
    """Delete a block and its subject assignments."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedule_entries WHERE block_id = ?", (block_id,))
    cursor.execute("DELETE FROM block_subjects WHERE block_id = ?", (block_id,))
    cursor.execute("DELETE FROM blocks WHERE id = ?", (block_id,))
    conn.commit()
    conn.close()


def get_block_requirements():
    """Get all blocks with their assigned subjects and instructors."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT b.id as block_id, 
               p.name || ' ' || p.year_level || '-' || b.section as block_name,
               s.id as subject_id, s.code, s.name as subject_name, s.units,
               i.full_name as instructor_name, i.id as instructor_id
        FROM blocks b
        JOIN programs p ON b.program_id = p.id
        LEFT JOIN block_subjects bs ON b.id = bs.block_id
        LEFT JOIN subjects s ON bs.subject_id = s.id
        LEFT JOIN instructor_subjects isub ON s.id = isub.subject_id
        LEFT JOIN instructors i ON isub.instructor_id = i.id AND i.status = 'Active'
        ORDER BY p.name, p.year_level, b.section, s.code
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── CRUD: Rooms ──────────────────────────────────────────────────────────────

def get_all_rooms():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM rooms ORDER BY building, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── CRUD: Time Slots ─────────────────────────────────────────────────────────

def get_all_time_slots():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM time_slots ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── CRUD: Schedules ──────────────────────────────────────────────────────────

def save_schedule(name: str, entries: list):
    """Save a generated schedule with its entries.
    entries: list of dicts with keys block_id, subject_id, instructor_id, room_id, time_slot_id
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO schedules (name) VALUES (?)", (name,))
    schedule_id = cursor.lastrowid
    for e in entries:
        cursor.execute("""
            INSERT INTO schedule_entries (schedule_id, block_id, subject_id, instructor_id, room_id, time_slot_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (schedule_id, e["block_id"], e["subject_id"], e["instructor_id"], e["room_id"], e["time_slot_id"]))
    conn.commit()
    conn.close()
    return schedule_id


def get_all_schedules():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM schedules ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_schedule_entries(schedule_id: int):
    conn = get_connection()
    rows = conn.execute("""
        SELECT se.id, se.schedule_id,
               p.name || ' ' || p.year_level || '-' || bl.section as block_name,
               bl.id as block_id,
               s.code as subject_code, s.name as subject_name, s.units,
               i.full_name as instructor_name, i.id as instructor_id,
               r.name as room_name, r.building, r.id as room_id,
               ts.day, ts.start_hour, ts.end_hour, ts.id as time_slot_id
        FROM schedule_entries se
        JOIN blocks bl ON se.block_id = bl.id
        JOIN programs p ON bl.program_id = p.id
        JOIN subjects s ON se.subject_id = s.id
        JOIN instructors i ON se.instructor_id = i.id
        JOIN rooms r ON se.room_id = r.id
        JOIN time_slots ts ON se.time_slot_id = ts.id
        WHERE se.schedule_id = ?
        ORDER BY ts.day, ts.start_hour
    """, (schedule_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_schedule(schedule_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()


# ─── Dashboard Stats ──────────────────────────────────────────────────────────

def get_dashboard_stats():
    conn = get_connection()
    stats = {
        "instructors": conn.execute("SELECT COUNT(*) FROM instructors WHERE status='Active'").fetchone()[0],
        "subjects": conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0],
        "blocks": conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0],
        "rooms": conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0],
        "schedules": conn.execute("SELECT COUNT(*) FROM schedules").fetchone()[0],
    }
    conn.close()
    return stats
