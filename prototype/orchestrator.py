"""LLM-based orchestrator for intelligent skill selection and chaining."""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from logger_config import get_logger
import json
import os

logger = get_logger(__name__)


class SkillOrchestrator:
    """Intelligent orchestrator that uses LLM to select and chain skills."""
    
    def __init__(self):
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))  # Lower temp for more consistent decisions
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def should_use_skills(
        self,
        available_skills: List[Dict[str, Any]],
        task: str
    ) -> Dict[str, Any]:
        """Determine if the task needs skills or can be answered directly by LLM."""
        
        # Prepare skill summaries for LLM
        skill_summaries = []
        for i, skill in enumerate(available_skills):
            summary = {
                "index": i,
                "name": skill["name"],
                "description": skill["description"],
                "has_scripts": len(skill.get("scripts", [])) > 0,
                "script_count": len(skill.get("scripts", [])),
                "has_references": len(skill.get("references", [])) > 0,
                "reference_count": len(skill.get("references", [])),
                "capabilities": self._extract_capabilities(skill)
            }
            skill_summaries.append(summary)
        
        # First decision: Do we need skills at all?
        decision_prompt = f"""You are an intelligent skill orchestrator. Your first job is to determine if a task requires specialized skills or can be answered directly.

AVAILABLE SKILLS:
{json.dumps(skill_summaries, indent=2)}

TASK: {task}

Analyze the task and determine:
1. Does this task require specialized skills (scripts, frameworks, domain knowledge from references)?
2. Or can this be answered directly with general knowledge?

A task NEEDS skills if it requires:
- Executing scripts to gather/process data
- Accessing specialized frameworks or methodologies
- Domain-specific knowledge from reference files
- Complex analysis that benefits from structured approaches

A task does NOT need skills if it's:
- A general knowledge question
- A simple explanation or definition
- A straightforward question that doesn't require specialized tools
- A conversational query

Respond with a JSON object in this exact format:
{{
    "needs_skills": true/false,  // Whether any skills are needed
    "reasoning": "Brief explanation of why skills are or aren't needed"
}}

If needs_skills is false, the task will be answered directly by the LLM without using any skills."""

        try:
            response = self.llm.invoke(decision_prompt)
            response_text = response.content.strip()
            
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            decision = json.loads(response_text)
            return decision
            
        except Exception as e:
            logger.warning(f"LLM decision failed ({e}), defaulting to using skills")
            return {"needs_skills": True, "reasoning": "Fallback: using skills"}
    
    def select_skills(
        self,
        available_skills: List[Dict[str, Any]],
        task: str
    ) -> List[Dict[str, Any]]:
        """Use LLM to intelligently select which skills to use for a task."""
        
        # First check if skills are needed
        decision = self.should_use_skills(available_skills, task)
        
        if not decision.get("needs_skills", True):
            # Return empty list to indicate no skills needed
            return []
        
        # Prepare skill summaries for LLM
        skill_summaries = []
        for i, skill in enumerate(available_skills):
            summary = {
                "index": i,
                "name": skill["name"],
                "description": skill["description"],
                "has_scripts": len(skill.get("scripts", [])) > 0,
                "script_count": len(skill.get("scripts", [])),
                "has_references": len(skill.get("references", [])) > 0,
                "reference_count": len(skill.get("references", [])),
                "capabilities": self._extract_capabilities(skill)
            }
            skill_summaries.append(summary)
        
        # Create prompt for LLM to select skills with emphasis on relevance
        prompt = f"""You are an intelligent skill orchestrator. Your job is to select the best skill(s) to complete a task with MAXIMUM RELEVANCE.

AVAILABLE SKILLS:
{json.dumps(skill_summaries, indent=2)}

TASK: {task}

Analyze the task and available skills. Determine:
1. Which skill(s) are MOST RELEVANT to this specific task
2. The optimal order for executing them (if multiple)
3. How they should work together to maximize relevance

RELEVANCE CRITERIA (in order of importance):
- Direct match: Skill's description/goal directly addresses the task
- Capability match: Skill has scripts/references that can answer the task
- Domain match: Skill operates in the same domain as the task
- Complementarity: Multiple skills together provide more complete answer

Consider:
- Each skill's description and capabilities
- Whether the task requires data gathering, analysis, frameworks, or problem-solving
- Whether multiple skills can complement each other
- The logical flow: data gathering → analysis → frameworks → recommendations
- RELEVANCE: Only select skills that are truly relevant - avoid marginally relevant skills

IMPORTANT: Prefer fewer, highly relevant skills over many marginally relevant ones.
If one skill can handle the task alone with high relevance, select only that skill.

Respond with a JSON object in this exact format:
{{
    "selected_skill_indices": [0, 1],  // List of skill indices to use (can be 1 or more)
    "execution_order": [0, 1],  // Order to execute them (same as indices if sequential)
    "execution_mode": "sequential" or "parallel",  // "sequential" if skills depend on each other, "parallel" if they can run independently
    "dependencies": {{"1": [0]}},  // Optional: which skills depend on which (e.g., skill 1 depends on skill 0)
    "reasoning": "Brief explanation of why these skills were selected and how they work together",
    "execution_flow": "Description of how the skills should work together (e.g., 'Skill 1 gathers data, Skill 2 analyzes it' or 'Skills 1 and 2 can run in parallel, then Skill 3 synthesizes')"
}}

EXECUTION MODE GUIDELINES:
- Use "sequential" when:
  * One skill's output is needed as input for another (e.g., data gathering → analysis)
  * Skills build on each other's work
  * There's a clear dependency chain
  
- Use "parallel" when:
  * Skills work on independent aspects of the task
  * Skills can gather different types of data simultaneously
  * Skills provide complementary but independent analyses
  * No skill depends on another's output

Only select skills that are truly relevant. Prefer fewer, highly relevant skills over many marginally relevant ones.
If one skill can handle the task alone, select only that skill."""

        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            skill_decision = json.loads(response_text)
            
            # Validate and extract selected skills
            selected_indices = skill_decision.get("selected_skill_indices", [])
            if not selected_indices:
                # Fallback: use first skill
                selected_indices = [0]
            
            selected_skills = [available_skills[i] for i in selected_indices if 0 <= i < len(available_skills)]
            
            # Add orchestration metadata
            execution_mode = skill_decision.get("execution_mode", "sequential")
            dependencies = skill_decision.get("dependencies", {})
            
            for i, skill in enumerate(selected_skills):
                skill["_orchestration"] = {
                    "reasoning": skill_decision.get("reasoning", ""),
                    "execution_flow": skill_decision.get("execution_flow", ""),
                    "order": skill_decision.get("execution_order", selected_indices),
                    "execution_mode": execution_mode,
                    "dependencies": dependencies,
                    "needs_skills_reasoning": decision.get("reasoning", "")
                }
            
            logger.info(f"Execution mode determined: {execution_mode}")
            if dependencies:
                logger.debug(f"Dependencies: {dependencies}")
            
            # Display ASCII flow diagram
            self._display_flow_diagram(selected_skills, execution_mode, dependencies)
            
            return selected_skills
            
        except Exception as e:
            logger.warning(f"LLM orchestration failed ({e}), falling back to simple selection")
            # Fallback to simple selection
            return self._fallback_selection(available_skills, task)
    
    def answer_directly(self, task: str) -> Dict[str, Any]:
        """Answer a task directly using LLM without any skills."""
        prompt = f"""Answer the following question or task directly using your knowledge. 
Provide a comprehensive, helpful response.

Task: {task}

Provide a clear, detailed answer."""

        try:
            response = self.llm.invoke(prompt)
            
            return {
                "status": "completed",
                "result": response.content,
                "agent_outputs": [{
                    "agent_name": "Direct LLM Response",
                    "output": response.content,
                    "reasoning": "Task answered directly without using specialized skills"
                }]
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "result": None
            }
    
    def _display_flow_diagram(self, skills: List[Dict[str, Any]], execution_mode: str, dependencies: Dict[str, List[int]]):
        """Display ASCII art flow diagram for execution plan."""
        logger.info("=" * 80)
        logger.info("EXECUTION FLOW DIAGRAM")
        logger.info("=" * 80)
        
        if execution_mode == "parallel":
            # Parallel execution diagram
            logger.info("")
            logger.info("PARALLEL EXECUTION:")
            logger.info("")
            for i, skill in enumerate(skills):
                logger.info(f"  ┌─ Task {i+1}: {skill['name']}")
                logger.info(f"  │  Role: {skill.get('role', 'N/A')[:50]}")
                logger.info(f"  │  Working independently...")
                logger.info(f"  └─ Output")
            
            logger.info("")
            logger.info("         │")
            logger.info("         │ (All outputs collected)")
            logger.info("         ▼")
            logger.info("  ┌──────────────────────┐")
            logger.info("  │  SYNTHESIS TASK      │")
            logger.info("  │  Combines all results│")
            logger.info("  └──────────────────────┘")
            logger.info("         │")
            logger.info("         ▼")
            logger.info("    FINAL OUTPUT")
            
        else:
            # Sequential execution diagram
            logger.info("")
            logger.info("SEQUENTIAL EXECUTION:")
            logger.info("")
            
            for i, skill in enumerate(skills):
                logger.info(f"  ┌─ Task {i+1}: {skill['name']}")
                logger.info(f"  │  Role: {skill.get('role', 'N/A')[:50]}")
                if i < len(skills) - 1:
                    logger.info(f"  │  Output →")
                    logger.info(f"  └───────────┐")
                    logger.info("              │")
                    logger.info("              ▼")
                else:
                    logger.info(f"  │  Final Output")
                    logger.info(f"  └─────────────")
        
        logger.info("")
        logger.info("=" * 80)
    
    def _extract_capabilities(self, skill: Dict[str, Any]) -> str:
        """Extract a brief description of skill capabilities."""
        capabilities = []
        
        if skill.get("scripts"):
            capabilities.append(f"Can execute {len(skill['scripts'])} script(s) for data processing")
        
        if skill.get("references"):
            capabilities.append(f"Has {len(skill['references'])} reference file(s) with frameworks/knowledge")
        
        if skill.get("pdf_files"):
            capabilities.append(f"Has {len(skill['pdf_files'])} PDF file(s) with detailed documentation")
        
        description = skill.get("description", "")
        if "analysis" in description.lower():
            capabilities.append("Provides analysis capabilities")
        if "framework" in description.lower() or "methodology" in description.lower():
            capabilities.append("Provides frameworks/methodologies")
        if "problem" in description.lower() or "solve" in description.lower():
            capabilities.append("Provides problem-solving capabilities")
        
        return "; ".join(capabilities) if capabilities else "General purpose skill"
    
    def _fallback_selection(self, available_skills: List[Dict[str, Any]], task: str) -> List[Dict[str, Any]]:
        """Fallback selection using simple keyword matching."""
        # Simple fallback: return first skill
        if available_skills:
            return [available_skills[0]]
        return []
    
    def generate_execution_plan(
        self,
        selected_skills: List[Dict[str, Any]],
        task: str
    ) -> Dict[str, Any]:
        """Generate an execution plan for the selected skills."""
        if len(selected_skills) == 1:
            return {
                "type": "single",
                "skills": selected_skills,
                "flow": "Execute single skill"
            }
        
        # Multi-skill execution plan
        plan = {
            "type": "chain",
            "skills": selected_skills,
            "flow": []
        }
        
        # Use orchestration metadata if available
        if selected_skills[0].get("_orchestration"):
            orchestration = selected_skills[0]["_orchestration"]
            plan["reasoning"] = orchestration.get("reasoning", "")
            plan["execution_flow"] = orchestration.get("execution_flow", "")
        
        # Build step-by-step flow
        for i, skill in enumerate(selected_skills):
            step = {
                "step": i + 1,
                "skill": skill["name"],
                "role": skill.get("role", ""),
                "has_scripts": len(skill.get("scripts", [])) > 0,
                "has_references": len(skill.get("references", [])) > 0,
                "instructions": self._generate_step_instructions(skill, i, len(selected_skills))
            }
            plan["flow"].append(step)
        
        return plan
    
    def _generate_step_instructions(
        self,
        skill: Dict[str, Any],
        step_index: int,
        total_steps: int
    ) -> str:
        """Generate instructions for a specific step in the chain."""
        instructions = []
        
        if step_index == 0:
            instructions.append("Start by gathering data and information")
        else:
            instructions.append(f"Build on the previous step's findings")
        
        if skill.get("scripts"):
            instructions.append(f"Use available scripts: {', '.join(skill['scripts'][:3])}")
        
        if skill.get("references"):
            instructions.append(f"Reference files available if needed: {len(skill['references'])} files")
        
        if step_index == total_steps - 1:
            instructions.append("Provide final comprehensive analysis and recommendations")
        
        return ". ".join(instructions) + "."

