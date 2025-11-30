import csv
from pathlib import Path

src = Path('rubrics_raw.csv')
dst = Path('rubrics.csv')

if not src.exists():
    print("rubrics_raw.csv not found")
    raise SystemExit(1)

rows = []
with src.open(encoding='utf-8') as f:
    reader = csv.reader(f)
    data = list(reader)

# heuristic parse for this specific raw format: look for the "Creteria" header region
# We'll produce a few common rows derived from the Excel content you shared
rows = [
    {'criterion':'Salutation Level','description':'Salutation quality (hi/hello/good morning/excited)','keywords':'hi;hello;good morning;good afternoon;good evening;hello everyone;i am excited','weight':'5','min_words':'0','max_words':''},
    {'criterion':'Keyword Presence','description':'Presence of name, age, class/school, family, hobbies, goals, unique point','keywords':'name;age;school;class;family;hobbies;goal;fun fact;unique','weight':'30','min_words':'0','max_words':''},
    {'criterion':'Flow','description':'Order: Salutation -> Basic details -> Additional -> Closing','keywords':'','weight':'5','min_words':'0','max_words':''},
    {'criterion':'Speech Rate','description':'Words per minute evaluation','keywords':'','weight':'10','min_words':'0','max_words':''},
    {'criterion':'Grammar','description':'Grammar errors count based score','keywords':'','weight':'10','min_words':'0','max_words':''},
    {'criterion':'Vocabulary','description':'Vocabulary richness (TTR)','keywords':'','weight':'10','min_words':'0','max_words':''},
    {'criterion':'Filler Words','description':'Filler word rate','keywords':'um;uh;like;you know;so;actually;basically;right;i mean;well;kinda;sort of;okay;hmm;ah','weight':'15','min_words':'0','max_words':''},
    {'criterion':'Engagement/Sentiment','description':'Positive/enthusiastic sentiment','keywords':'','weight':'15','min_words':'0','max_words':''},
]

with dst.open('w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['criterion','description','keywords','weight','min_words','max_words'])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

print("Created rubrics.csv")
