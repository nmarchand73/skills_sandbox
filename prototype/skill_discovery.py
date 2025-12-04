"""Discover and select skills based on tasks."""
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from skill_parser import parse_skill_md, extract_agent_config
from logger_config import get_logger
import re

logger = get_logger(__name__)


def discover_skills(skills_dir: Path) -> List[Dict[str, Any]]:
    """Discover all skills in a directory."""
    skills = []
    
    if not skills_dir.exists():
        return skills
    
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                try:
                    skill_data = parse_skill_md(skill_dir)
                    agent_config = extract_agent_config(skill_data)
                    
                    # Get skill structure
                    scripts = []
                    scripts_dir = skill_dir / "scripts"
                    if scripts_dir.exists():
                        scripts = [f.name for f in scripts_dir.iterdir() 
                                 if f.is_file() and f.suffix == '.py']
                    
                    references = []
                    ref_dir = skill_dir / "references"
                    if ref_dir.exists():
                        references = [f.name for f in ref_dir.iterdir() if f.is_file()]
                    
                    # Note PDF files in references
                    pdf_files = [f.name for f in ref_dir.iterdir() if f.is_file() and f.suffix.lower() == '.pdf'] if ref_dir.exists() else []
                    
                    skills.append({
                        "path": skill_dir,
                        "name": agent_config["name"],
                        "description": agent_config["description"],
                        "role": agent_config["role"],
                        "goal": agent_config["goal"],
                        "backstory": agent_config["backstory"],
                        "scripts": scripts,
                        "references": references,
                        "pdf_files": pdf_files,
                        "metadata": skill_data["metadata"],
                        "content": skill_data["content"]
                    })
                except Exception as e:
                    logger.warning(f"Could not parse skill {skill_dir.name}: {e}")
                    continue
    
    return skills


def score_skill_relevance(skill: Dict[str, Any], task: str) -> float:
    """Score how relevant a skill is to a task."""
    score = 0.0
    task_lower = task.lower()
    
    # Check description match
    description = skill.get("description", "").lower()
    if description:
        # Count keyword matches
        task_words = set(re.findall(r'\b\w+\b', task_lower))
        desc_words = set(re.findall(r'\b\w+\b', description))
        common_words = task_words.intersection(desc_words)
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
        common_words = common_words - stop_words
        score += len(common_words) * 2.0
    
    # Check name match
    name = skill.get("name", "").lower()
    if any(word in name for word in task_lower.split() if len(word) > 3):
        score += 5.0
    
    # Check goal match
    goal = skill.get("goal", "").lower()
    if goal:
        goal_words = set(re.findall(r'\b\w+\b', goal))
        common_words = task_words.intersection(goal_words) - stop_words
        score += len(common_words) * 1.5
    
    # Extract important keywords from skill description and name dynamically
    # Look for significant words (3+ chars) in skill name and description
    skill_text = f"{name} {description} {goal}".lower()
    skill_keywords = set(re.findall(r'\b\w{4,}\b', skill_text)) - stop_words
    
    # Boost score if task mentions skill-specific keywords
    task_keywords = set(re.findall(r'\b\w{4,}\b', task_lower)) - stop_words
    matching_keywords = task_keywords.intersection(skill_keywords)
    if matching_keywords:
        score += len(matching_keywords) * 1.0
    
    return score


def select_best_skill(skills: List[Dict[str, Any]], task: str) -> Optional[Dict[str, Any]]:
    """Select the best skill for a given task."""
    if not skills:
        return None
    
    # Score all skills
    scored_skills = [(skill, score_skill_relevance(skill, task)) for skill in skills]
    scored_skills.sort(key=lambda x: x[1], reverse=True)
    
    # Return the best match
    best_skill, best_score = scored_skills[0]
    
    # Only return if score is above threshold
    if best_score > 0:
        return best_skill
    
    return None


def should_chain_skills(scored_skills: List[Tuple[Dict[str, Any], float]], task: str) -> bool:
    """Determine if skills should be chained based on task and scores."""
    if len(scored_skills) < 2:
        return False
    
    best_skill, best_score = scored_skills[0]
    second_skill, second_score = scored_skills[1]
    
    # Don't chain if best score is too low
    if best_score < 3.0:
        return False
    
    # Don't chain if second score is too low or much lower than first
    if second_score < 2.0:
        return False
    
    # Don't chain if second score is less than 50% of first score
    if second_score < (best_score * 0.5):
        return False
    
    # Check if task explicitly mentions multiple domains that would benefit from chaining
    task_lower = task.lower()
    
    # Look for explicit multi-domain indicators (generic patterns)
    # Patterns that suggest multiple skills needed:
    # - Action verbs followed by different action verbs
    # - "and then", "and apply", "then use" patterns
    # - Domain-specific terms combined with analysis/framework terms
    multi_domain_patterns = [
        r'\b(analyze|gather|collect|fetch).*?\b(apply|use|framework|solve|analyze)\b',
        r'\b(and then|and apply|then use|then apply)\b',
        r'\b(data|information|results).*?\b(framework|methodology|strategy|analyze)\b',
        r'\b(problem|solve|solution).*?\b(analyze|data|framework)\b',
    ]
    
    has_multi_domain = any(
        re.search(pattern, task_lower, re.IGNORECASE)
        for pattern in multi_domain_patterns
    )
    
    # Only chain if:
    # 1. Task explicitly mentions multiple domains, OR
    # 2. Both skills have high scores and are close together
    if has_multi_domain:
        return True
    
    # If both scores are high and close, consider chaining
    if best_score >= 5.0 and second_score >= 4.0 and (second_score / best_score) >= 0.7:
        return True
    
    return False


def select_multiple_skills(skills: List[Dict[str, Any]], task: str, max_skills: int = 2) -> List[Dict[str, Any]]:
    """Select multiple relevant skills for a task - only when it makes logical sense."""
    if not skills:
        return []
    
    # Score all skills
    scored_skills = [(skill, score_skill_relevance(skill, task)) for skill in skills]
    scored_skills.sort(key=lambda x: x[1], reverse=True)
    
    # Default to single best skill
    best_skill, best_score = scored_skills[0]
    
    # Only return multiple skills if chaining makes logical sense
    if should_chain_skills(scored_skills, task):
        selected = [best_skill]
        # Add second skill if it's relevant enough
        if len(scored_skills) > 1:
            second_skill, second_score = scored_skills[1]
            if second_score >= 2.0:  # Minimum threshold for second skill
                selected.append(second_skill)
        return selected
    
    # Return single best skill
    if best_score > 0:
        return [best_skill]
    
    return []


def generate_task_prompt(skill: Dict[str, Any], user_task: str) -> str:
    """Generate an optimized task prompt based on skill structure."""
    scripts = skill.get("scripts", [])
    references = skill.get("references", [])
    
    prompt_parts = [user_task]
    prompt_parts.append("\n\nINSTRUCTIONS:")
    
    # Script usage instructions - emphasize comprehensive use
    if scripts:
        prompt_parts.append(f"\n1. Available scripts ({len(scripts)}): {', '.join(scripts)}")
        prompt_parts.append("   - MANDATORY: Use MULTIPLE scripts (at least 80% of available)")
        prompt_parts.append(f"   - If {len(scripts)} scripts exist, use at least {max(1, int(len(scripts) * 0.8))} of them")
        prompt_parts.append("   - Execute scripts in the sequence recommended by SKILL.md")
        prompt_parts.append("   - Start with data fetching scripts, then analysis scripts")
        prompt_parts.append("   - Chain scripts: use output from one as input for the next")
        prompt_parts.append("   - Each script provides different data - combine them all")
        prompt_parts.append("   - Don't skip scripts unless SKILL.md explicitly says to")
    else:
        prompt_parts.append("\n1. No scripts available - work with available references and knowledge")
    
    # Reference usage instructions - emphasize comprehensive use
    if references:
        pdf_files = skill.get("pdf_files", [])
        text_refs = [r for r in references if r not in pdf_files]
        prompt_parts.append(f"\n2. Available references ({len(references)} total):")
        if text_refs:
            prompt_parts.append(f"   - Text files ({len(text_refs)}): {', '.join(text_refs[:5])}{'...' if len(text_refs) > 5 else ''}")
        if pdf_files:
            prompt_parts.append(f"   - PDF files ({len(pdf_files)}): {', '.join(pdf_files)}")
            prompt_parts.append("     * Use read_pdf tool to extract text from PDF files")
        
        # Calculate minimum references to read based on total count
        min_refs = min(3, len(references)) if len(references) <= 3 else (3 if len(references) <= 6 else 4)
        prompt_parts.append(f"   - MANDATORY: Read MULTIPLE references (at least {min_refs} out of {len(references)} available)")
        prompt_parts.append("   - Reference reading guidelines:")
        prompt_parts.append("     * If 2-3 references exist: read at least 2")
        prompt_parts.append("     * If 4-6 references exist: read at least 3")
        prompt_parts.append(f"     * If 7+ references exist (like you have {len(references)}): read at least 3-4")
        prompt_parts.append("   - Each reference provides different value:")
        prompt_parts.append("     * Frameworks for structured thinking (e.g., analytical-frameworks.md, structure-methods.md)")
        prompt_parts.append("     * Methodologies for approaches (e.g., analysis-methods.md, design-thinking.md)")
        prompt_parts.append("     * Examples for patterns (e.g., examples.md)")
        prompt_parts.append("     * Communication strategies (e.g., communication.md)")
        prompt_parts.append("     * Problem definition (e.g., tosca-framework.md)")
        prompt_parts.append("   - Read references even if scripts provide data - they add context")
        prompt_parts.append("   - Use read_pdf for PDFs, read_reference for text files")
        prompt_parts.append("   - Don't skip references - each one adds unique value")
        prompt_parts.append(f"   - With {len(references)} references available, you should read at least {min_refs} to get comprehensive coverage")
    else:
        prompt_parts.append("\n2. No reference files available")
    
    # SKILL.md as primary reference
    prompt_parts.append("\n3. SKILL.md is the PRIMARY reference:")
    prompt_parts.append("   - Use read_skill_md tool FIRST to understand the skill")
    prompt_parts.append("   - SKILL.md explains workflows, script usage, and when to use references")
    prompt_parts.append("   - Follow the guidance and structure in SKILL.md")
    
    # Emphasize chaining multiple resources
    prompt_parts.append("\n4. CHAIN MULTIPLE RESOURCES within this single skill:")
    if scripts and len(scripts) > 1:
        prompt_parts.append(f"   - Chain multiple scripts: {', '.join(scripts[:3])}{'...' if len(scripts) > 3 else ''}")
        prompt_parts.append("   - Execute scripts sequentially as they build on each other")
    if references and len(references) > 1:
        prompt_parts.append(f"   - Read multiple references: {', '.join(references[:3])}{'...' if len(references) > 3 else ''}")
        prompt_parts.append("   - Use different references for different purposes (frameworks, examples, methodologies)")
    if scripts and references:
        prompt_parts.append("   - Combine scripts (for data) with references (for context/frameworks)")
    
    # List files tool
    prompt_parts.append("\n5. Use list_files tool to see all available resources")
    
    # Output instructions
    prompt_parts.append("\n6. Synthesize information from ALL resources used:")
    if scripts:
        prompt_parts.append(f"   - Chain and combine outputs from multiple scripts ({len(scripts)} available)")
    if references:
        prompt_parts.append(f"   - Integrate insights from multiple references ({len(references)} available)")
    prompt_parts.append("   - Your knowledge and analysis")
    
    prompt_parts.append("\n7. Provide a comprehensive, actionable response that synthesizes information from all scripts and references you used, following SKILL.md's structure and recommendations.")
    
    return "".join(prompt_parts)

