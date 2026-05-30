from bs4 import BeautifulSoup

html_path = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\templates\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

soup = BeautifulSoup(content, 'html.parser')

panels = soup.find_all(id="chatSidebarPanel")
print(f"Found {len(panels)} elements with id='chatSidebarPanel'")
for idx, p in enumerate(panels):
    print(f"  {idx}: tag=<{p.name}>, parent=<{p.parent.name}> (parent id={p.parent.get('id')}), classes={p.get('class')}")

main_areas = soup.find_all(id="chatMainArea")
print(f"Found {len(main_areas)} elements with id='chatMainArea'")
for idx, m in enumerate(main_areas):
    print(f"  {idx}: tag=<{m.name}>, parent=<{m.parent.name}> (parent id={m.parent.get('id')}), classes={m.get('class')}")
