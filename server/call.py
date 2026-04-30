from graph_tool import call

plan = call(
    semesters=8,
    credits=15,
    classes_taken=[
        "CS180",
        "CS193",
        "MA161"
    ],
    track="machine intelligence"
)

print(plan)
