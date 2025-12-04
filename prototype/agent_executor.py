"""Execute skills as CrewAI agents."""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
from logger_config import get_logger
import subprocess
import json

logger = get_logger(__name__)

# PDF reading imports
PDFPLUMBER_AVAILABLE = False
PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pass

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    pass


class ScriptTool(BaseTool):
    """Tool for executing Python scripts from skills."""
    name: str = "execute_script"
    description: str = "Execute a Python script from the skill's scripts directory. Check SKILL.md first (using read_skill_md) to see which scripts to use and in what order. SKILL.md provides workflows and examples for script usage."
    
    def _run(self, script_name: str, args: str = "") -> str:
        """Execute a script with optional arguments."""
        skill_path_str = os.getenv("SKILL_PATH", ".")
        skill_path = Path(skill_path_str).resolve()  # Resolve to absolute path
        script_path = skill_path / "scripts" / script_name
        
        if not script_path.exists():
            # List available scripts to help the agent
            scripts_dir = skill_path / "scripts"
            if scripts_dir.exists():
                available = [f.name for f in scripts_dir.iterdir() if f.is_file() and f.suffix == '.py']
                return f"Error: Script '{script_name}' not found. Available scripts: {', '.join(available) if available else 'None'}"
            else:
                return f"Error: Scripts directory not found at {scripts_dir}"
        
        try:
            # Execute script
            cmd = ["python", str(script_path)]
            if args:
                cmd.extend(args.split())
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace problematic characters instead of failing
                timeout=300,
                cwd=str(skill_path),
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}  # Set encoding for Python scripts
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                error_msg = result.stderr if result.stderr else "Script execution failed"
                return f"Error: {error_msg}"
        except subprocess.TimeoutExpired:
            return "Error: Script execution timed out"
        except Exception as e:
            return f"Error: {str(e)}"


class ReadSkillMDTool(BaseTool):
    """Tool for reading the SKILL.md file - the primary reference for understanding the skill."""
    name: str = "read_skill_md"
    description: str = "Read the SKILL.md file - this is the PRIMARY reference that explains what the skill does, how to use it, available workflows, and guides you on when to use scripts and references. Always read this first to understand the skill's capabilities and structure."
    
    def _run(self) -> str:
        """Read the SKILL.md file."""
        skill_path_str = os.getenv("SKILL_PATH", ".")
        skill_path = Path(skill_path_str).resolve()
        skill_md_path = skill_path / "SKILL.md"
        
        if not skill_md_path.exists():
            return f"Error: SKILL.md not found at {skill_md_path}"
        
        try:
            return skill_md_path.read_text(encoding="utf-8", errors='replace')
        except Exception as e:
            return f"Error reading SKILL.md: {str(e)}"


class ReferenceTool(BaseTool):
    """Tool for reading reference files from skills."""
    name: str = "read_reference"
    description: str = "Read a reference file (text files like .md, .txt) ONLY when you need background context, frameworks, strategies, or methodologies. For PDF files, use read_pdf tool instead. Use read_skill_md first to understand the skill, then use list_files to see available files. Only read references that are directly relevant to the task - skip if not needed."
    
    def _run(self, filename: str) -> str:
        """Read a reference file."""
        skill_path_str = os.getenv("SKILL_PATH", ".")
        skill_path = Path(skill_path_str).resolve()  # Resolve to absolute path
        ref_path = skill_path / "references" / filename
        
        if not ref_path.exists():
            # List available files to help the agent
            ref_dir = skill_path / "references"
            if ref_dir.exists():
                available = [f.name for f in ref_dir.iterdir() if f.is_file()]
                pdf_files = [f.name for f in ref_dir.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']
                error_msg = f"Error: Reference file '{filename}' not found. Available files: {', '.join(available)}"
                if pdf_files:
                    error_msg += f"\nNote: PDF files ({', '.join(pdf_files)}) should be read using read_pdf tool, not read_reference."
                return error_msg
            else:
                return f"Error: References directory not found at {ref_dir}"
        
        # Check if it's a PDF file
        if ref_path.suffix.lower() == '.pdf':
            return f"Error: '{filename}' is a PDF file. Use read_pdf tool instead of read_reference to read PDF files."
        
        try:
            return ref_path.read_text(encoding="utf-8", errors='replace')
        except Exception as e:
            return f"Error reading file: {str(e)}"


class ListFilesTool(BaseTool):
    """Tool for listing available scripts and reference files."""
    name: str = "list_files"
    description: str = "List all available scripts and reference files in the skill"
    
    def _run(self) -> str:
        """List available files."""
        skill_path_str = os.getenv("SKILL_PATH", ".")
        skill_path = Path(skill_path_str).resolve()
        
        result = []
        
        # List scripts
        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists():
            scripts = [f.name for f in scripts_dir.iterdir() if f.is_file() and f.suffix == '.py']
            result.append(f"Available scripts: {', '.join(scripts) if scripts else 'None'}")
        else:
            result.append("Scripts directory not found")
        
        # List references
        ref_dir = skill_path / "references"
        if ref_dir.exists():
            refs = [f.name for f in ref_dir.iterdir() if f.is_file()]
            result.append(f"Available reference files: {', '.join(refs) if refs else 'None'}")
        else:
            result.append("References directory not found")
        
        return "\n".join(result)


class ReadPDFTool(BaseTool):
    """Tool for reading PDF files - available to all skills."""
    name: str = "read_pdf"
    description: str = "Read and extract text from a PDF file. Use this for PDF files in references directory or any PDF file path. Always use this tool when you encounter PDF files."
    
    def _run(self, filepath: str) -> str:
        """Read a PDF file and extract text."""
        skill_path_str = os.getenv("SKILL_PATH", ".")
        skill_path = Path(skill_path_str).resolve()
        
        # Handle relative paths (from references directory) or absolute paths
        pdf_path = Path(filepath)
        if not pdf_path.is_absolute():
            # Try references directory first
            ref_path = skill_path / "references" / filepath
            if ref_path.exists():
                pdf_path = ref_path
            else:
                # Try as relative to skill path
                pdf_path = skill_path / filepath
        
        if not pdf_path.exists():
            return f"Error: PDF file not found at {pdf_path}"
        
        if pdf_path.suffix.lower() != '.pdf':
            return f"Error: File is not a PDF: {pdf_path}"
        
        try:
            # Try pdfplumber first (better text extraction)
            if PDFPLUMBER_AVAILABLE:
                text_parts = []
                with pdfplumber.open(str(pdf_path)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                if text_parts:
                    return "\n\n".join(text_parts)
            
            # Fallback to PyPDF2
            if PYPDF2_AVAILABLE:
                import PyPDF2
                text_parts = []
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                if text_parts:
                    return "\n\n".join(text_parts)
            
            return "Error: No PDF library available. Please install pdfplumber or PyPDF2."
            
        except Exception as e:
            return f"Error reading PDF: {str(e)}"


class WriteFileTool(BaseTool):
    """Tool for writing files - generic tool available to all skills."""
    name: str = "write_file"
    description: str = "Write content to a file. Files are written to the outputs directory in the prototype folder (where main.py is), not in skill directories. Provide the file path (relative filename or subdirectory/filename) and the content to write. For text files, use .txt, .md, .json, .csv, etc. extensions."
    
    def _run(self, filepath: str, content: str) -> str:
        """Write content to a file in the prototype outputs directory."""
        # Get the prototype directory (where main.py is located)
        # main.py is in prototype/, so we go up from agent_executor.py to get prototype/
        prototype_dir = Path(__file__).parent.resolve()
        file_path = Path(filepath)
        
        # Handle relative paths - write to prototype/outputs/ directory
        if not file_path.is_absolute():
            # Write to outputs subdirectory in prototype folder
            outputs_dir = prototype_dir / "outputs"
            file_path = outputs_dir / filepath
        else:
            # For absolute paths, still write to outputs directory for safety
            outputs_dir = prototype_dir / "outputs"
            file_path = outputs_dir / file_path.name
        
        # Create parent directories if they don't exist
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            file_path.write_text(content, encoding='utf-8')
            
            logger.info(f"✓ Wrote file '{file_path.name}' ({len(content)} chars) to {file_path.parent}")
            return f"Successfully wrote {len(content)} characters to {file_path}"
        except Exception as e:
            logger.error(f"Error writing file '{filepath}': {str(e)}")
            return f"Error writing file: {str(e)}"


def create_agent_from_skill(agent_config: Dict[str, Any], skill_path: Path) -> Agent:
    """Create a CrewAI agent from skill configuration."""
    # Set environment variable for tools - use absolute path to avoid issues
    skill_path_abs = skill_path.resolve()
    os.environ["SKILL_PATH"] = str(skill_path_abs)
    
    # Create tools (including generic PDF reader, file writer, and SKILL.md reader)
    tools = [
        ReadSkillMDTool(),  # Primary reference - read first
        ScriptTool(),
        ReferenceTool(),
        ListFilesTool(),
        ReadPDFTool(),      # Generic PDF reader
        WriteFileTool()     # Generic file writer
    ]
    
    # Get LLM configuration
    model_name = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # Create LLM instance
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create agent
    agent = Agent(
        role=agent_config["role"],
        goal=agent_config["goal"],
        backstory=agent_config["backstory"],
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    return agent


def execute_skill_agent(
    skill_path: Path,
    task_description: str,
    agent_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a skill as a CrewAI agent."""
    # Create agent
    agent = create_agent_from_skill(agent_config, skill_path)
    
    # Enhanced task description that uses SKILL.md as primary reference
    # Emphasizes that a single skill can chain multiple scripts and references
    enhanced_task = f"""{task_description}

IMPORTANT INSTRUCTIONS:
1. FIRST: Read SKILL.md using read_skill_md tool - this is the PRIMARY reference that explains:
   - What this skill does and its purpose
   - Available workflows and how to use them
   - Which scripts to use and when
   - Which references are available and when to use them
   - Best practices and examples

2. CHAIN MULTIPLE RESOURCES: A single skill can chain multiple scripts and/or references:
   - **Multiple Scripts**: Execute scripts sequentially (e.g., fetch_data.py → process_data.py → analyze.py)
   - **Multiple References**: Read different reference files for different purposes (e.g., frameworks.md, methodologies.md, examples.md)
   - **Combine Scripts + References**: Use scripts for data processing and references for context/frameworks
   - Follow SKILL.md guidance to determine which resources to use and in what order

3. Follow the guidance in SKILL.md to:
   - Use the recommended scripts in the suggested order (chain multiple if available)
   - Read multiple references when SKILL.md indicates they're needed
   - Follow the workflows described in SKILL.md
   - Synthesize information from all resources used

4. Use MULTIPLE scripts as guided by SKILL.md:
   - Follow the workflow patterns described
   - Use scripts in the sequence recommended
   - Chain scripts together when they build on each other (e.g., data gathering → processing → analysis)
   - Use almost all available scripts, not just one

5. Read MULTIPLE reference files when needed:
   - SKILL.md specifically mentions them for your task
   - You need different types of context (frameworks, methodologies, examples, strategies)
   - The task requires multiple perspectives or approaches
   - Different references provide complementary information

6. SKILL.md is your guide - follow its structure and recommendations

Your final output should synthesize information from ALL scripts and references you used, following SKILL.md's guidance."""
    
    # Create task with emphasis on chaining multiple resources
    task = Task(
        description=enhanced_task,
        agent=agent,
        expected_output="A comprehensive analysis that chains and synthesizes information from multiple scripts and/or reference files, following SKILL.md guidance"
    )
    
    # Create crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True
    )
    
    # Execute
    try:
        result = crew.kickoff()
        
        return {
            "status": "completed",
            "result": str(result),
            "agent_outputs": [
                {
                    "agent_name": agent_config["name"],
                    "output": str(result),
                    "reasoning": getattr(result, "reasoning", "N/A")
                }
            ]
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "result": None
        }


def create_agent_with_skill_path(agent_config: Dict[str, Any], skill_path: Path) -> Agent:
    """Create an agent with a specific skill path (for chaining).
    
    This function creates agents with isolated tools that don't rely on
    the global SKILL_PATH environment variable, ensuring each agent in
    a chain uses its own skill directory.
    """
    skill_path_abs = skill_path.resolve()
    
    logger.debug(f"Creating agent with skill path: {skill_path_abs}")
    
    # Create tools with skill path embedded (isolated from global SKILL_PATH)
    class ScriptToolWithPath(ScriptTool):
        def _run(self, script_name: str, args: str = "") -> str:
            skill_name = agent_config.get('name', 'unknown')
            script_path = skill_path_abs / "scripts" / script_name
            
            if not script_path.exists():
                scripts_dir = skill_path_abs / "scripts"
                if scripts_dir.exists():
                    available = [f.name for f in scripts_dir.iterdir() if f.is_file() and f.suffix == '.py']
                    logger.warning(f"Script '{script_name}' not found in {scripts_dir} for agent {skill_name}. Available: {', '.join(available) if available else 'None'}")
                    return f"Error: Script '{script_name}' not found. Available: {', '.join(available) if available else 'None'}"
                logger.warning(f"Scripts directory not found at {scripts_dir} for agent {skill_name}")
                return f"Error: Scripts directory not found"
            
            try:
                logger.debug(f"Executing script '{script_name}' for agent {skill_name} from {script_path}")
                cmd = ["python", str(script_path)]
                if args:
                    cmd.extend(args.split())
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=300,
                    cwd=str(skill_path_abs),
                    env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                )
                if result.returncode == 0:
                    logger.info(f"✓ Executed script '{script_name}' successfully for agent {skill_name} ({len(result.stdout)} chars output)")
                    return result.stdout
                else:
                    logger.error(f"Script '{script_name}' failed for agent {skill_name}: {result.stderr if result.stderr else 'Script execution failed'}")
                    return f"Error: {result.stderr if result.stderr else 'Script execution failed'}"
            except subprocess.TimeoutExpired:
                logger.error(f"Script '{script_name}' timed out for agent {skill_name}")
                return "Error: Script execution timed out"
            except Exception as e:
                logger.error(f"Exception executing script '{script_name}' for agent {skill_name}: {str(e)}")
                return f"Error: {str(e)}"
    
    class ReadSkillMDToolWithPath(ReadSkillMDTool):
        def _run(self) -> str:
            # Use the specific skill path, not the global environment variable
            skill_md_path = skill_path_abs / "SKILL.md"
            skill_name = agent_config.get('name', 'unknown')
            
            if not skill_md_path.exists():
                logger.warning(f"SKILL.md not found at {skill_md_path} for agent {skill_name}")
                return f"Error: SKILL.md not found at {skill_md_path}"
            
            try:
                content = skill_md_path.read_text(encoding="utf-8", errors='replace')
                # Verify the content matches the expected skill by checking the frontmatter
                if skill_name.replace("-", "_") in content[:500] or skill_name in content[:500]:
                    logger.info(f"✓ Read SKILL.md from {skill_md_path.name} ({len(content)} chars) for agent {skill_name}")
                else:
                    logger.warning(f"⚠ SKILL.md content may not match expected skill {skill_name} - read from {skill_md_path}")
                return content
            except Exception as e:
                logger.error(f"Error reading SKILL.md from {skill_md_path} for agent {skill_name}: {str(e)}")
                return f"Error reading SKILL.md: {str(e)}"
    
    class ReferenceToolWithPath(ReferenceTool):
        def _run(self, filename: str) -> str:
            # Use the specific skill path, not the global environment variable
            skill_name = agent_config.get('name', 'unknown')
            ref_path = skill_path_abs / "references" / filename
            
            if not ref_path.exists():
                ref_dir = skill_path_abs / "references"
                if ref_dir.exists():
                    available = [f.name for f in ref_dir.iterdir() if f.is_file()]
                    logger.warning(f"Reference '{filename}' not found in {ref_dir} for agent {skill_name}. Available: {', '.join(available) if available else 'None'}")
                    return f"Error: Reference '{filename}' not found. Available: {', '.join(available) if available else 'None'}"
                logger.warning(f"References directory not found at {ref_dir} for agent {skill_name}")
                return f"Error: References directory not found"
            
            # Check if it's a PDF file
            if ref_path.suffix.lower() == '.pdf':
                logger.info(f"⚠ Reference '{filename}' is a PDF. Agent {skill_name} should use read_pdf tool instead.")
                return f"Error: '{filename}' is a PDF file. Use read_pdf tool instead of read_reference to read PDF files."
            
            try:
                content = ref_path.read_text(encoding="utf-8", errors='replace')
                logger.info(f"✓ Read reference '{filename}' from {ref_path.parent.name}/ ({len(content)} chars) for agent {skill_name}")
                return content
            except Exception as e:
                logger.error(f"Error reading reference '{filename}' from {ref_path} for agent {skill_name}: {str(e)}")
                return f"Error reading file: {str(e)}"
    
    class ListFilesToolWithPath(ListFilesTool):
        def _run(self) -> str:
            # Use the specific skill path, not the global environment variable
            skill_name = agent_config.get('name', 'unknown')
            result = []
            scripts_dir = skill_path_abs / "scripts"
            if scripts_dir.exists():
                scripts = [f.name for f in scripts_dir.iterdir() if f.is_file() and f.suffix == '.py']
                result.append(f"Available scripts: {', '.join(scripts) if scripts else 'None'}")
                logger.debug(f"Listed {len(scripts)} script(s) for agent {skill_name}")
            else:
                logger.debug(f"No scripts directory found for agent {skill_name}")
            
            ref_dir = skill_path_abs / "references"
            if ref_dir.exists():
                refs = [f.name for f in ref_dir.iterdir() if f.is_file()]
                pdf_files = [f.name for f in ref_dir.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']
                text_files = [f.name for f in ref_dir.iterdir() if f.is_file() and f.suffix.lower() != '.pdf']
                
                if text_files:
                    result.append(f"Available reference files (text): {', '.join(text_files)}")
                if pdf_files:
                    result.append(f"Available PDF files (use read_pdf tool): {', '.join(pdf_files)}")
                if not refs:
                    result.append("Available reference files: None")
                
                logger.debug(f"Listed {len(refs)} reference file(s) ({len(pdf_files)} PDFs, {len(text_files)} text) for agent {skill_name}")
            else:
                logger.debug(f"No references directory found for agent {skill_name}")
                result.append("Available reference files: None")
            
            return "\n".join(result) if result else "No files found"
    
    class ReadPDFToolWithPath(ReadPDFTool):
        def _run(self, filepath: str) -> str:
            # Use the specific skill path, not the global environment variable
            skill_name = agent_config.get('name', 'unknown')
            # Handle relative paths (from references directory) or absolute paths
            pdf_path = Path(filepath)
            if not pdf_path.is_absolute():
                # Try references directory first (most common case)
                ref_path = skill_path_abs / "references" / filepath
                if ref_path.exists():
                    pdf_path = ref_path
                else:
                    # Try as relative to skill path
                    pdf_path = skill_path_abs / filepath
            
            if not pdf_path.exists():
                # List available PDFs to help the agent
                ref_dir = skill_path_abs / "references"
                if ref_dir.exists():
                    available_pdfs = [f.name for f in ref_dir.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']
                    logger.warning(f"PDF '{filepath}' not found in {ref_dir} for agent {skill_name}. Available PDFs: {', '.join(available_pdfs) if available_pdfs else 'None'}")
                    return f"Error: PDF file not found at {pdf_path}. Available PDFs: {', '.join(available_pdfs) if available_pdfs else 'None'}"
                logger.warning(f"PDF '{filepath}' not found and references directory doesn't exist for agent {skill_name}")
                return f"Error: PDF file not found at {pdf_path}"
            
            if pdf_path.suffix.lower() != '.pdf':
                logger.warning(f"File '{filepath}' is not a PDF for agent {skill_name}")
                return f"Error: File is not a PDF: {pdf_path}"
            
            try:
                # Try pdfplumber first (better text extraction)
                if PDFPLUMBER_AVAILABLE:
                    text_parts = []
                    with pdfplumber.open(str(pdf_path)) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_parts.append(page_text)
                    if text_parts:
                        content = "\n\n".join(text_parts)
                        logger.info(f"✓ Read PDF '{pdf_path.name}' from {pdf_path.parent.name}/ ({len(content)} chars) for agent {skill_name}")
                        return content
                
                # Fallback to PyPDF2
                if PYPDF2_AVAILABLE:
                    import PyPDF2
                    text_parts = []
                    with open(pdf_path, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        for page in pdf_reader.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_parts.append(page_text)
                    if text_parts:
                        content = "\n\n".join(text_parts)
                        logger.info(f"✓ Read PDF '{pdf_path.name}' from {pdf_path.parent.name}/ ({len(content)} chars) for agent {skill_name}")
                        return content
                
                logger.error(f"No PDF library available for agent {skill_name}")
                return "Error: No PDF library available. Please install pdfplumber or PyPDF2."
                
            except Exception as e:
                logger.error(f"Error reading PDF '{pdf_path}' for agent {skill_name}: {str(e)}")
                return f"Error reading PDF: {str(e)}"
    
    class WriteFileToolWithPath(WriteFileTool):
        def _run(self, filepath: str, content: str) -> str:
            """Write content to a file in the prototype outputs directory (not in skill directory)."""
            skill_name = agent_config.get('name', 'unknown')
            # Get the prototype directory (where main.py is located)
            prototype_dir = Path(__file__).parent.resolve()
            file_path = Path(filepath)
            
            # Handle relative paths - write to prototype/outputs/ directory
            if not file_path.is_absolute():
                # Write to outputs subdirectory in prototype folder
                outputs_dir = prototype_dir / "outputs"
                file_path = outputs_dir / filepath
            else:
                # For absolute paths, still write to outputs directory for safety
                outputs_dir = prototype_dir / "outputs"
                file_path = outputs_dir / file_path.name
            
            # Create parent directories if they don't exist
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write content to file
                file_path.write_text(content, encoding='utf-8')
                
                logger.info(f"✓ Wrote file '{file_path.name}' ({len(content)} chars) to {file_path.parent} for agent {skill_name}")
                return f"Successfully wrote {len(content)} characters to {file_path}"
            except Exception as e:
                logger.error(f"Error writing file '{filepath}' for agent {skill_name}: {str(e)}")
                return f"Error writing file: {str(e)}"
    
    # Create tool instances with proper skill path isolation
    tools = [
        ReadSkillMDToolWithPath(), 
        ScriptToolWithPath(), 
        ReferenceToolWithPath(), 
        ListFilesToolWithPath(), 
        ReadPDFToolWithPath(),
        WriteFileToolWithPath()  # Generic file writer
    ]
    
    # Log tool creation for debugging
    logger.debug(f"Created {len(tools)} tools for agent {agent_config.get('name', 'unknown')} with skill path: {skill_path_abs}")
    
    model_name = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    agent = Agent(
        role=agent_config["role"],
        goal=agent_config["goal"],
        backstory=agent_config["backstory"],
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    return agent


def execute_skill_chain(
    skill_paths: list[Path],
    task_description: str,
    agent_configs: list[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute a chain of skills as a CrewAI crew (multiple agents working together).
    
    Uses CrewAI's sequential process with proper task context chaining:
    - Each task has context from previous tasks
    - Tasks are executed sequentially
    - Each agent builds on the previous agent's output
    """
    if len(skill_paths) != len(agent_configs):
        raise ValueError("Number of skill paths must match number of agent configs")
    
    logger.info(f"Creating skill chain with {len(skill_paths)} skill(s)")
    
    # Create agents for each skill with their own paths
    agents = []
    tasks = []
    
    for i, (skill_path, agent_config) in enumerate(zip(skill_paths, agent_configs)):
        logger.debug(f"Creating agent {i+1}/{len(skill_paths)}: {agent_config['name']}")
        agent = create_agent_with_skill_path(agent_config, skill_path)
        agents.append(agent)
        
        # Build task description that references previous tasks
        if i == 0:
            # First task: full description with emphasis on providing usable output
            task_desc = f"""{task_description}

CRITICAL: This is STEP 1 of {len(skill_paths)}. Your output will be the INPUT for the next agent.

YOUR RESPONSIBILITIES:
1. Read SKILL.md FIRST using read_skill_md tool to understand this skill's capabilities
2. Execute scripts and read references as needed to gather comprehensive information
3. Structure your output clearly so the next agent can easily use it:
   - Provide raw data, findings, and key insights
   - Include specific facts, numbers, and observations
   - Organize information in a logical structure
   - Make it clear what you discovered and what it means
4. Be thorough and complete - the next agent depends on your work

OUTPUT REQUIREMENTS:
- Comprehensive and detailed findings
- Clear structure (use headings, lists, sections)
- Specific data points and observations
- Key insights and preliminary conclusions
- Everything needed for the next agent to build upon"""
            
            expected_output = f"Comprehensive, well-structured data and findings from {agent_config['name']} that provides all necessary information for the next agent to build upon. Must include specific details, facts, and insights."
            context = []
        else:
            # Subsequent tasks: explicitly use previous output
            prev_skill_name = agent_configs[i-1]['name']
            prev_skill_role = agent_configs[i-1].get('role', prev_skill_name)
            
            task_desc = f"""{task_description}

CRITICAL: This is STEP {i+1} of {len(skill_paths)}. You MUST use the previous agent's output as your PRIMARY INPUT.

PREVIOUS AGENT'S WORK:
- Agent: {prev_skill_name} ({prev_skill_role})
- They have completed their analysis and provided findings
- Their output is automatically provided in your task context by CrewAI
- The context contains their complete output - you have full access to it

YOUR RESPONSIBILITIES:
1. FIRST: Access and read the previous agent's output from your task context:
   - CrewAI automatically provides previous task outputs in your task context
   - The output from {prev_skill_name} is available to you - you can see it in your context
   - READ THE ENTIRE OUTPUT carefully - don't skip any parts
   - Extract ALL key data points, findings, numbers, insights, and conclusions
   - Identify what information is relevant to your task
   - Understand the complete structure and all conclusions they provided
   - Note any specific facts, metrics, observations, or data they discovered
   - If the context contains structured data, extract all relevant fields
   
2. Read SKILL.md using read_skill_md tool to understand YOUR skill's capabilities

3. Apply YOUR skill's unique capabilities to the previous agent's findings:
   - Use your scripts to process/analyze their data (if applicable)
   - Apply your frameworks/methodologies to their findings
   - Use your references to provide additional context or analysis
   
4. BUILD ON their work - do NOT repeat what they already said:
   - Take their findings as GIVEN
   - Add YOUR analysis, frameworks, or insights
   - Synthesize: combine their work with your expertise
   - Provide NEW value that builds on their foundation

5. Structure your output to show:
   - What you received from the previous agent (summary)
   - What you added (your analysis, frameworks, insights)
   - How it all fits together (synthesis)
   - Final recommendations or conclusions

OUTPUT REQUIREMENTS:
- Explicitly reference and build upon the previous agent's findings
- Show clear progression from their work to your analysis
- Provide enhanced insights that weren't in the previous output
- Synthesize information from both agents
- If you're the last agent, provide final comprehensive conclusions"""
            
            expected_output = f"Enhanced analysis from {agent_config['name']} that explicitly builds on {prev_skill_name}'s findings, adds new insights using this skill's capabilities, and provides a synthesized result."
            # Context includes all previous tasks for full chain visibility
            context = tasks[:i]  # All previous tasks
        
        task = Task(
            description=task_desc,
            agent=agent,
            expected_output=expected_output,
            context=context  # CrewAI automatically includes previous task outputs in agent's context
        )
        tasks.append(task)
        if context:
            logger.debug(f"Task {i+1} created with context from {len(context)} previous task(s): {', '.join([agent_configs[j]['name'] for j in range(i)])}")
        else:
            logger.debug(f"Task {i+1} created (first task, no context)")
    
    # Create crew with sequential process
    logger.info("Creating CrewAI crew with sequential process...")
    
    # Log context chain for debugging
    context_chain = []
    for i, task in enumerate(tasks):
        if task.context:
            prev_names = [agent_configs[j]['name'] for j in range(i)]
            context_chain.append(f"Task {i+1} ({agent_configs[i]['name']}) <- context from: {', '.join(prev_names)}")
        else:
            context_chain.append(f"Task {i+1} ({agent_configs[i]['name']}) <- no context (first task)")
    logger.debug("Context chain: " + " -> ".join(context_chain))
    
    crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        process="sequential"  # Sequential execution: CrewAI automatically passes previous task outputs via context parameter
    )
    
    # Log context setup for debugging
    for i, task in enumerate(tasks):
        logger.debug(f"Task {i+1} ({agent_configs[i]['name']}): has context from {len(task.context)} previous task(s)")
    
    # Execute
    try:
        logger.info("Starting crew execution...")
        result = crew.kickoff()
        logger.info("Crew execution completed successfully")
        
        # Extract individual task outputs if available
        agent_outputs = []
        if hasattr(result, 'tasks_output') and result.tasks_output:
            for i, output in enumerate(result.tasks_output):
                agent_outputs.append({
                    "agent_name": agent_configs[i]["name"],
                    "output": str(output),
                    "step": i + 1
                })
        else:
            # Fallback if task outputs aren't directly accessible
            for i, config in enumerate(agent_configs):
                agent_outputs.append({
                    "agent_name": config["name"],
                    "output": f"See combined result (step {i+1})",
                    "step": i + 1
                })
        
        return {
            "status": "completed",
            "result": str(result),
            "agent_outputs": agent_outputs,
            "total_steps": len(agent_configs)
        }
    except Exception as e:
        logger.error(f"Crew execution failed: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "result": None
        }

