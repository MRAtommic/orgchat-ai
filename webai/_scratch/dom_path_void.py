from html.parser import HTMLParser

class DOMPathFinder(HTMLParser):
    # List of HTML5 void elements that do not have closing tags
    VOID_ELEMENTS = {
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr'
    }

    def __init__(self, target_id):
        super().__init__()
        self.target_id = target_id
        self.stack = []
        self.found_path = None

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        
        attrs_dict = dict(attrs)
        tag_id = attrs_dict.get('id')
        tag_class = attrs_dict.get('class')
        
        node_info = {
            'tag': tag_lower,
            'id': tag_id,
            'class': tag_class
        }
        
        self.stack.append(node_info)
        
        if tag_id == self.target_id:
            self.found_path = list(self.stack)
            
        # If it's a void element, we pop it immediately because it cannot have children
        if tag_lower in self.VOID_ELEMENTS:
            self.stack.pop()

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.VOID_ELEMENTS:
            return # Already popped or ignored
            
        # Pop until we find the matching start tag
        while self.stack:
            popped = self.stack.pop()
            if popped['tag'] == tag_lower:
                break

# Let's run this for target modals and components
with open(r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\templates\index.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

for target in ['editExpenseModal', 'moveModal', 'mediaSidebar', 'navSidebar']:
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
