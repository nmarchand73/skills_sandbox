"""Parse SKILL.md files and extract metadata."""
import yaml
import re
from pathlib import Path
from typing import Dict, Any
from logger_config import get_logger

logger = get_logger(__name__)


def parse_skill_md(skill_path: Path) -> Dict[str, Any]:
    """Parse a SKILL.md file and extract frontmatter and content."""
    skill_file = skill_path / "SKILL.md"
    
    if not skill_file.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_path}")
    
    content = skill_file.read_text(encoding="utf-8")
    
    # Extract YAML frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    
    if not frontmatter_match:
        raise ValueError("SKILL.md must have YAML frontmatter")
    
    frontmatter_str, body = frontmatter_match.groups()
    frontmatter = yaml.safe_load(frontmatter_str)
    
    return {
        "metadata": frontmatter,
        "content": body,
        "skill_path": skill_path
    }


def extract_agent_config(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract CrewAI agent configuration from skill data."""
    metadata = skill_data["metadata"]
    content = skill_data["content"]
    
    # Extract role from name or description
    name = metadata.get("name", "skill")
    description = metadata.get("description", "")
    
    # Create role from name (convert kebab-case to title)
    role = name.replace("-", " ").title()
    
    # Goal is the description
    goal = description
    
    # Backstory combines description and key content sections
    backstory_parts = [description]
    
    # Extract key sections from content
    quick_start_match = re.search(r'## Quick Start\n\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
    if quick_start_match:
        backstory_parts.append(f"Quick Start: {quick_start_match.group(1)[:200]}")
    
    backstory = "\n\n".join(backstory_parts)
    
    return {
        "role": role,
        "goal": goal,
        "backstory": backstory,
        "name": name,
        "description": description
    }

