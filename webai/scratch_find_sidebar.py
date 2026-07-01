with open('templates/index.html', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if 'showView(\'admin\')' in line or 'showView("admin")' in line or 'view-admin' in line or 'แดชบอร์ด' in line or 'แผงควบคุม' in line or 'admin_required' in line or 'org_role' in line:
            print(f"{idx}: {line.strip()[:150]}")
