from html.parser import HTMLParser

class DOMPathFinder(HTMLParser):
    def __init__(self, target_id):
        super().__init__()
        self.target_id = target_id
        self.stack = []
        self.found_path = None

    def handle_starttag(self, tag, attrs):
        # Keep track of class and id
        attrs_dict = dict(attrs)
        tag_id = attrs_dict.get('id')
        tag_class = attrs_dict.get('class')
        
        node_info = {
            'tag': tag,
            'id': tag_id,
            'class': tag_class
        }
        self.stack.append(node_info)
        
        if tag_id == self.target_id:
            self.found_path = list(self.stack)

    def handle_endtag(self, tag):
        # We need to pop from stack
        # To handle mismatching tags cleanly, we pop if it matches the last tag, otherwise we pop carefully
        if self.stack:
            # Simple popping
            self.stack.pop()

# Let's run this for both editExpenseModal and navSidebar
with open(r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\templates\index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

for target in ['editExpenseModal', 'moveModal', 'navSidebar']:
    parser = DOMPathFinder(target)
    parser.feed(html_content)
    print(f"\n--- Path to #{target} ---")
    if parser.found_path:
        for idx, node in enumerate(parser.found_path):
            id_str = f" id='{node['id']}'" if node['id'] else ""
            class_str = f" class='{node['class']}'" if node['class'] else ""
            print(f"{'  ' * idx}<{node['tag']}{id_str}{class_str}>")
    else:
        print("Not found or parser error")
