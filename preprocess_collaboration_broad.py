import pandas as pd
import os

# === Load Datasets ===
grant_to_person = pd.read_csv("data/GrantToPerson.csv")
person = pd.read_csv("data/Person.csv")
institute = pd.read_csv("data/Institute.csv")
grant = pd.read_csv("data/Grant.csv")

# === Rename and merge Person → Institute ===
person = person.rename(columns={"PersonNumber": "PersonId", "InstituteNumber": "InstituteId"})
institute = institute.rename(columns={"InstituteNumber": "InstituteId", "Institute": "InstituteName"})

person_inst = person[["PersonId", "InstituteId"]].merge(
    institute[["InstituteId", "InstituteName", "InstituteCountry"]],
    on="InstituteId", how="left"
)

# === Merge GrantToPerson with person-institute info ===
grant_to_person = grant_to_person.rename(columns={"PersonNumber": "PersonId"})
merged = grant_to_person.merge(person_inst, on="PersonId", how="left")

# === Auto-detect StartDate column ===
date_cols = [col for col in grant.columns if "start" in col.lower()]
if date_cols:
    start_col = date_cols[0]
    print(f"📅 Using detected start date column: '{start_col}'")
    grant["ParsedStart"] = pd.to_datetime(grant[start_col], errors="coerce")
    grant["start_year"] = grant["ParsedStart"].dt.year
else:
    print("❌ No 'StartDate' column found. 'start_year' will be empty.")
    grant["start_year"] = None
    grant["AmountGranted"] = None

# === Ensure correct Grant ID column name ===
grant = grant.rename(columns={"GrantNumber": "GrantId"})

# === Merge grant info ===
merged = merged.merge(
    grant[["GrantId", "start_year", "AmountGranted"]],
    left_on="GrantNumber", right_on="GrantId", how="left"
)

# === Clean missing institute info ===
missing_before = merged["InstituteName"].isna().sum()
merged["InstituteName"] = merged["InstituteName"].fillna("Unknown")
merged["InstituteCountry"] = merged["InstituteCountry"].fillna("Unknown")
missing_after = merged["InstituteName"].isna().sum()

print(f"🔍 'Unknown' assigned to {missing_before - missing_after} missing institutes.")

# === Final columns for collaboration_data.csv ===
final = merged[[
    "GrantNumber", "PersonId", "Type", "InstituteName", "InstituteCountry",
    "start_year", "AmountGranted"
]]

# === Save to CSV ===
os.makedirs("data", exist_ok=True)
final.to_csv("data/collaboration_data.csv", index=False)
print(f"✅ Saved {len(final)} rows to data/collaboration_data.csv")
