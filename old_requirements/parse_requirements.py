#!/usr/bin/env python3
"""
Parse software design requirements from README files and generate readme.json
"""

import json
import re
from pathlib import Path

# File paths
FILES = {
    "Agent": "/Users/sahil/Desktop/eclipse/eclipse-ankaios/agent/doc/swdesign/README.md",
    "Ank": "/Users/sahil/Desktop/eclipse/eclipse-ankaios/ank/doc/swdesign/README.md",
    "Server": "/Users/sahil/Desktop/eclipse/eclipse-ankaios/server/doc/swdesign/README.md",
    "Common": "/Users/sahil/Desktop/eclipse/eclipse-ankaios/common/doc/swdesign/README.md",
    "gRPC": "/Users/sahil/Desktop/eclipse/eclipse-ankaios/grpc/doc/swdesign/README.md",
}

OUTPUT_FILE = "/Users/sahil/Desktop/eclipse/eclipse-ankaios/old_requirements/readme.json"


def clean_title(text):
    """Clean up requirement title."""
    # Remove markdown heading markers
    text = re.sub(r'^#{1,6}\s+', '', text)
    # Strip whitespace
    text = text.strip()
    return text


def extract_requirements(file_path, component):
    """Extract all requirements from a README file."""
    requirements = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for requirement tag pattern
        match = re.search(r'`swdd~([^~]+)~(\d+)`', line)

        if match:
            req_name = match.group(1)
            req_version = match.group(2)

            # Get title from previous non-empty line (before the tag)
            title = None
            j = i - 1
            while j >= 0:
                prev_line = lines[j].strip()
                if prev_line and not prev_line.startswith('####') and prev_line != '':
                    # Check if this is a heading
                    if prev_line.startswith('#'):
                        title = clean_title(prev_line)
                        break
                    # Skip if it's part of a list or table
                    elif not prev_line.startswith('-') and not prev_line.startswith('|') and not prev_line.startswith('*'):
                        # This might be descriptive text, keep looking for heading
                        pass
                j -= 1

            # If no title found, generate from requirement name
            if not title:
                title = req_name.replace('-', ' ').title()

            # Extract description - look for the first substantive paragraph after "Status: approved"
            description_lines = []
            k = i + 1
            found_status = False
            in_description = False

            while k < len(lines):
                desc_line = lines[k].strip()

                # Look for Status line
                if desc_line.startswith('Status:'):
                    found_status = True
                    k += 1
                    continue

                # Skip empty lines until we've found status
                if not found_status or (not desc_line and not in_description):
                    k += 1
                    continue

                # Start collecting after status
                if found_status and desc_line:
                    # Stop at Tags, Needs, Comment, Rationale, next heading, or next requirement
                    if (desc_line.startswith('Tags:') or
                        desc_line.startswith('Needs:') or
                        desc_line.startswith('Comment:') or
                        desc_line.startswith('Rationale:') or
                        desc_line.startswith('Assumptions:') or
                        desc_line.startswith('Considered alternatives:') or
                        desc_line.startswith('#') or
                        '`swdd~' in desc_line):
                        break

                    in_description = True
                    description_lines.append(desc_line)

                # Stop after collecting enough
                if in_description and len(description_lines) >= 2:
                    break

                # Stop at empty line after starting description
                if in_description and not desc_line:
                    break

                k += 1

            # Join description lines
            description = ' '.join(description_lines) if description_lines else title

            # Truncate if too long
            if len(description) > 250:
                description = description[:247] + "..."

            requirements.append({
                'component': component,
                'name': req_name,
                'version': req_version,
                'title': title,
                'description': description
            })

        i += 1

    return requirements


def generate_json(all_requirements):
    """Generate the final JSON structure."""
    issues = []

    for idx, req in enumerate(all_requirements, start=1):
        issue_key = f"REQ-D-{req['component']}-{idx:03d}"

        issue = {
            "id": str(idx),
            "key": issue_key,
            "fields": {
                "summary": req['title'],
                "issuetype": {
                    "id": str(idx),
                    "description": "Software design requirement",
                    "name": "Design Requirement"
                },
                "status": {
                    "id": "approved",
                    "name": "Approved"
                },
                "assignee": {
                    "displayName": "Unassigned",
                    "accountId": "unassigned"
                },
                "reporter": {
                    "displayName": "System",
                    "accountId": "system"
                },
                "description": req['description'],
                "verifiableByCodeOnly": True
            }
        }
        issues.append(issue)

    total_count = len(issues)

    output = {
        "expand": "schema,names",
        "startAt": 0,
        "maxResults": total_count,
        "total": total_count,
        "issues": issues
    }

    return output


def main():
    """Main execution function."""
    all_requirements = []

    # Extract requirements from each file
    for component, file_path in FILES.items():
        print(f"Processing {component} from {file_path}...")
        reqs = extract_requirements(file_path, component)
        all_requirements.extend(reqs)
        print(f"  Found {len(reqs)} requirements")

    print(f"\nTotal requirements found: {len(all_requirements)}")

    # Generate JSON
    output_data = generate_json(all_requirements)

    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nGenerated {OUTPUT_FILE} with {len(output_data['issues'])} requirements")


if __name__ == "__main__":
    main()
