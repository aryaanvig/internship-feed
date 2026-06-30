#!/usr/bin/env python3
"""
Internship feed compiler for Aryan Vig.
Pulls live internship postings from public GitHub trackers, filters to YOUR
target companies (targets.txt), and writes output/internships.csv + .html.
Pure standard library: no pip installs needed. Runs anywhere Python 3.8+ exists.
"""
import urllib.request, re, csv, html, sys, datetime, os

# Raw README files of the public trackers. Add/replace as repos change each cycle.
# When you apply in fall 2027, bump the year in these URLs to the then-current cycle.
SOURCES = [
    ("AI/ML (SpeedyApply)",
     "https://raw.githubusercontent.com/speedyapply/2026-AI-College-Jobs/main/README.md"),
    ("SWE (SpeedyApply)",
     "https://raw.githubusercontent.com/speedyapply/2026-SWE-College-Jobs/main/README.md"),
    ("All Internships (Simplify)",
     "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/README.md"),
]

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)


def load_targets():
    """Return list of (term, compiled_matcher). Short terms (<=4 chars) require a
    word boundary so 'xai' matches the company xAI but not 'Xaira'."""
    path = os.path.join(HERE, "targets.txt")
    terms = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                t = line.lower()
                if len(t) <= 4:
                    terms.append(("re", re.compile(r'\b' + re.escape(t) + r'\b')))
                else:
                    terms.append(("in", t))
    return terms


def matches(company_lower, targets):
    for kind, t in targets:
        if kind == "in" and t in company_lower:
            return True
        if kind == "re" and t.search(company_lower):
            return True
    return False


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (internship-feed)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def strip_md(cell):
    """Turn a markdown/HTML table cell into (text, first_link)."""
    link = ""
    m = re.search(r'\[([^\]]*)\]\(([^)]+)\)', cell)          # [text](url)
    if m:
        link = m.group(2)
    m2 = re.search(r'href=["\']([^"\']+)["\']', cell)         # <a href="url">
    if m2 and not link:
        link = m2.group(1)
    text = re.sub(r'<[^>]+>', ' ', cell)                      # drop html tags
    text = re.sub(r'\[([^\]]*)\]\([^)]+\)', r'\1', text)      # [text](url) -> text
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r'[🔒🛂✅�: ]{2,}', ' ', text)
    return text.strip(" |"), link.strip()


def parse_tables(md):
    """Yield dict rows from every markdown table, keyed by lowercased header name."""
    lines = md.splitlines()
    i = 0
    last_company = ""
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r'^\s*\|?[\s:|-]+\|?\s*$', lines[i+1]):
            headers = [h.strip().lower() for h in line.strip().strip("|").split("|")]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = lines[i].strip().strip("|").split("|")
                if len(cells) >= len(headers):
                    row = {}
                    for h, c in zip(headers, cells):
                        txt, lnk = strip_md(c)
                        row[h] = txt
                        if lnk and "link" not in row:
                            row["_link"] = lnk
                    yield row, last_company
                    comp = row.get("company", "")
                    if comp and comp not in ("↳", "->", ""):
                        last_company = comp
                i += 1
        else:
            i += 1


def col(row, *names):
    for n in names:
        for k in row:
            if n in k:
                return row[k]
    return ""


def main():
    targets = load_targets()
    seen = set()
    results = []
    errors = []

    for label, url in SOURCES:
        try:
            md = fetch(url)
        except Exception as e:
            errors.append(f"{label}: {e}")
            continue
        for row, carry in parse_tables(md):
            company = col(row, "company") or carry
            if company in ("↳", "->", ""):
                company = carry
            role = col(row, "role", "position", "title")
            location = col(row, "location", "locations")
            date = col(row, "date", "age", "posted")
            link = row.get("_link", "")
            cl = company.lower()
            if not matches(cl, targets):
                continue
            if "🔒" in (company + role) or "closed" in role.lower():
                continue  # skip closed roles
            key = (company.lower(), role.lower(), location.lower())
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "Company": company, "Role": role, "Location": location,
                "Posted": date, "Apply": link, "Source": label,
            })

    results.sort(key=lambda r: (r["Company"].lower(), r["Role"].lower()))
    write_csv(results)
    write_html(results, errors)
    print(f"Wrote {len(results)} matching open postings across {len(targets)} target terms.")
    if errors:
        print("Source warnings:", "; ".join(errors))


def write_csv(rows):
    with open(os.path.join(OUT, "internships.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Company", "Role", "Location", "Posted", "Apply", "Source"])
        w.writeheader()
        w.writerows(rows)


def write_html(rows, errors):
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    trs = ""
    for r in rows:
        apply = f'<a href="{html.escape(r["Apply"])}" target="_blank">Apply</a>' if r["Apply"] else ""
        trs += ("<tr>"
                f'<td class="co">{html.escape(r["Company"])}</td>'
                f'<td>{html.escape(r["Role"])}</td>'
                f'<td>{html.escape(r["Location"])}</td>'
                f'<td>{html.escape(r["Posted"])}</td>'
                f'<td>{apply}</td>'
                f'<td class="src">{html.escape(r["Source"])}</td>'
                "</tr>\n")
    warn = ""
    if errors:
        warn = '<div class="warn">Some sources did not load (the others still worked): ' + html.escape("; ".join(errors)) + "</div>"
    empty = "" if rows else '<div class="warn">No matching open postings right now. Most of your targets only appear when they open applications (typically fall for the next summer). Check back, or open the source repos directly.</div>'
    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>My Open Internship Targets</title>
<style>
:root{{--navy:#122E5C;--maroon:#8C202C;--pale:#E8EEF7;--line:#dde3ec;}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,Segoe UI,Arial,sans-serif;background:#F7F9FC;color:#1f2430;padding:0 0 60px}}
header{{background:var(--navy);color:#fff;padding:20px 28px}}
header h1{{font-size:20px}} header p{{opacity:.85;font-size:13px;margin-top:4px}}
.meta{{padding:10px 28px;font-size:12px;color:#6B7280}}
.wrap{{padding:8px 28px}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
th{{background:var(--navy);color:#fff;font-size:11px;text-transform:uppercase;letter-spacing:.4px;padding:11px 10px;text-align:left}}
td{{padding:9px 10px;font-size:13px;border-bottom:1px solid var(--line);vertical-align:top}}
tr:hover td{{background:#fafbfe}}
.co{{font-weight:700;color:var(--navy)}}
.src{{color:#6B7280;font-size:11px}}
a{{color:var(--maroon);font-weight:600}}
.warn{{background:#FFF8E1;border-left:4px solid var(--maroon);padding:11px 16px;margin:14px 28px;border-radius:4px;font-size:13px}}
.count{{display:inline-block;background:var(--pale);color:var(--navy);padding:3px 10px;border-radius:20px;font-weight:600;font-size:12px}}
</style></head><body>
<header><h1>My Open Internship Targets</h1>
<p>Auto-compiled from public trackers, filtered to your target companies. Updates daily.</p></header>
<div class="meta">Last updated: {now} &nbsp;|&nbsp; <span class="count">{len(rows)} open postings</span></div>
{warn}{empty}
<div class="wrap"><table><thead><tr>
<th>Company</th><th>Role</th><th>Location</th><th>Posted</th><th>Link</th><th>Source</th>
</tr></thead><tbody>
{trs}
</tbody></table></div></body></html>"""
    with open(os.path.join(OUT, "internships.html"), "w", encoding="utf-8") as f:
        f.write(doc)


if __name__ == "__main__":
    main()
