# graph_tool.py
from __future__ import annotations

from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Set, Tuple
import re

__all__ = ["call"]


# Search controls. These defaults keep the solver fast while still producing
# realistic schedules. You can override them through call(...).
DEFAULT_MAX_COURSES_PER_SEMESTER = 5
DEFAULT_BEAM_WIDTH = 80
DEFAULT_MAX_AVAILABLE_CANDIDATES = 14


# =========================
# Expression helpers
# =========================

def COURSE(code: str) -> dict:
    return {"type": "course", "code": code}


def ALL(*args: dict) -> dict:
    return {"type": "all", "args": list(args)}


def ANY(*args: dict) -> dict:
    return {"type": "any", "args": list(args)}


def eval_expr(expr: Optional[dict], taken: Set[str]) -> bool:
    if expr is None:
        return True

    expr_type = expr["type"]
    if expr_type == "course":
        return expr["code"] in taken
    if expr_type == "all":
        return all(eval_expr(arg, taken) for arg in expr["args"])
    if expr_type == "any":
        return any(eval_expr(arg, taken) for arg in expr["args"])

    raise ValueError(f"Unknown expression type: {expr_type}")


def referenced_courses(expr: Optional[dict]) -> Set[str]:
    if expr is None:
        return set()

    expr_type = expr["type"]
    if expr_type == "course":
        return {expr["code"]}
    if expr_type in {"all", "any"}:
        out: Set[str] = set()
        for arg in expr["args"]:
            out |= referenced_courses(arg)
        return out

    raise ValueError(f"Unknown expression type: {expr_type}")


# =========================
# Course catalog
# =========================

COURSES: Dict[str, Dict] = {}


def add_course(
    code: str,
    title: str,
    credits: int,
    prereq: Optional[dict] = None,
    auto_select: bool = True,
) -> None:
    COURSES[code] = {
        "title": title,
        "credits": int(credits),
        "prereq": prereq,
        "auto_select": auto_select,
    }


# Common support / prerequisite courses
add_course("MA16100", "Plane Analytic Geometry and Calculus I", 5, None)
add_course("MA16200", "Plane Analytic Geometry and Calculus II", 5, COURSE("MA16100"))
add_course("MA26100", "Multivariate Calculus", 4, COURSE("MA16200"))
add_course("MA26500", "Linear Algebra", 3, COURSE("MA26100"))
add_course("STAT35000", "Introduction to Statistics", 3, COURSE("MA16200"))

add_course("MA26600", "Ordinary Differential Equations", 3, COURSE("MA26100"))
add_course("MA36600", "Ordinary Differential Equations", 4, COURSE("MA26500"))
add_course("STAT41600", "Probability", 3, COURSE("MA26100"))
add_course(
    "STAT51200",
    "Applied Regression Analysis",
    3,
    ANY(COURSE("STAT35000"), COURSE("STAT35500"), COURSE("STAT41700"), COURSE("STAT51100")),
)
add_course("MA38500", "Introduction to Logic", 3, COURSE("MA26100"))
add_course("MA45300", "Elements of Algebra I", 3, ANY(COURSE("MA26500"), COURSE("MA35100"), COURSE("MA35200")))
add_course("MA34100", "Foundations of Analysis", 3, COURSE("MA26100"))

# Core CS requirements
add_course("CS19300", "Tools", 1, None)
add_course("CS18000", "Problem Solving and Object-Oriented Programming", 4, COURSE("MA16100"))
add_course("CS18200", "Foundations of Computer Science", 3, ALL(COURSE("CS18000"), COURSE("MA16100")))
add_course("CS24000", "Programming in C", 3, COURSE("CS18000"))
add_course("CS25000", "Computer Architecture", 4, ALL(COURSE("CS18200"), COURSE("CS24000")))
add_course("CS25100", "Data Structures and Algorithms", 3, ALL(COURSE("CS18200"), COURSE("CS24000")))
add_course("CS25200", "Systems Programming", 4, ALL(COURSE("CS25000"), COURSE("CS25100")))

# Upper-level CS courses with explicit prerequisite logic
add_course("CS30700", "Software Engineering I", 3, ANY(COURSE("CS25100"), COURSE("CS25300")))
add_course("CS31100", "Competitive Programming II", 2, ANY(COURSE("CS21100"), COURSE("CS38100")))
add_course(
    "CS31400",
    "Numerical Methods",
    3,
    ALL(
        COURSE("CS18000"),
        ANY(COURSE("MA26200"), COURSE("MA26500"), COURSE("MA35000"), COURSE("MA35100")),
    ),
)
add_course(
    "CS33400",
    "Fundamentals of Computer Graphics",
    3,
    ALL(
        ANY(COURSE("MA26500"), COURSE("MA35000"), COURSE("MA35100")),
        ANY(COURSE("CS24000"), COURSE("ECE36800")),
    ),
)
add_course("CS34800", "Information Systems", 3, ANY(COURSE("CS25100"), COURSE("CS25300"), COURSE("ECE36800")))
add_course("CS35100", "Cloud Computing", 3, COURSE("CS25200"))
add_course("CS35200", "Compilers: Principles and Practice", 3, ALL(COURSE("CS25100"), COURSE("CS25200")))
add_course("CS35300", "Principles of Concurrency and Parallelism", 3, ALL(COURSE("CS25100"), COURSE("CS25200"), COURSE("CS35200")))
add_course("CS35400", "Operating Systems", 3, ALL(COURSE("CS25100"), COURSE("CS25200")))
add_course(
    "CS35500",
    "Introduction to Cryptography",
    3,
    ALL(
        ANY(COURSE("CS25100"), COURSE("CS25300"), COURSE("ECE36800")),
        ANY(
            COURSE("MA26200"),
            COURSE("MA26500"),
            COURSE("MA35000"),
            COURSE("MA35100"),
            COURSE("STAT35000"),
            COURSE("STAT51100"),
        ),
    ),
)
add_course(
    "CS37300",
    "Data Mining and Machine Learning",
    3,
    ALL(
        COURSE("CS18200"),
        ANY(COURSE("CS25100"), COURSE("CS25300")),
        ANY(COURSE("STAT35000"), COURSE("STAT35500"), COURSE("STAT51100")),
    ),
)
add_course(
    "CS38100",
    "Introduction to the Analysis of Algorithms",
    3,
    ALL(
        ANY(COURSE("CS25100"), COURSE("CS25300"), COURSE("ECE36800"), COURSE("ECE36900")),
        COURSE("MA26100"),
    ),
)
add_course("CS39000AALG", "Advanced Topics in Algorithms", 3, None, auto_select=False)
add_course("CS40700", "Software Engineering Senior Project", 3, COURSE("CS30700"))
add_course("CS40800", "Software Testing", 3, ANY(COURSE("CS25100"), COURSE("CS25300")))
add_course("CS41100", "Competitive Programming III", 2, COURSE("CS31100"))
add_course("CS42200", "Computer Networks", 3, ALL(COURSE("CS35400"), COURSE("CS25100"), COURSE("CS25200")))
add_course("CS42600", "Computer Security", 3, ALL(COURSE("CS25100"), COURSE("CS25200")))
add_course("CS43400", "Advanced Computer Graphics", 3, COURSE("CS33400"))
add_course("CS43900", "Introduction to Data Visualization", 3, ANY(COURSE("CS25100"), COURSE("CS25300")))
add_course("CS44000", "Large Scale Data Analytics", 3, ALL(COURSE("CS37300"), COURSE("STAT41700")), auto_select=False)
add_course("CS44800", "Introduction to Relational Database Systems", 3, ANY(COURSE("CS25100"), COURSE("CS25300")))
add_course("CS45600", "Programming Languages", 3, COURSE("CS35200"))
add_course("CS45800", "Introduction to Robotics", 3, ANY(COURSE("CS25100"), COURSE("CS25300")))
add_course("CS47100", "Introduction to Artificial Intelligence", 3, ANY(COURSE("CS25100"), COURSE("CS25300"), COURSE("ECE36800")))
add_course("CS47300", "Web Information Search and Management", 3, ANY(COURSE("CS25100"), COURSE("CS25300"), COURSE("ECE36800")))
add_course("CS47500", "Human-Computer Interaction", 3, ANY(COURSE("CS25100"), COURSE("CS25300")))
add_course(
    "CS47800",
    "Introduction to Bioinformatics",
    3,
    ALL(
        ANY(COURSE("BIOL23000"), COURSE("BIOL23100")),
        COURSE("BIOL24100"),
        COURSE("CS18000"),
    ),
)
add_course("CS48300", "Introduction to the Theory of Computation", 3, ANY(COURSE("CS38100"), COURSE("CS39000AALG")))
add_course("CS48900", "Embedded Systems", 3, ALL(COURSE("CS25000"), COURSE("CS25100"), COURSE("CS25200")))

# Officially listed but non-standard / variable-title / graduate-restricted options.
# They count if already completed, but the planner does not auto-select them.
add_course("CS49000DSO", "Distributed Systems", 3, None, auto_select=False)
add_course("CS49000SWS", "Software Security", 3, None, auto_select=False)
add_course("CS49000VR", "Introduction to VR/AR", 3, None, auto_select=False)
add_course("CS49000SENIORPROJECT", "Senior Project", 3, None, auto_select=False)
add_course("CS49700", "Honors Research Project", 3, None, auto_select=False)
add_course("CS51000", "Software Engineering", 3, COURSE("CS25100"), auto_select=False)
add_course("CS51400", "Numerical Analysis", 3, COURSE("CS31400"), auto_select=False)
add_course("CS51500", "Numerical Linear Algebra", 3, None, auto_select=False)
add_course("CS52000", "Computational Methods in Optimization", 3, None, auto_select=False)
add_course("CS52500", "Parallel Computing", 3, None, auto_select=False)
add_course("CS56000", "Reasoning About Programs", 3, ALL(COURSE("CS18200"), COURSE("CS25200"), COURSE("CS38100")), auto_select=False)
add_course("CS57700", "Natural Language Processing", 3, None, auto_select=False)
add_course("CS57800", "Statistical Machine Learning", 3, None, auto_select=False)
add_course("CS59000SRS", "Software Reliability and Security", 3, None, auto_select=False)

# External / supporting / transcript-recognized only
add_course("EPCS41100", "EPICS Senior Design I", 1, None, auto_select=False)
add_course("EPCS41200", "EPICS Senior Design II", 1, None, auto_select=False)
add_course("ECE30100", "Signals and Systems", 3, None, auto_select=False)
add_course("IE33500", "Operations Research - Optimization", 3, None, auto_select=False)
add_course("IE33600", "Operations Research - Stochastic Models", 3, None, auto_select=False)
add_course("MA35301", "Linear Algebra II", 3, None, auto_select=False)
add_course("MA36200", "Topics in Vector Calculus", 3, None, auto_select=False)
add_course("MA42100", "Linear Programming and Optimization Techniques", 3, None, auto_select=False)
add_course("MA44000", "Analysis II", 3, None, auto_select=False)

# Alternative prerequisite markers / equivalence-friendly transcript recognition
add_course("CS21100", "Competitive Programming I", 2, None, auto_select=False)
add_course("CS25300", "Data Structures and Algorithms for DS/AI", 3, None, auto_select=False)
add_course("ECE36800", "Data Structures", 3, None, auto_select=False)
add_course("ECE36900", "Discrete Mathematics for Engineers", 3, None, auto_select=False)
add_course("ECE46900", "Operating Systems Engineering", 3, None, auto_select=False)
add_course("STAT35500", "Statistics for Data Science", 3, None, auto_select=False)
add_course("STAT51100", "Statistical Methods", 3, None, auto_select=False)
add_course("STAT41700", "Statistical Theory", 3, None, auto_select=False)
add_course("MA26200", "Linear Algebra and Differential Equations", 4, None, auto_select=False)
add_course("MA35000", "Linear Algebra I", 3, None, auto_select=False)
add_course("MA35100", "Elementary Linear Algebra", 3, None, auto_select=False)
add_course("MA35200", "Linear Algebra II", 3, None, auto_select=False)
add_course("MA35300", "Linear Algebra I", 3, None, auto_select=False)
add_course("MA51100", "Linear Algebra", 3, None, auto_select=False)
add_course("BIOL23000", "Structure and Function of Organisms I", 4, None, auto_select=False)
add_course("BIOL23100", "Structure and Function of Organisms II", 4, None, auto_select=False)
add_course("BIOL24100", "Genetics", 3, None, auto_select=False)


CORE_REQUIRED = (
    "CS19300",
    "CS18000",
    "CS18200",
    "CS24000",
    "CS25000",
    "CS25100",
    "CS25200",
)


# =========================
# Requirement slot helpers
# =========================

def option(*courses: str, tags: Tuple[str, ...] = (), auto_select: Optional[bool] = None, cs_count: Optional[int] = None) -> Dict:
    if auto_select is None:
        auto_select = all(COURSES.get(course, {}).get("auto_select", False) for course in courses)

    if cs_count is None:
        cs_count = 1 if all(course.startswith("CS") for course in courses) else 0

    return {
        "courses": tuple(courses),
        "tags": tuple(tags),
        "auto_select": bool(auto_select),
        "cs_count": int(cs_count),
    }


def repeat_slots(n: int, options: List[Dict]) -> List[List[Dict]]:
    return [list(options) for _ in range(n)]


ALGO_SLOT = [option("CS38100"), option("CS39000AALG", auto_select=False)]

TRACKS: Dict[str, Dict] = {
    "computational_science_and_engineering": {
        "display": "Computational Science and Engineering",
        "min_cs_slots": 4,
        "slots": [
            [option("MA26600", cs_count=0), option("MA36600", cs_count=0)],
            [option("CS31400")],
            ALGO_SLOT,
            [option("CS37300"), option("CS47300"), option("CS47800"), option("IE33600", auto_select=False, cs_count=0), option("ECE30100", auto_select=False, cs_count=0)],
            [option("CS35200"), option("CS35300"), option("CS35400")],
            *repeat_slots(
                2,
                [
                    option("CS30700"),
                    option("CS42200"),
                    option("CS45600"),
                    option("CS45800"),
                    option("CS47100"),
                    option("CS48300"),
                    option("CS51400", auto_select=False),
                    option("CS51500", auto_select=False),
                    option("CS52000", auto_select=False),
                    option("CS52500", auto_select=False),
                    option("IE33500", auto_select=False, cs_count=0),
                    option("MA34100", cs_count=0),
                    option("MA44000", auto_select=False, cs_count=0),
                    # Extra Applications / Systems courses may also count as electives.
                    option("CS37300"),
                    option("CS47300"),
                    option("CS47800"),
                    option("IE33600", auto_select=False, cs_count=0),
                    option("ECE30100", auto_select=False, cs_count=0),
                    option("CS35200"),
                    option("CS35300"),
                    option("CS35400"),
                ],
            ),
        ],
    },
    "computer_graphics_and_visualization": {
        "display": "Computer Graphics and Visualization",
        "slots": [
            [option("CS31400")],
            [option("CS33400")],
            [option("CS37300"), option("CS43400"), option("CS47100")],
            *repeat_slots(
                3,
                [
                    option("CS35200"),
                    option("CS35400"),
                    option("CS37300"),
                    option("CS38100"),
                    option("CS39000AALG", auto_select=False),
                    option("CS42200"),
                    option("CS43400"),
                    option("CS43900"),
                    option("CS45600"),
                    option("CS45800"),
                    option("CS47100"),
                    option("CS49000VR", auto_select=False),
                ],
            ),
        ],
    },
    "database_and_information_systems": {
        "display": "Database and Information Systems",
        "slots": [
            [option("CS34800")],
            ALGO_SLOT,
            [option("CS44800")],
            [option("CS37300"), option("CS47300")],
            [option("CS35200"), option("CS35300"), option("CS35400")],
            [option("CS35500"), option("CS42600")],
            [
                option("CS37300"),
                option("CS42200"),
                option("CS47100"),
                option("CS47300"),
                option("CS47800"),
                option("CS48300"),
                option("CS49000SENIORPROJECT", auto_select=False),
                option("CS49700", auto_select=False),
                option("EPCS41100", "EPCS41200", auto_select=False, cs_count=0),
            ],
        ],
    },
    "algorithmic_foundations": {
        "display": "Algorithmic Foundations",
        "slots": [
            [option("CS35200"), option("CS35400")],
            [option("CS37300"), option("CS47100")],
            ALGO_SLOT,
            *repeat_slots(
                3,
                [
                    option("CS31100", "CS41100"),
                    option("CS31400"),
                    option("CS33400"),
                    option("CS35300"),
                    option("CS35500"),
                    option("CS44800"),
                    option("CS45600"),
                    option("CS45800"),
                    option("CS48300"),
                    option("MA34100", cs_count=0),
                    option("MA35300", auto_select=False, cs_count=0),
                    option("MA35301", auto_select=False, cs_count=0),
                    option("MA36200", auto_select=False, cs_count=0),
                    option("MA36600", cs_count=0),
                    option("MA38500", cs_count=0),
                    option("MA42100", auto_select=False, cs_count=0),
                    option("MA45300", cs_count=0),
                ],
            ),
        ],
    },
    "machine_intelligence": {
        "display": "Machine Intelligence",
        "slots": [
            [option("CS37300")],
            ALGO_SLOT,
            [option("CS47100"), option("CS47300")],
            [option("STAT41600", cs_count=0), option("STAT51200", cs_count=0)],
            *repeat_slots(
                2,
                [
                    option("CS31400"),
                    option("CS34800"),
                    option("CS35200"),
                    option("CS44800"),
                    option("CS45600"),
                    option("CS45800"),
                    option("CS47100"),
                    option("CS47300"),
                    option("CS48300"),
                    option("CS43900"),
                    option("CS44000", auto_select=False),
                    option("CS47500"),
                    option("CS57700", auto_select=False),
                    option("CS57800", auto_select=False),
                    option("CS31100", "CS41100", auto_select=False),  # case-by-case approval
                ],
            ),
        ],
    },
    "programming_languages": {
        "display": "Programming Languages",
        "slots": [
            [option("CS35200")],
            [option("CS35400")],
            [option("CS45600")],
            *repeat_slots(
                3,
                [
                    option("CS30700", tags=("pl_line1",)),
                    option("CS40800", tags=("pl_line1",)),
                    option("CS34800", tags=("pl_line2",)),
                    option("CS44800", tags=("pl_line2",)),
                    option("CS35300"),
                    option("CS38100"),
                    option("CS39000AALG", auto_select=False),
                    option("CS42600"),
                    option("CS48300"),
                    option("CS56000", auto_select=False),
                    option("MA38500", tags=("pl_line3",), cs_count=0),
                    option("MA45300", tags=("pl_line3",), cs_count=0),
                ],
            ),
        ],
    },
    "security": {
        "display": "Security",
        "slots": [
            [option("CS35400")],
            [option("CS35500")],
            [option("CS42600")],
            *repeat_slots(
                3,
                [
                    option("CS30700", tags=("sec_line1",)),
                    option("CS40800", tags=("sec_line1",)),
                    option("CS34800", tags=("sec_line2",)),
                    option("CS44800", tags=("sec_line2",)),
                    option("CS47300", tags=("sec_line2",)),
                    option("CS35200"),
                    option("CS35300", tags=("sec_line4",)),
                    option("CS45600", tags=("sec_line4",)),
                    option("CS37300", tags=("sec_line5",)),
                    option("CS47100", tags=("sec_line5",)),
                    option("CS38100"),
                    option("CS39000AALG", auto_select=False),
                    option("CS42200"),
                    option("CS48900", tags=("sec_line8",)),
                    option("CS49000DSO", tags=("sec_line8",), auto_select=False),
                    option("CS49000SWS", auto_select=False),
                ],
            ),
        ],
    },
    "software_engineering": {
        "display": "Software Engineering",
        "slots": [
            [option("CS30700")],
            [option("CS35200"), option("CS35400")],
            ALGO_SLOT,
            [option("CS40800")],
            [option("CS40700")],
            [
                option("CS31100", "CS41100"),
                option("CS34800"),
                option("CS35100"),
                option("CS35200"),
                option("CS35300"),
                option("CS35400"),
                option("CS37300"),
                option("CS42200"),
                option("CS42600"),
                option("CS44800"),
                option("CS45600"),
                option("CS47100"),
                option("CS47300"),
                option("CS48900"),
                option("CS49000DSO", auto_select=False),
                option("CS49000SWS", auto_select=False),
                option("CS51000", auto_select=False),
                option("CS59000SRS", auto_select=False),
            ],
        ],
    },
    "systems_software": {
        "display": "Systems Software",
        "slots": [
            [option("CS35200")],
            [option("CS35400")],
            [option("CS42200")],
            *repeat_slots(
                3,
                [
                    option("CS30700"),
                    option("CS31100", "CS41100"),
                    option("CS33400"),
                    option("CS35100"),
                    option("CS35300"),
                    option("CS38100"),
                    option("CS39000AALG", auto_select=False),
                    option("CS42600"),
                    option("CS44800"),
                    option("CS45600"),
                    option("CS48900"),
                    option("CS49000DSO", auto_select=False),
                    option("CS49000VR", auto_select=False),
                    option("CS49000SENIORPROJECT", auto_select=False),
                ],
            ),
        ],
    },
}


# =========================
# Normalization
# =========================

TRACK_ALIASES = {
    "machineintelligence": "machine_intelligence",
    "mi": "machine_intelligence",
    "machine_intelligence": "machine_intelligence",
    "computationalscienceandengineering": "computational_science_and_engineering",
    "cse": "computational_science_and_engineering",
    "computergraphicsandvisualization": "computer_graphics_and_visualization",
    "graphics": "computer_graphics_and_visualization",
    "cgv": "computer_graphics_and_visualization",
    "databaseandinformationsystems": "database_and_information_systems",
    "database": "database_and_information_systems",
    "dbis": "database_and_information_systems",
    "algorithmicfoundations": "algorithmic_foundations",
    "foundations": "algorithmic_foundations",
    "af": "algorithmic_foundations",
    "programminglanguages": "programming_languages",
    "pl": "programming_languages",
    "security": "security",
    "softwareengineering": "software_engineering",
    "softeng": "software_engineering",
    "systemssoftware": "systems_software",
    "systemsoftware": "systems_software",
    "systemsprogramming": "systems_software",
}

MANUAL_CODE_ALIASES = {
    "MA41600": "STAT41600",
    "EE36800": "ECE36800",
    "EE46900": "ECE46900",
    "BIOL47800": "CS47800",
    "MATH26100": "MA26100",
    "MATH26200": "MA26200",
    # Common calculus-sequence simplifications
    "MA16300": "MA16100",
    "MA16500": "MA16100",
    "MATH16500": "MA16100",
    "MA16700": "MA16100",
    "MA17400": "MA26100",
    "MA18200": "MA26100",
    "MA26300": "MA26100",
    "MA27100": "MA26100",
    "MA27101": "MA26100",
}

TITLE_ALIASES: Dict[str, str] = {}
for code, data in COURSES.items():
    normalized_title = re.sub(r"[^A-Z0-9]+", "", data["title"].upper())
    TITLE_ALIASES[normalized_title] = code

TITLE_ALIASES.update({
    "TOOLS": "CS19300",
    "SOFTWAREENGINEERINGSENIORPROJECT": "CS40700",
    "ADVANCEDTOPICSINALGORITHMS": "CS39000AALG",
    "DISTRIBUTEDSYSTEMS": "CS49000DSO",
    "SOFTWARESECURITY": "CS49000SWS",
    "INTRODUCTIONTOVRAR": "CS49000VR",
    "SENIORPROJECT": "CS49000SENIORPROJECT",
    "HONORSRESEARCHPROJECT": "CS49700",
    "PROBABILITY": "STAT41600",
})


def normalize_track(track: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "", (track or "").lower())
    return TRACK_ALIASES.get(key, "machine_intelligence")


def normalize_course_name(raw: str) -> str:
    if not isinstance(raw, str):
        raise TypeError("Every item in classes_taken must be a string.")

    compact = re.sub(r"[^A-Z0-9]+", "", raw.upper())

    if compact in TITLE_ALIASES:
        return TITLE_ALIASES[compact]

    # Handle common code forms like CS340, CS34000, CS490DSO, CS49000DSO.
    match = re.match(r"^([A-Z]+)(\d{3,5})([A-Z0-9]*)$", compact)
    if match:
        subject, digits, suffix = match.groups()
        digits = digits.ljust(5, "0")
        code = f"{subject}{digits}{suffix}"
        return MANUAL_CODE_ALIASES.get(code, code)

    return MANUAL_CODE_ALIASES.get(compact, compact)


# =========================
# Requirement evaluation
# =========================

def track_slots(track_key: str) -> List[List[Dict]]:
    return TRACKS[track_key]["slots"]


@lru_cache(maxsize=None)
def track_satisfied_cached(track_key: str, taken_frozen: frozenset) -> bool:
    taken = set(taken_frozen)
    slots = track_slots(track_key)
    min_cs_slots = int(TRACKS[track_key].get("min_cs_slots", 0))

    @lru_cache(maxsize=None)
    def dfs(slot_idx: int, used_courses: frozenset, used_tags: frozenset, cs_slots: int) -> bool:
        if slot_idx == len(slots):
            return cs_slots >= min_cs_slots

        used_course_set = set(used_courses)
        used_tag_set = set(used_tags)

        for opt in slots[slot_idx]:
            course_set = set(opt["courses"])
            tag_set = set(opt["tags"])

            if not course_set.issubset(taken):
                continue
            if course_set & used_course_set:
                continue
            if tag_set & used_tag_set:
                continue

            if dfs(
                slot_idx + 1,
                frozenset(used_course_set | course_set),
                frozenset(used_tag_set | tag_set),
                cs_slots + int(opt["cs_count"]),
            ):
                return True

        return False

    return dfs(0, frozenset(), frozenset(), 0)


def requirements_met(track_key: str, taken: Set[str]) -> bool:
    return all(course in taken for course in CORE_REQUIRED) and track_satisfied_cached(track_key, frozenset(taken))


def direct_requirement_courses(track_key: str, auto_select_only: bool = False) -> Set[str]:
    out = set(CORE_REQUIRED)
    for slot in TRACKS[track_key]["slots"]:
        for opt in slot:
            if auto_select_only and not opt.get("auto_select", True):
                continue
            out.update(opt["courses"])
    return out


def relevant_closure(track_key: str) -> Set[str]:
    # The planner should not auto-plan variable-title, graduate-restricted,
    # or case-by-case courses. They still count when already completed, but
    # they are intentionally excluded from generated candidates.
    seeds = direct_requirement_courses(track_key, auto_select_only=True)
    seen: Set[str] = set()
    stack = list(seeds)

    while stack:
        code = stack.pop()
        if code in seen:
            continue
        seen.add(code)

        data = COURSES.get(code)
        if data is None:
            continue

        for prereq_code in referenced_courses(data["prereq"]):
            if prereq_code in COURSES and prereq_code not in seen:
                stack.append(prereq_code)

    return seen


CLOSURE_BY_TRACK = {track_key: relevant_closure(track_key) for track_key in TRACKS}


def reverse_dependencies(track_key: str) -> Dict[str, Set[str]]:
    closure = CLOSURE_BY_TRACK[track_key]
    rev: Dict[str, Set[str]] = {}
    for course in closure:
        rev.setdefault(course, set())
    for course in closure:
        for prereq_code in referenced_courses(COURSES[course]["prereq"]):
            if prereq_code in closure:
                rev.setdefault(prereq_code, set()).add(course)
    return rev


REVERSE_DEPS_BY_TRACK = {track_key: reverse_dependencies(track_key) for track_key in TRACKS}


def course_is_available(code: str, taken: Set[str]) -> bool:
    return eval_expr(COURSES[code]["prereq"], taken)


def automatic_candidates(track_key: str, taken: Set[str]) -> List[str]:
    closure = CLOSURE_BY_TRACK[track_key]
    candidates = []

    for code in closure:
        if code in taken:
            continue
        data = COURSES[code]
        if not data["auto_select"]:
            continue
        if course_is_available(code, taken):
            candidates.append(code)

    rev = REVERSE_DEPS_BY_TRACK[track_key]
    direct = direct_requirement_courses(track_key)

    def sort_key(code: str) -> Tuple[int, int, int, str]:
        is_direct = 1 if code in direct else 0
        unlocks = len(rev.get(code, set()) & closure)
        credits = COURSES[code]["credits"]
        return (-is_direct, -unlocks, -credits, code)

    return sorted(candidates, key=sort_key)


@lru_cache(maxsize=None)
def track_progress_count_cached(track_key: str, taken_frozen: frozenset) -> int:
    """Maximum number of track slots that can be filled by the taken set.

    This is used only for search ordering. Full validation still happens in
    track_satisfied_cached(...).
    """
    taken = set(taken_frozen)
    slots = track_slots(track_key)

    @lru_cache(maxsize=None)
    def dfs(slot_idx: int, used_courses: frozenset, used_tags: frozenset) -> int:
        if slot_idx == len(slots):
            return 0

        # Option 1: skip this slot for progress-count purposes.
        best = dfs(slot_idx + 1, used_courses, used_tags)

        used_course_set = set(used_courses)
        used_tag_set = set(used_tags)

        for opt in slots[slot_idx]:
            course_set = set(opt["courses"])
            tag_set = set(opt["tags"])

            if not course_set.issubset(taken):
                continue
            if course_set & used_course_set:
                continue
            if tag_set & used_tag_set:
                continue

            best = max(
                best,
                1 + dfs(
                    slot_idx + 1,
                    frozenset(used_course_set | course_set),
                    frozenset(used_tag_set | tag_set),
                ),
            )

        return best

    return dfs(0, frozenset(), frozenset())


def state_progress_score(track_key: str, taken: Set[str]) -> Tuple[int, int]:
    core_done = sum(1 for course in CORE_REQUIRED if course in taken)
    track_done = track_progress_count_cached(track_key, frozenset(taken))
    return core_done, track_done


def _course_priority(track_key: str, code: str) -> Tuple[int, int, int, int, str]:
    """Priority used to order courses before building semester subsets.

    Lower tuple is better. Direct requirement courses come first, then courses that
    unlock many later courses, then higher-credit courses.
    """
    direct = direct_requirement_courses(track_key)
    rev = REVERSE_DEPS_BY_TRACK[track_key]
    is_direct = 1 if code in direct else 0
    unlocks = len(rev.get(code, set()))
    credits = COURSES[code]["credits"]
    auto = 1 if COURSES[code].get("auto_select", False) else 0
    return (-is_direct, -unlocks, -auto, -credits, code)


def generate_semester_subsets(
    track_key: str,
    available: List[str],
    taken_frozen: frozenset,
    credit_cap: int,
    max_courses_per_semester: int = DEFAULT_MAX_COURSES_PER_SEMESTER,
    beam_width: int = DEFAULT_BEAM_WIDTH,
    max_available_candidates: int = DEFAULT_MAX_AVAILABLE_CANDIDATES,
) -> List[Tuple[str, ...]]:
    """Return promising non-empty subsets of available courses.

    The old version generated every subset under the credit cap. That is the
    primary reason the planner becomes slow. This version keeps the best
    available candidates, limits realistic semester size, sorts by usefulness,
    and trims to a beam width.
    """
    if credit_cap <= 0:
        return []

    max_courses_per_semester = max(1, int(max_courses_per_semester))
    beam_width = max(1, int(beam_width))
    max_available_candidates = max(1, int(max_available_candidates))

    direct = direct_requirement_courses(track_key)
    rev = REVERSE_DEPS_BY_TRACK[track_key]
    base_taken = set(taken_frozen)
    base_core_done, base_track_done = state_progress_score(track_key, base_taken)

    available = sorted(set(available), key=lambda code: _course_priority(track_key, code))
    available = available[:max_available_candidates]

    subsets: List[Tuple[str, ...]] = []

    def backtrack(start: int, current: List[str], current_credits: int) -> None:
        if current:
            subsets.append(tuple(sorted(current)))

        if len(current) >= max_courses_per_semester:
            return

        for idx in range(start, len(available)):
            code = available[idx]
            next_credits = current_credits + COURSES[code]["credits"]
            if next_credits > credit_cap:
                continue

            current.append(code)
            backtrack(idx + 1, current, next_credits)
            current.pop()

    backtrack(0, [], 0)

    def subset_key(subset: Tuple[str, ...]) -> Tuple[int, int, int, int, int, Tuple[str, ...]]:
        next_taken = base_taken | set(subset)
        next_core_done, next_track_done = state_progress_score(track_key, next_taken)
        core_delta = next_core_done - base_core_done
        track_delta = next_track_done - base_track_done
        unlock_count = sum(len(rev.get(code, set())) for code in subset)
        credits = sum(COURSES[code]["credits"] for code in subset)
        course_count = len(subset)
        # Prefer real requirement progress first. Then prefer prerequisite
        # unlocking. Only after that, prefer smaller semesters to avoid taking
        # unnecessary electives just because they fit.
        return (-core_delta, -track_delta, -unlock_count, credits, course_count, subset)

    subsets.sort(key=subset_key)
    return subsets[:beam_width]


@lru_cache(maxsize=None)
def generate_semester_subsets_cached(
    track_key: str,
    available_tuple: Tuple[str, ...],
    taken_frozen: frozenset,
    credit_cap: int,
    max_courses_per_semester: int,
    beam_width: int,
    max_available_candidates: int,
) -> Tuple[Tuple[str, ...], ...]:
    return tuple(
        generate_semester_subsets(
            track_key=track_key,
            available=list(available_tuple),
            taken_frozen=taken_frozen,
            credit_cap=credit_cap,
            max_courses_per_semester=max_courses_per_semester,
            beam_width=beam_width,
            max_available_candidates=max_available_candidates,
        )
    )


def _slot_already_satisfied(slot: List[Dict], taken: Set[str]) -> bool:
    return any(set(opt["courses"]).issubset(taken) for opt in slot)


def remaining_relevant_courses_underestimate(track_key: str, taken: Set[str]) -> Set[str]:
    """Cheap lower-bound estimate of still-needed courses.

    This intentionally underestimates. It is safe for pruning because it only
    rejects a state if even this optimistic estimate cannot fit.
    """
    needed: Set[str] = {course for course in CORE_REQUIRED if course not in taken}

    for slot in TRACKS[track_key]["slots"]:
        if _slot_already_satisfied(slot, taken):
            continue
        usable_options = [opt for opt in slot if opt.get("auto_select", True)] or list(slot)
        cheapest = min(
            usable_options,
            key=lambda opt: sum(COURSES[c]["credits"] for c in opt["courses"] if c in COURSES),
        )
        needed.update(c for c in cheapest["courses"] if c not in taken and c in COURSES)

    return needed


def credit_lower_bound_semesters(track_key: str, taken: Set[str], credit_cap: int) -> int:
    if credit_cap <= 0:
        return 10**9
    remaining = remaining_relevant_courses_underestimate(track_key, taken)
    remaining_credits = sum(COURSES[c]["credits"] for c in remaining if c in COURSES)
    return (remaining_credits + credit_cap - 1) // credit_cap


def plan_key(plan: Tuple[Tuple[str, ...], ...]) -> Tuple:
    semesters_used = len(plan)
    total_credits = sum(COURSES[code]["credits"] for semester in plan for code in semester)
    return (semesters_used, total_credits, plan)


# =========================
# Public solver
# =========================

def call(
    semesters: int,
    credits: int,
    classes_taken: Iterable[str],
    track: str = "machine intelligence",
    fast: bool = True,
    max_courses_per_semester: int = DEFAULT_MAX_COURSES_PER_SEMESTER,
    beam_width: int = DEFAULT_BEAM_WIDTH,
    max_available_candidates: int = DEFAULT_MAX_AVAILABLE_CANDIDATES,
) -> Dict:
    """
    Return a JSON-serializable dictionary containing an optimal semester-by-semester plan.

    Parameters
    ----------
    semesters:
        Maximum number of future semesters allowed.
    credits:
        Maximum credits per semester. This is hard-capped at 18.
    classes_taken:
        Iterable of already-completed courses. Inputs are normalized automatically.
    track:
        Student track. Defaults to "machine intelligence".
    fast:
        If True, return the first valid high-priority plan. If False, continue
        searching inside the bounded beam for the best plan found.
    max_courses_per_semester:
        Hard cap on number of courses in a generated semester subset.
    beam_width:
        Maximum number of semester subsets considered per state.
    max_available_candidates:
        Maximum number of available candidate courses used to build subsets.

    Returns
    -------
    dict
        {} if no valid plan is found; otherwise a semester-by-semester plan.
    """
    if semesters is None or credits is None:
        return {}
    if semesters <= 0:
        return {}

    credit_cap = max(1, min(int(credits), 18))
    track_key = normalize_track(track)

    max_courses_per_semester = max(1, min(int(max_courses_per_semester), 6))
    beam_width = max(1, int(beam_width))
    max_available_candidates = max(1, int(max_available_candidates))

    normalized_taken: Set[str] = set()
    for item in classes_taken or []:
        normalized_taken.add(normalize_course_name(item))

    @lru_cache(maxsize=None)
    def solve(semesters_left: int, taken_frozen: frozenset) -> Optional[Tuple[Tuple[str, ...], ...]]:
        taken = set(taken_frozen)

        if requirements_met(track_key, taken):
            return tuple()

        if semesters_left == 0:
            return None

        if credit_lower_bound_semesters(track_key, taken, credit_cap) > semesters_left:
            return None

        available = tuple(automatic_candidates(track_key, taken))
        if not available:
            return None

        best_plan: Optional[Tuple[Tuple[str, ...], ...]] = None

        for semester_choice in generate_semester_subsets_cached(
            track_key,
            available,
            taken_frozen,
            credit_cap,
            max_courses_per_semester,
            beam_width,
            max_available_candidates,
        ):
            next_taken = frozenset(taken | set(semester_choice))
            suffix = solve(semesters_left - 1, next_taken)
            if suffix is None:
                continue

            # Purdue says CS 40700 should be in the student's last or next-to-last semester.
            # Because we minimize the number of non-empty semesters, this means there may be
            # at most 1 additional non-empty semester after the semester containing CS 40700.
            if "CS40700" in semester_choice and len(suffix) > 1:
                continue

            candidate = (tuple(sorted(semester_choice)),) + suffix

            if fast:
                return candidate

            if best_plan is None or plan_key(candidate) < plan_key(best_plan):
                best_plan = candidate

        return best_plan

    raw_plan = solve(int(semesters), frozenset(normalized_taken))
    if raw_plan is None:
        return {}

    formatted_plan = []
    total_credits = 0

    for idx, semester_courses in enumerate(raw_plan, start=1):
        semester_credit_total = sum(COURSES[code]["credits"] for code in semester_courses)
        total_credits += semester_credit_total
        formatted_plan.append(
            {
                "semester": idx,
                "credits": semester_credit_total,
                "courses": [
                    {
                        "code": code,
                        "title": COURSES[code]["title"],
                        "credits": COURSES[code]["credits"],
                    }
                    for code in semester_courses
                ],
            }
        )

    return {
        "track": TRACKS[track_key]["display"],
        "normalized_track": track_key,
        "credit_cap": credit_cap,
        "normalized_classes_taken": sorted(normalized_taken),
        "search_mode": "fast" if fast else "bounded_optimal",
        "max_courses_per_semester": max_courses_per_semester,
        "beam_width": beam_width,
        "max_available_candidates": max_available_candidates,
        "semesters_used": len(raw_plan),
        "total_credits": total_credits,
        "plan": formatted_plan,
    }

