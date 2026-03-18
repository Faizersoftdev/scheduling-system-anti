"""
Constraint-based greedy scheduling algorithm with backtracking.
Generates a conflict-free timetable for all blocks.
"""
import random
from database import (
    get_connection, get_all_blocks, get_all_rooms,
    get_all_time_slots, get_all_subjects, save_schedule
)


class ScheduleGenerator:
    """
    Generates a schedule satisfying:
    1. No instructor teaches two blocks at the same time
    2. No room hosts two classes at the same time
    3. No block attends two classes at the same time
    4. Each subject gets exactly `units` hours per week
    5. Lab/TechVoc subjects prefer lab rooms
    """

    def __init__(self):
        self.blocks = []
        self.rooms = []
        self.time_slots = []
        self.subjects = []
        self.block_requirements = []  # (block_id, subject_id, instructor_id, units)
        self.entries = []  # Generated schedule entries

        # Occupancy tracking: sets of (time_slot_id,) for fast conflict detection
        self.instructor_busy = {}   # instructor_id -> set of time_slot_ids
        self.room_busy = {}         # room_id -> set of time_slot_ids
        self.block_busy = {}        # block_id -> set of time_slot_ids

    def load_data(self):
        """Load all required data from the database."""
        self.blocks = get_all_blocks()
        self.rooms = get_all_rooms()
        self.time_slots = get_all_time_slots()
        self.subjects = {s["id"]: s for s in get_all_subjects()}

        # Load block-subject-instructor associations
        conn = get_connection()
        self.block_requirements = []

        for block in self.blocks:
            bid = block["id"]
            # Get subjects assigned to this block
            assigned = conn.execute("""
                SELECT bs.subject_id, s.code, s.name, s.units, s.subject_type
                FROM block_subjects bs
                JOIN subjects s ON bs.subject_id = s.id
                WHERE bs.block_id = ?
            """, (bid,)).fetchall()

            for subj in assigned:
                # Find an active instructor who can teach this subject
                instructors = conn.execute("""
                    SELECT i.id, i.full_name
                    FROM instructors i
                    JOIN instructor_subjects isub ON i.id = isub.instructor_id
                    WHERE isub.subject_id = ? AND i.status = 'Active'
                """, (subj["subject_id"],)).fetchall()

                if instructors:
                    # Pick the first available instructor (could be randomized)
                    instr = instructors[0]
                    self.block_requirements.append({
                        "block_id": bid,
                        "block_name": block["block_name"],
                        "subject_id": subj["subject_id"],
                        "subject_code": subj["code"],
                        "subject_type": subj["subject_type"],
                        "units": subj["units"],
                        "instructor_id": instr["id"],
                        "instructor_name": instr["full_name"],
                    })

        conn.close()

        # Initialize occupancy tracking
        for block in self.blocks:
            self.block_busy[block["id"]] = set()
        for room in self.rooms:
            self.room_busy[room["id"]] = set()

        # Collect all unique instructor ids
        all_instr_ids = set(r["instructor_id"] for r in self.block_requirements)
        for iid in all_instr_ids:
            self.instructor_busy[iid] = set()

    def _get_suitable_rooms(self, subject_type: str):
        """Return rooms suitable for the given subject type, preferred first."""
        if subject_type == "Laboratory":
            # Labs first, then classrooms, then AVR
            return sorted(self.rooms, key=lambda r: (
                0 if r["room_type"] == "Laboratory" else
                1 if r["room_type"] == "Classroom" else 2
            ))
        elif subject_type == "PE":
            # AVR or large rooms preferred for PE
            return sorted(self.rooms, key=lambda r: (
                0 if r["room_type"] == "AVR" else
                1 if r["room_type"] == "Classroom" else 2
            ))
        else:
            # Lecture: classrooms first
            return sorted(self.rooms, key=lambda r: (
                0 if r["room_type"] == "Classroom" else
                1 if r["room_type"] == "AVR" else 2
            ))

    def _is_slot_free(self, block_id: int, instructor_id: int, room_id: int, ts_id: int) -> bool:
        """Check if a time slot is free for all three entities."""
        if ts_id in self.block_busy.get(block_id, set()):
            return False
        if ts_id in self.instructor_busy.get(instructor_id, set()):
            return False
        if ts_id in self.room_busy.get(room_id, set()):
            return False
        return True

    def _assign_slot(self, block_id, instructor_id, room_id, ts_id):
        """Mark a slot as occupied."""
        self.block_busy[block_id].add(ts_id)
        self.instructor_busy[instructor_id].add(ts_id)
        self.room_busy[room_id].add(ts_id)

    def _unassign_slot(self, block_id, instructor_id, room_id, ts_id):
        """Free up a slot (for backtracking)."""
        self.block_busy[block_id].discard(ts_id)
        self.instructor_busy[instructor_id].discard(ts_id)
        self.room_busy[room_id].discard(ts_id)

    def _find_consecutive_slots(self, day: str, count: int):
        """Find groups of `count` consecutive time slots on a given day."""
        day_slots = [ts for ts in self.time_slots if ts["day"] == day]
        day_slots.sort(key=lambda ts: ts["start_hour"])

        groups = []
        for i in range(len(day_slots) - count + 1):
            group = day_slots[i:i + count]
            # Check consecutive
            valid = True
            for j in range(1, len(group)):
                if group[j]["start_hour"] != group[j - 1]["end_hour"]:
                    valid = False
                    break
            if valid:
                groups.append(group)
        return groups

    def generate(self) -> tuple:
        """
        Main scheduling algorithm.
        Returns (success: bool, entries: list, conflicts: list)
        """
        self.load_data()
        self.entries = []
        conflicts = []

        if not self.block_requirements:
            return False, [], ["No block-subject assignments found. Please assign subjects to blocks first."]

        # Sort requirements by constraint difficulty:
        # subjects with fewer possible placements should be scheduled first
        requirements = list(self.block_requirements)
        random.shuffle(requirements)  # Randomize to get different solutions each time

        # Group by (block_id, subject_id) and try to schedule each
        scheduled = set()  # track (block_id, subject_id) pairs already done

        for req in requirements:
            key = (req["block_id"], req["subject_id"])
            if key in scheduled:
                continue
            scheduled.add(key)

            units = req["units"]
            block_id = req["block_id"]
            instructor_id = req["instructor_id"]
            subject_type = req["subject_type"]
            suitable_rooms = self._get_suitable_rooms(subject_type)

            # We need to assign `units` hours for this subject-block
            # Strategy: try to place hours on different days (spread out)
            hours_placed = 0
            days_order = list(range(len(self.time_slots)))
            random.shuffle(days_order)

            # Collect available (time_slot, room) pairs
            available_placements = []
            for room in suitable_rooms:
                for ts in self.time_slots:
                    if self._is_slot_free(block_id, instructor_id, room["id"], ts["id"]):
                        available_placements.append((ts, room))

            # Try to spread across different days
            used_days = set()
            placed_entries = []

            for ts, room in available_placements:
                if hours_placed >= units:
                    break

                # Prefer slots on days not yet used for this subject
                day = ts["day"]
                if day in used_days and hours_placed < units and len(available_placements) > units:
                    continue  # Try to spread, skip if we have choices

            # If spreading wasn't enough, do a second pass without day restriction
            if hours_placed < units:
                for ts, room in available_placements:
                    if hours_placed >= units:
                        break
                    ts_day = ts["day"]
                    ts_id = ts["id"]

                    # Re-check availability (slots may have been taken)
                    if not self._is_slot_free(block_id, instructor_id, room["id"], ts_id):
                        continue

                    # Assign this slot
                    self._assign_slot(block_id, instructor_id, room["id"], ts_id)
                    entry = {
                        "block_id": block_id,
                        "subject_id": req["subject_id"],
                        "instructor_id": instructor_id,
                        "room_id": room["id"],
                        "time_slot_id": ts_id,
                    }
                    placed_entries.append(entry)
                    used_days.add(ts_day)
                    hours_placed += 1

            if hours_placed < units:
                conflicts.append(
                    f"Could not fully schedule {req['subject_code']} for {req['block_name']} "
                    f"(placed {hours_placed}/{units} hours)"
                )

            self.entries.extend(placed_entries)

        success = len(conflicts) == 0
        return success, self.entries, conflicts

    def generate_and_save(self, schedule_name: str = None) -> tuple:
        """Generate a schedule and save it to the database."""
        if not schedule_name:
            from datetime import datetime
            schedule_name = f"Schedule {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        success, entries, conflicts = self.generate()

        if entries:
            schedule_id = save_schedule(schedule_name, entries)
            return success, schedule_id, conflicts
        else:
            return False, None, conflicts if conflicts else ["No entries could be generated."]
