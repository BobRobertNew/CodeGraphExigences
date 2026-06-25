import pandas as pd

# Dummy Data for Project A
data_A = {
    "Normes": ["Loi 1", "Loi 2", "Loi 3", "Loi 1"],
    "Exigence": [
        "The system must handle 1000 concurrent users.",
        "Data must be encrypted at rest.",
        "The UI must be responsive.",
        "The system must have an uptime of 99.9%."
    ],
    "Phase projet": ["Design", "Implementation", "Design", "Testing"],
    "Métier": ["Backend", "Security", "Frontend", "Ops"],
    "Preuve de conformité": ["Load test report", "Encryption certificate", "UI test report", "Uptime logs"]
}
df_A = pd.DataFrame(data_A)
df_A.to_excel("project_A.xlsx", index=False)

# Dummy Data for Project B (Shares some exigencies with A)
data_B = {
    "Normes": ["Loi 1", "Loi 4", "Loi 2"],
    "Exigence": [
        "The system must handle 1000 concurrent users.", # Shared with A
        "User passwords must be hashed.",
        "Data must be encrypted at rest." # Shared with A
    ],
    "Phase projet": ["Design", "Implementation", "Implementation"],
    "Métier": ["Backend", "Security", "Security"],
    "Preuve de conformité": ["Load test report v2", "Code review", "Encryption certificate v2"]
}
df_B = pd.DataFrame(data_B)
df_B.to_excel("project_B.xlsx", index=False)

# Dummy Data for Project C (Shares some with B, none with A)
data_C = {
    "Normes": ["Loi 4", "Loi 5"],
    "Exigence": [
        "User passwords must be hashed.", # Shared with B
        "The application must support multi-language."
    ],
    "Phase projet": ["Implementation", "Design"],
    "Métier": ["Security", "Frontend"],
    "Preuve de conformité": ["Security audit", "Translation files"]
}
df_C = pd.DataFrame(data_C)
df_C.to_excel("project_C.xlsx", index=False)

# Dummy Data for REX associated with Project A
data_rex_A = {
    "Exigence": [
        "The system must handle 1000 concurrent users.", # Link to Exg in A
        "The UI must be responsive." # Link to Exg in A
    ],
    "REX Detail": [ # Extra info not strictly needed by graph tool, but common in such files
        "We used AWS Auto Scaling, it worked perfectly.",
        "CSS Grid was very helpful for the UI."
    ]
}
df_rex_A = pd.DataFrame(data_rex_A)
df_rex_A.to_excel("rex_project_A.xlsx", index=False)

print("Dummy Excel files created successfully.")
