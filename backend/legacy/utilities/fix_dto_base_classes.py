#!/usr/bin/env python3
"""
Fix all DTOs to not inherit from Request/Response base classes.

Since the base classes are no longer dataclasses, we need to include
the base fields directly in each DTO.
"""

import os
import re
from pathlib import Path

def fix_request_class(content, class_name):
    """Fix a Request class to include base fields."""
    # Find the class definition
    pattern = rf'(@dataclass\s*\nclass {class_name}\(Request\):.*?)\n([ ]+)(\w+:.*?)(?=\n\n|\Z)'
    
    def replacer(match):
        header = match.group(1).replace('(Request):', ':')
        indent = match.group(2)
        fields = match.group(3)
        
        # Add base Request fields at the end
        base_fields = f"""{indent}# Base Request fields
{indent}request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
{indent}timestamp: datetime = field(default_factory=datetime.utcnow)
{indent}user_id: Optional[str] = None
{indent}correlation_id: Optional[str] = None"""
        
        return f"{header}\n{indent}{fields}\n{indent}\n{base_fields}"
    
    return re.sub(pattern, replacer, content, flags=re.DOTALL)

def fix_response_class(content, class_name):
    """Fix a Response class to include base fields and methods."""
    # This is more complex since Response classes already exist
    # For now, just log them
    print(f"  Found Response class: {class_name}")
    return content

def fix_dto_file(filepath):
    """Fix a single DTO file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Find all Request classes
    request_pattern = r'@dataclass\s*\nclass\s+(\w+Request)\(Request\):'
    for match in re.finditer(request_pattern, content):
        class_name = match.group(1)
        print(f"  Fixing Request class: {class_name}")
        content = fix_request_class(content, class_name)
    
    # Find all Response classes that inherit from Response
    response_pattern = r'@dataclass\s*\nclass\s+(\w+Response)\(Response\):'
    for match in re.finditer(response_pattern, content):
        class_name = match.group(1)
        content = fix_response_class(content, class_name)
    
    # Add imports if needed
    if 'uuid' in content and 'import uuid' not in content:
        # Add uuid import after other imports
        content = re.sub(
            r'(from typing import.*?\n)',
            r'\1import uuid\n',
            content
        )
    
    if content != original_content:
        print(f"  -> Would update {filepath}")
        # Uncomment to actually write:
        # with open(filepath, 'w') as f:
        #     f.write(content)
        return True
    return False

def main():
    """Main function."""
    dto_dir = Path("application/dto")
    
    if not dto_dir.exists():
        print(f"Directory {dto_dir} does not exist!")
        return
    
    # Find all Python files in dto directory
    dto_files = list(dto_dir.glob("*.py"))
    
    files_to_fix = []
    
    for filepath in dto_files:
        if filepath.name in ["__init__.py", "base.py"]:
            continue
        
        print(f"\nChecking {filepath.name}:")
        if fix_dto_file(filepath):
            files_to_fix.append(filepath)
    
    print(f"\nSummary:")
    print(f"Files that need fixing: {len(files_to_fix)}")

if __name__ == "__main__":
    main()