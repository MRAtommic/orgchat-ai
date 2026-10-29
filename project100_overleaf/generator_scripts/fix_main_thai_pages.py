# -*- coding: utf-8 -*-
import os

def fix_main_tex(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add full Thai alphabet definition in preamble
    thai_counter_def = r"""% Define full Thai alphabet for page numbering beyond 10
\makeatletter
\def\@thaialph#1{%
  \ifcase#1\or ก\or ข\or ค\or ง\or จ\or ฉ\or ช\or ซ\or ฌ\or ญ\or ฎ\or ฏ\or ฐ\or ฑ\or ฒ\or ณ\or ด\or ต\or ถ\or ท\or ธ\or น\or บ\or ป\or ผ\or ฝ\or พ\or ฟ\or ภ\or ม\or ย\or ร\or ล\or ว\or ศ\or ษ\or ส\or ห\or ฬ\or อ\or ฮ\else ?\fi
}
\def\thaialph#1{\expandafter\@thaialph\csname c@#1\endcsname}
\def\thaiAlph#1{\expandafter\@thaialph\csname c@#1\endcsname}
\makeatother
"""
    if "@thaialph" not in content:
        content = content.replace(r"\begin{document}", thai_counter_def + "\n" + r"\begin{document}")

    # 2. Compress \customLOTthai slightly so it fits in 2 pages if possible
    lot_target = r"\customLOTthai"
    lot_replacement = r"""\begingroup
    \linespread{0.93}\selectfont
    \customLOTthai
    \endgroup"""
    if r"\linespread{0.93}\selectfont" not in content:
        content = content.replace(lot_target, lot_replacement)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

fix_main_tex(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OrgChat_Overleaf_Updated\Main.tex')
fix_main_tex(r'c:\Users\FEWIT\Desktop\orgchat-ai-main\webai\เอกสาร โปรจบ\OVERLEFT\Main.tex')

print("Main.tex updated with full Thai page counter and compressed LOT!")
