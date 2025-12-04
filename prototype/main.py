"""Main prototype script to execute a skill as a CrewAI agent."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from skill_parser import extract_agent_config
from agent_executor import execute_skill_agent, execute_skill_chain
from skill_discovery import discover_skills, generate_task_prompt
from orchestrator import SkillOrchestrator
from logger_config import setup_logging, get_logger
from typing import List, Dict, Any


def _display_execution_flow(skills: List[Dict[str, Any]], execution_mode: str, dependencies: Dict[str, List[int]]):
    """Display ASCII art flow diagram for execution plan."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("EXECUTION FLOW")
    logger.info("=" * 80)
    
    if execution_mode == "parallel":
        # Parallel execution diagram
        logger.info("")
        logger.info("Mode: PARALLEL (Independent tasks)")
        logger.info("")
        for i, skill in enumerate(skills):
            skill_name = skill['name'][:30]
            role = skill.get('role', 'N/A')[:40]
            logger.info(f"  ┌─────────────────────────────────────────┐")
            logger.info(f"  │ Task {i+1}: {skill_name:<30} │")
            logger.info(f"  │ {role:<41} │")
            logger.info(f"  │ Working independently...                │")
            logger.info(f"  └─────────────────────────────────────────┘")
        
        logger.info("")
        logger.info("         │")
        logger.info("         │ (All outputs collected)")
        logger.info("         ▼")
        logger.info("  ┌─────────────────────────────────────────┐")
        logger.info("  │      SYNTHESIS TASK                     │")
        logger.info("  │      Combines all parallel results      │")
        logger.info("  └─────────────────────────────────────────┘")
        logger.info("         │")
        logger.info("         ▼")
        logger.info("    ┌─────────────────┐")
        logger.info("    │  FINAL OUTPUT   │")
        logger.info("    └─────────────────┘")
        
    else:
        # Sequential execution diagram
        logger.info("")
        logger.info("Mode: SEQUENTIAL (Dependent tasks)")
        logger.info("")
        
        for i, skill in enumerate(skills):
            skill_name = skill['name'][:30]
            role = skill.get('role', 'N/A')[:40]
            logger.info(f"  ┌─────────────────────────────────────────┐")
            logger.info(f"  │ Task {i+1}: {skill_name:<30} │")
            logger.info(f"  │ {role:<41} │")
            
            if i < len(skills) - 1:
                logger.info(f"  │                                         │")
                logger.info(f"  └─────────────────┬───────────────────────┘")
                logger.info("                    │")
                logger.info("                    │ Output →")
                logger.info("                    ▼")
            else:
                logger.info(f"  │                                         │")
                logger.info(f"  └─────────────────────────────────────────┘")
                logger.info("                    │")
                logger.info("                    ▼")
                logger.info("            ┌─────────────────┐")
                logger.info("            │  FINAL OUTPUT   │")
                logger.info("            └─────────────────┘")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("")

# Set up logging
setup_logging()
logger = get_logger(__name__)

# Load environment variables (handle encoding issues gracefully)
try:
    load_dotenv(encoding='utf-8')
except (UnicodeDecodeError, Exception):
    logger.debug("Could not load .env file, using environment variables")

# Check for OpenAI API key
if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY not set in environment")
    logger.info("Please set it in .env file (UTF-8 encoded) or as environment variable")
    logger.info("Example: export OPENAI_API_KEY=your-key-here")
    sys.exit(1)


def main():
    """Main execution function."""
    # Discover skills
    skills_dir = Path(__file__).parent.parent / "skills"
    
    if not skills_dir.exists():
        logger.error(f"Skills directory not found: {skills_dir}")
        sys.exit(1)
    
    logger.info("Discovering available skills...")
    all_skills = discover_skills(skills_dir)
    
    if not all_skills:
        logger.error("No skills found in skills directory")
        sys.exit(1)
    
    logger.info(f"Found {len(all_skills)} skill(s): {', '.join([s['name'] for s in all_skills])}")
    
    # Get task from command line or use default
    if len(sys.argv) > 1:
        user_task = " ".join(sys.argv[1:])
    else:
        # Generic default task that will match available skills
        user_task = "Help me with analysis and insights"
    
    logger.info(f"Task: {user_task}")
    
    # Use LLM-based orchestrator to select skills
    logger.info("Orchestrating skills using LLM...")
    orchestrator = SkillOrchestrator()
    selected_skills = orchestrator.select_skills(all_skills, user_task)
    
    # Check if no skills are needed (direct LLM answer)
    if not selected_skills:
        decision = orchestrator.should_use_skills(all_skills, user_task)
        if not decision.get("needs_skills", True):
            logger.info("Decision: Task can be answered directly without skills")
            logger.debug(f"Reasoning: {decision.get('reasoning', 'N/A')}")
            logger.info("Answering directly using LLM...")
            result = orchestrator.answer_directly(user_task)
        else:
            logger.warning("No skills selected but skills may be needed. Using first available skill.")
            selected_skills = [all_skills[0]]
            # Continue with skill execution
            execution_plan = orchestrator.generate_execution_plan(selected_skills, user_task)
            # Execute single skill
            skill = selected_skills[0]
            skill_path = skill["path"]
            task_prompt = generate_task_prompt(skill, user_task)
            agent_config = {
                "name": skill["name"],
                "role": skill["role"],
                "goal": skill["goal"],
                "backstory": skill["backstory"]
            }
            logger.info(f"Executing skill: {skill['name']}")
            result = execute_skill_agent(skill_path, task_prompt, agent_config)
    else:
        # Skills are needed - proceed with execution
        # Show selection reasoning
        if len(selected_skills) == 1:
            skill = selected_skills[0]
            logger.info(f"Selected skill: {skill['name']}")
            if skill.get("_orchestration"):
                logger.debug(f"Reasoning: {skill['_orchestration'].get('reasoning', 'N/A')}")
        else:
            logger.info(f"Selected {len(selected_skills)} skill(s): {', '.join([s['name'] for s in selected_skills])}")
            if selected_skills[0].get("_orchestration"):
                orchestration = selected_skills[0]["_orchestration"]
                logger.debug(f"Reasoning: {orchestration.get('reasoning', 'N/A')}")
                logger.debug(f"Execution flow: {orchestration.get('execution_flow', 'N/A')}")
        
        # Generate execution plan
        execution_plan = orchestrator.generate_execution_plan(selected_skills, user_task)
        
        # Execute based on execution plan
        if execution_plan["type"] == "single":
            # Single skill execution
            skill = selected_skills[0]
            skill_path = skill["path"]
            
            logger.info(f"Skill: {skill['name']}")
            logger.debug(f"Description: {skill['description'][:150]}...")
            logger.debug(f"Scripts: {len(skill['scripts'])} available")
            logger.debug(f"References: {len(skill['references'])} available")
            
            # Generate optimized prompt based on skill structure
            task_prompt = generate_task_prompt(skill, user_task)
            
            agent_config = {
                "name": skill["name"],
                "role": skill["role"],
                "goal": skill["goal"],
                "backstory": skill["backstory"]
            }
            
            logger.info("Executing agent...")
            result = execute_skill_agent(skill_path, task_prompt, agent_config)
            
        else:
            # Multiple skills chained
            logger.info("Executing skill chain...")
            
            # Get execution mode and display flow
            execution_mode = selected_skills[0].get("_orchestration", {}).get("execution_mode", "sequential")
            dependencies = selected_skills[0].get("_orchestration", {}).get("dependencies", {})
            
            # Display ASCII flow diagram
            _display_execution_flow(selected_skills, execution_mode, dependencies)
            
            logger.debug("Execution plan:")
            for step in execution_plan["flow"]:
                logger.debug(f"  Step {step['step']}: {step['skill']} - {step['instructions']}")
            
            skill_paths = [s["path"] for s in selected_skills]
            agent_configs = [
                {
                    "name": s["name"],
                    "role": s["role"],
                    "goal": s["goal"],
                    "backstory": s["backstory"]
                }
                for s in selected_skills
            ]
            
            # Get execution mode
            execution_mode = selected_skills[0].get("_orchestration", {}).get("execution_mode", "sequential")
            
            # Generate combined prompt with clear flow instructions
            if execution_mode == "parallel":
                flow_parts = [f"{user_task}\n\nThis task requires {len(selected_skills)} skill(s) working in PARALLEL. Each agent works independently, then results will be synthesized.\n"]
            else:
                flow_parts = [f"{user_task}\n\nThis task requires {len(selected_skills)} skill(s) working in SEQUENCE. Each agent builds on the previous agent's output.\n"]
            
            for i, step in enumerate(execution_plan["flow"]):
                skill = selected_skills[i]
                flow_parts.append(f"\n{'='*60}")
                flow_parts.append(f"STEP {step['step']} - {skill['name']}")
                flow_parts.append(f"{'='*60}")
                flow_parts.append(f"Role: {skill.get('role', 'N/A')}")
                flow_parts.append(f"Instructions: {step['instructions']}")
                if skill.get('scripts'):
                    flow_parts.append(f"Available scripts: {', '.join(skill['scripts'])}")
                if skill.get('references'):
                    flow_parts.append(f"Available references: {len(skill['references'])} files")
                if execution_mode == "parallel":
                    flow_parts.append(f"\n→ You are working INDEPENDENTLY in parallel with other agents.")
                    flow_parts.append(f"  Provide comprehensive analysis from your perspective. Results will be synthesized later.")
                elif i < len(selected_skills) - 1:
                    next_skill = selected_skills[i+1]
                    flow_parts.append(f"\n→ Your output will be used by: {next_skill['name']} (Step {i+2})")
                    flow_parts.append(f"  Make sure your output is clear, complete, and usable by them.")
                else:
                    flow_parts.append(f"\n→ You are the FINAL step. Provide comprehensive final conclusions.")
                flow_parts.append("")
            
            if execution_plan.get("execution_flow"):
                flow_parts.append(f"\nOverall Flow: {execution_plan['execution_flow']}")
            
            task_prompt = "\n".join(flow_parts)
            
            # Get execution mode and dependencies from orchestration metadata
            execution_mode = selected_skills[0].get("_orchestration", {}).get("execution_mode", "sequential")
            dependencies = selected_skills[0].get("_orchestration", {}).get("dependencies", {})
            
            logger.info(f"Execution mode: {execution_mode}")
            if dependencies:
                logger.debug(f"Task dependencies: {dependencies}")
            
            result = execute_skill_chain(skill_paths, task_prompt, agent_configs, execution_mode, dependencies)
    
    # Display results
    logger.info("="*80)
    logger.info("EXECUTION RESULTS")
    logger.info("="*80)
    logger.info(f"Status: {result['status']}")
    
    if result['status'] == 'completed':
        logger.info(f"Result: {result['result']}")
        if result.get('agent_outputs'):
            logger.info(f"Agent Outputs: {len(result['agent_outputs'])} agent(s) executed")
    else:
        logger.error(f"Error: {result.get('error', 'Unknown error')}")
    
    return result


if __name__ == "__main__":
    main()
