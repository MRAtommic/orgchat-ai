import re

def escape_latex(text):
    if not text:
        return ""
    replacements = [
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
    ]
    res = text
    for char, rep in replacements:
        res = res.replace(char, rep)
    return res

def clean_caption(caption):
    if not caption:
        return ""
    # Strip leading "ตารางที่ X - Y", "ภาพที่ X - Y", "ตารางที่ X.Y", "ภาพที่ X.Y", etc.
    c = re.sub(r'^(ตารางที่|ภาพที่)\s*\d+[\s\-\.]+\d*\s*', '', caption.strip())
    # Strip leading/trailing \fontSixTeen or font sizes
    c = re.sub(r'\\fontSixTeen\s*', '', c).strip()
    return c

def format_table_tabularx(headers, rows, caption, label, col_spec=None):
    num_cols = len(headers)
    cleaned_caption = clean_caption(caption)
    
    if not col_spec:
        # Default: first col c, rest L (RaggedRight) to prevent stretched Thai text
        if num_cols == 2:
            col_spec = "| c | L |"
        elif num_cols == 3:
            col_spec = "| c | L | c |"
        elif num_cols == 4:
            col_spec = "| c | L | c | c |"
        elif num_cols == 5:
            col_spec = "| c | L | c | c | L |"
        elif num_cols == 6:
            col_spec = "| c | L | c | c | c | c |"
        elif num_cols == 7:
            col_spec = "| c | L | c | c | c | c | c |"
        else:
            col_spec = "| " + " | ".join(["c"] + ["L"] * (num_cols - 1)) + " |"

    escaped_headers = [f"\\textbf{{{escape_latex(h)}}}" for h in headers]
    header_line = " & ".join(escaped_headers) + r" \\ \hline"

    body_lines = []
    for row in rows:
        escaped_cells = [escape_latex(c).replace('\n', r'\\ ') for c in row]
        while len(escaped_cells) < num_cols:
            escaped_cells.append("")
        body_lines.append(" & ".join(escaped_cells[:num_cols]) + r" \\ \hline")

    table_tex = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{{escape_latex(cleaned_caption)}}}
\\label{{{label}}}
\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}
\\hline
{header_line}
""" + "\n".join(body_lines) + f"""
\\end{{tabularx}}
\\end{{table}}
"""
    return table_tex
