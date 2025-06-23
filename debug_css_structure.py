#!/usr/bin/env python3
"""
CSS Debug Script - Check HTML structure and CSS classes
This script helps identify differences in CSS classes and flex properties
between pages that work correctly and those that don't.
"""

import re

def analyze_template_structure(template_path, template_name):
    """Analyze the template structure for CSS classes and layout patterns."""
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        print(f"\n=== ANALYZING {template_name.upper()} ===")
        
        # Check for block content structure
        content_block = re.search(r'{% block content %}(.*?){% endblock %}', content, re.DOTALL)
        if content_block:
            block_content = content_block.group(1).strip()
            
            # Check for various container patterns
            patterns_to_check = [
                (r'<div class="row">', "Bootstrap row wrapper"),
                (r'<div class="col-\d+">', "Bootstrap column wrapper"),
                (r'<div class="container-fluid">', "Container-fluid wrapper"),
                (r'<div class="card">', "Direct card element"),
                (r'<div class="[^"]*d-flex[^"]*">', "D-flex classes"),
                (r'class="[^"]*"', "All CSS classes")
            ]
            
            for pattern, description in patterns_to_check:
                matches = re.findall(pattern, block_content)
                if matches:
                    print(f"  {description}: {len(matches)} found")
                    if "All CSS classes" in description:
                        # Show first few class definitions
                        for i, match in enumerate(matches[:3]):
                            print(f"    {i+1}. {match}")
                        if len(matches) > 3:
                            print(f"    ... and {len(matches) - 3} more")
                else:
                    print(f"  {description}: None found")
            
            # Check the first few lines of content block
            first_lines = '\n'.join(block_content.split('\n')[:5])
            print(f"  First content structure:\n{first_lines}")
        else:
            print("  No content block found")
            
    except Exception as e:
        print(f"  Error analyzing {template_name}: {e}")

# Templates to analyze
templates_to_check = [
    ("templates/dashboard.html", "dashboard"),
    ("templates/machines.html", "machines"),
    ("templates/maintenance.html", "maintenance"),
    ("templates/parts.html", "parts"),
    ("templates/audits.html", "audits"),
    ("templates/audit_history.html", "audit_history"),
    ("templates/sites.html", "sites"),
    ("templates/admin.html", "admin"),
    ("templates/user_profile.html", "user_profile")
]

print("HTML STRUCTURE ANALYSIS")
print("=" * 50)

for template_path, template_name in templates_to_check:
    analyze_template_structure(template_path, template_name)

print("\n" + "=" * 50)
print("ANALYSIS COMPLETE")
