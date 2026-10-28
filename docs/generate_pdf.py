"""
PlantScan AI - PDF Generator for Master Guide
Converts docs/PlantScanAI_FINAL_DEMO_AND_VIVA_MASTER_GUIDE.md into a high-quality,
professionally styled PDF using MarkdownIt and Chrome/Edge headless printing.
"""

import os
import re
import subprocess
from pathlib import Path
from markdown_it import MarkdownIt

def build_pdf():
    docs_dir = Path(__file__).resolve().parent
    md_path = docs_dir / "PlantScanAI_FINAL_DEMO_AND_VIVA_MASTER_GUIDE.md"
    html_path = docs_dir / "PlantScanAI_FINAL_DEMO_AND_VIVA_MASTER_GUIDE.html"
    pdf_path = docs_dir / "PlantScanAI_FINAL_DEMO_AND_VIVA_MASTER_GUIDE.pdf"

    if not md_path.exists():
        raise FileNotFoundError(f"Markdown source not found: {md_path}")

    raw_md = md_path.read_text(encoding="utf-8")

    # 1. Pre-process GitHub-style alerts:
    # > [!NOTE], > [!IMPORTANT], > [!WARNING], > [!TIP], > [!CAUTION]
    alert_patterns = [
        (r"(?m)^> \[!NOTE\]\s*\n((?:> .*\n?)+)", r'<div class="callout callout-note"><div class="callout-title">NOTE</div>\1</div>'),
        (r"(?m)^> \[!IMPORTANT\]\s*\n((?:> .*\n?)+)", r'<div class="callout callout-important"><div class="callout-title">IMPORTANT</div>\1</div>'),
        (r"(?m)^> \[!WARNING\]\s*\n((?:> .*\n?)+)", r'<div class="callout callout-warning"><div class="callout-title">WARNING</div>\1</div>'),
        (r"(?m)^> \[!TIP\]\s*\n((?:> .*\n?)+)", r'<div class="callout callout-tip"><div class="callout-title">TIP</div>\1</div>'),
        (r"(?m)^> \[!CAUTION\]\s*\n((?:> .*\n?)+)", r'<div class="callout callout-caution"><div class="callout-title">CAUTION</div>\1</div>'),
    ]

    processed_md = raw_md
    for pat, repl in alert_patterns:
        def alert_sub(match):
            text = match.group(0)
            lines = text.split("\n")
            title = lines[0].replace("> [!", "").replace("]", "").strip()
            content_lines = [l[2:] if l.startswith("> ") else (l[1:] if l.startswith(">") else l) for l in lines[1:]]
            content = "\n".join(content_lines).strip()
            cls_map = {
                "NOTE": "callout-note",
                "IMPORTANT": "callout-important",
                "WARNING": "callout-warning",
                "TIP": "callout-tip",
                "CAUTION": "callout-caution",
            }
            css_cls = cls_map.get(title.upper(), "callout-note")
            return f'\n\n<div class="callout {css_cls}"><div class="callout-title">{title}</div>\n\n{content}\n\n</div>\n\n'
        processed_md = re.sub(pat, alert_sub, processed_md)

    # 2. Pre-process evidence status badges:
    # `[VERIFIED]`, `[PARTIALLY VERIFIED]`, `[EXPERIMENTAL]`, `[PLANNED]`, `[UNKNOWN]`, `[RECOMMENDATION]`
    badge_replacements = [
        (r"`\[VERIFIED\]`|\[VERIFIED\]", '<span class="badge badge-verified">VERIFIED</span>'),
        (r"`\[PARTIALLY VERIFIED\]`|\[PARTIALLY VERIFIED\]", '<span class="badge badge-partial">PARTIALLY VERIFIED</span>'),
        (r"`\[EXPERIMENTAL\]`|\[EXPERIMENTAL\]", '<span class="badge badge-experimental">EXPERIMENTAL</span>'),
        (r"`\[PLANNED\]`|\[PLANNED\]", '<span class="badge badge-planned">PLANNED</span>'),
        (r"`\[UNKNOWN\]`|\[UNKNOWN\]", '<span class="badge badge-unknown">UNKNOWN</span>'),
        (r"`\[RECOMMENDATION\]`|\[RECOMMENDATION\]", '<span class="badge badge-recommendation">RECOMMENDATION</span>'),
    ]
    for pat, repl in badge_replacements:
        processed_md = re.sub(pat, repl, processed_md)

    # 3. Add explicit page breaks before top-level section headings
    processed_md = re.sub(
        r"(?m)^# (SECTION \d+: [^\n]+)",
        r'<div class="section-break"></div>\n\n# \1',
        processed_md
    )

    # 4. Render Markdown to HTML via MarkdownIt
    md = MarkdownIt("gfm-like", {"linkify": False, "html": True})
    content_html = md.render(processed_md)

    # 5. Build full HTML document with typography, styling, cover page, and print media rules
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>PlantScan AI: Final Demo & Viva Master Guide</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&family=Outfit:wght@500;600;700;800&family=Nirmala+UI:wght@400;700&display=swap');

@page {{
  size: A4;
  margin: 20mm 15mm 20mm 15mm;
  @bottom-right {{
    content: counter(page);
    font-family: 'Inter', sans-serif;
    font-size: 8pt;
    color: #666;
  }}
  @top-right {{
    content: "PlantScan AI — Technical Audit & Viva Master Guide";
    font-family: 'Inter', sans-serif;
    font-size: 8pt;
    color: #888;
  }}
}}

body {{
  font-family: 'Inter', 'Segoe UI', 'Nirmala UI', -apple-system, sans-serif;
  font-size: 9.5pt;
  line-height: 1.55;
  color: #1a1a1a;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
}}

/* Cover Page */
.cover-page {{
  page-break-after: always;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 90vh;
  padding: 20px 10px;
  border-bottom: 2px solid #2d6a4f;
}}

.institution-header {{
  text-align: center;
  border-bottom: 2px solid #1b4332;
  padding-bottom: 15px;
}}

.institution-name {{
  font-family: 'Outfit', sans-serif;
  font-size: 15pt;
  font-weight: 800;
  color: #1b4332;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-bottom: 4px;
}}

.institution-sub {{
  font-size: 10.5pt;
  font-weight: 700;
  color: #2d6a4f;
  margin-bottom: 6px;
}}

.institution-accreditation {{
  font-size: 7.5pt;
  color: #555;
  line-height: 1.35;
  max-width: 90%;
  margin: 0 auto;
}}

.dept-name {{
  margin-top: 10px;
  font-size: 11pt;
  font-weight: 700;
  color: #111;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}

.project-title-box {{
  text-align: center;
  margin: 40px 0;
  padding: 25px 20px;
  background: #f4fbf7;
  border-left: 6px solid #2d6a4f;
  border-radius: 4px;
}}

.project-badge-tag {{
  display: inline-block;
  background: #1b4332;
  color: #ffffff;
  font-family: 'Outfit', sans-serif;
  font-size: 8pt;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 12px;
}}

.project-main-title {{
  font-family: 'Outfit', sans-serif;
  font-size: 19pt;
  font-weight: 800;
  color: #1b4332;
  line-height: 1.25;
  margin: 0 0 12px 0;
}}

.project-subtitle {{
  font-size: 10.5pt;
  color: #333;
  line-height: 1.45;
  font-weight: 500;
}}

.meta-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 30px;
  font-size: 9pt;
  background: #fafafa;
  padding: 15px 20px;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}}

.meta-block strong {{
  color: #1b4332;
  display: block;
  font-size: 9pt;
  margin-bottom: 3px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}

.document-footer-meta {{
  text-align: center;
  font-size: 8pt;
  color: #666;
  border-top: 1px solid #ddd;
  padding-top: 10px;
  margin-top: 20px;
}}

/* Headings */
h1, h2, h3, h4 {{
  font-family: 'Outfit', 'Segoe UI', sans-serif;
  color: #1b4332;
  margin-top: 1.4em;
  margin-bottom: 0.5em;
  page-break-after: avoid;
}}

h1 {{
  font-size: 15pt;
  border-bottom: 2px solid #2d6a4f;
  padding-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}

h2 {{
  font-size: 12pt;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 3px;
}}

h3 {{
  font-size: 10.5pt;
  color: #2d6a4f;
}}

h4 {{
  font-size: 9.5pt;
  color: #333;
}}

.section-break {{
  page-break-before: always;
}}

/* Paragraphs & Lists */
p {{
  margin: 0.5em 0;
  text-align: justify;
}}

ul, ol {{
  margin: 0.5em 0;
  padding-left: 20px;
}}

li {{
  margin: 0.3em 0;
}}

/* Tables */
table {{
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 8pt;
  page-break-inside: avoid;
}}

th, td {{
  border: 1px solid #dcdcdc;
  padding: 5px 7px;
  text-align: left;
  vertical-align: top;
}}

th {{
  background-color: #1b4332;
  color: #ffffff;
  font-weight: 600;
  font-family: 'Outfit', sans-serif;
  letter-spacing: 0.3px;
}}

tr:nth-child(even) {{
  background-color: #f8faf8;
}}

/* Code Blocks & Monospace */
pre, code {{
  font-family: 'JetBrains Mono', 'Consolas', monospace;
}}

code {{
  font-size: 8pt;
  background-color: #f1f3f1;
  color: #1b4332;
  padding: 1px 4px;
  border-radius: 3px;
  border: 1px solid #e2e8e2;
}}

pre {{
  background-color: #0f1713;
  color: #e5f2eb;
  padding: 10px 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 7.5pt;
  line-height: 1.4;
  page-break-inside: avoid;
  border: 1px solid #2d6a4f;
}}

pre code {{
  background-color: transparent;
  color: inherit;
  padding: 0;
  border: none;
  font-size: inherit;
}}

/* Callouts / Alerts */
.callout {{
  margin: 1em 0;
  padding: 10px 14px;
  border-radius: 4px;
  page-break-inside: avoid;
  border-left: 4px solid;
}}

.callout-title {{
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  font-size: 8.5pt;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
  text-transform: uppercase;
}}

.callout-note {{
  background: #f0f7ff;
  border-color: #0066cc;
  color: #003366;
}}
.callout-note .callout-title {{ color: #0066cc; }}

.callout-important {{
  background: #f5f0ff;
  border-color: #7b2cbf;
  color: #3c096c;
}}
.callout-important .callout-title {{ color: #7b2cbf; }}

.callout-warning {{
  background: #fff8f0;
  border-color: #e65100;
  color: #662200;
}}
.callout-warning .callout-title {{ color: #e65100; }}

.callout-tip {{
  background: #f0fff4;
  border-color: #2d6a4f;
  color: #081c15;
}}
.callout-tip .callout-title {{ color: #2d6a4f; }}

.callout-caution {{
  background: #fff0f0;
  border-color: #d00000;
  color: #6a040f;
}}
.callout-caution .callout-title {{ color: #d00000; }}

/* Badges */
.badge {{
  display: inline-block;
  font-family: 'Outfit', sans-serif;
  font-size: 6.8pt;
  font-weight: 700;
  padding: 1.5px 6px;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  vertical-align: middle;
}}

.badge-verified {{
  background-color: #2d6a4f;
  color: #ffffff;
}}

.badge-partial {{
  background-color: #e67e22;
  color: #ffffff;
}}

.badge-experimental {{
  background-color: #8e44ad;
  color: #ffffff;
}}

.badge-planned {{
  background-color: #2980b9;
  color: #ffffff;
}}

.badge-unknown {{
  background-color: #7f8c8d;
  color: #ffffff;
}}

.badge-recommendation {{
  background-color: #16a085;
  color: #ffffff;
}}

blockquote {{
  border-left: 3px solid #2d6a4f;
  background-color: #f7faf8;
  margin: 0.8em 0;
  padding: 8px 14px;
  font-style: italic;
  color: #2c3e50;
  border-radius: 0 4px 4px 0;
}}

/* Print specific optimizations */
@media print {{
  body {{
    font-size: 8.8pt;
  }}
  a {{
    text-decoration: none;
    color: #1b4332;
  }}
  .section-break {{
    page-break-before: always;
  }}
}}
</style>
</head>
<body>

<!-- Formal Academic Cover Page -->
<div class="cover-page">
  <div class="institution-header">
    <div class="institution-name">National Education Society (R.)</div>
    <div class="institution-sub">J. N. N. College of Engineering, Shivamogga</div>
    <div class="institution-accreditation">
      Approved by AICTE, New Delhi &bull; Certified by UGC 2f & 12B &bull; Accredited by NAAC – 'A'<br>
      All 7 UG Programs Accredited by National Board of Accreditation (NBA)<br>
      Recognized by Govt. of Karnataka &bull; Affiliated to Visvesvaraya Technological University (VTU), Belagavi
    </div>
    <div class="dept-name">Department of Computer Science and Engineering</div>
  </div>

  <div class="project-title-box">
    <span class="project-badge-tag">B.E. Final-Year Major Project (Phase III)</span>
    <h1 class="project-main-title">PlantScan AI</h1>
    <div class="project-subtitle">
      <strong>Multi-Crop Disease Diagnosis and Multilingual Integrated Pest Management (IPM) Advisory System using Deep Learning & Mobile-Cloud Architecture</strong>
    </div>
  </div>

  <div class="meta-grid">
    <div class="meta-block">
      <strong>Candidate / Presenter</strong>
      <span>Sagar Nag (USN: <code>4JN22CS___</code>)</span><br>
      <span>Final Year B.E., Batch-12 (CSE-Phase III)</span>
    </div>
    <div class="meta-block">
      <strong>Development Team</strong>
      <span>Batch-12 Project Team</span><br>
      <span>Git: <code>Sagarnag774</code>, <code>divakar-c-25</code></span>
    </div>
    <div class="meta-block">
      <strong>Project Guide</strong>
      <span>Department of Computer Science & Engineering</span><br>
      <span>J.N.N. College of Engineering, Shivamogga</span>
    </div>
    <div class="meta-block">
      <strong>Document Scope & Standard</strong>
      <span>Repository-Grounded Technical Audit</span><br>
      <span>Full System Reconstruction & Viva Master Guide</span>
    </div>
  </div>

  <div class="document-footer-meta">
    <span>Academic Year: 2025 – 2026 &bull; Examination Date: October 2026 &bull; Location: Shivamogga, Karnataka, India</span>
  </div>
</div>

<!-- Main Body Content -->
{content_html}

</body>
</html>
"""

    html_path.write_text(full_html, encoding="utf-8")
    print(f"[OK] Generated styled HTML at {html_path} ({len(full_html)} chars)")

    # 6. Locate Chrome or Edge executable
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    browser_exe = None
    for cp in chrome_paths:
        if Path(cp).exists():
            browser_exe = cp
            break

    if not browser_exe:
        raise RuntimeError("Neither Chrome nor Edge was found at standard Windows paths.")

    print(f"[INFO] Using browser engine: {browser_exe}")

    # 7. Convert HTML to PDF using Headless Chrome/Edge
    cmd = [
        browser_exe,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={pdf_path.resolve()}",
        str(html_path.resolve())
    ]

    print(f"[INFO] Executing PDF rendering command...")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        print(f"[ERROR] PDF generation failed: {res.stderr}")
        return False

    if pdf_path.exists():
        size_kb = pdf_path.stat().st_size / 1024
        print(f"[SUCCESS] PDF generated successfully: {pdf_path} ({size_kb:.1f} KB)")
        return True
    else:
        print("[ERROR] PDF file was not created.")
        return False

if __name__ == "__main__":
    build_pdf()
