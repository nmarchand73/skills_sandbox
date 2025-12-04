# Skills Prototype

This prototype demonstrates how to convert a Claude Skill into a CrewAI agent and execute it.

**Note: This prototype runs directly without Docker. Docker support is available but optional for future use.**

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

Or set it directly:
```bash
export OPENAI_API_KEY=your-api-key-here  # Linux/Mac
set OPENAI_API_KEY=your-api-key-here     # Windows
```

## Usage

The prototype automatically discovers and selects the best skill(s) based on your question:

```bash
python main.py "your question or task"
```

### Examples

**Single Skill:**
```bash
# Supply chain analysis
python main.py "Analyze the Nvidia supply chain"

# Problem-solving frameworks
python main.py "Apply problem-solving frameworks to analyze a business challenge"
```

**Skill Chaining (Multiple Skills):**
```bash
# Data gathering + Problem solving
python main.py "Analyze supply chain data and apply problem-solving frameworks"

# Multi-step analysis
python main.py "Gather data, analyze findings, and apply frameworks to generate recommendations"
```

**Direct LLM Answer (No Skills Needed):**
```bash
python main.py "What is machine learning?"
```

### Debugging

Enable detailed logging:
```bash
# Windows PowerShell
$env:LOG_LEVEL="DEBUG"
python main.py "your question"

# Linux/Mac
export LOG_LEVEL=DEBUG
python main.py "your question"
```

Check logs:
```bash
# Windows PowerShell
Get-Content logs/prototype.log -Tail 50

# Linux/Mac
tail -50 logs/prototype.log
```

### Environment Variables

```bash
# Log level: DEBUG, INFO (default), WARNING, ERROR
$env:LOG_LEVEL="DEBUG"

# Custom log file
$env:LOG_FILE="logs/custom.log"

# OpenAI model
$env:OPENAI_MODEL="gpt-4-turbo-preview"
$env:OPENAI_TEMPERATURE="0.7"
```

The prototype will:
1. **Discover** all skills in `skills_samples/` directory
2. **Select** the best skill(s) based on your question
3. **Generate** optimized prompts based on each skill's structure (scripts, references)
4. **Execute** the agent(s) with the appropriate tools

## How It Works

1. **Skill Discovery**: Automatically scans `skills_samples/` directory and discovers all skills
2. **Skill Selection**: Matches your question to the best skill(s) using:
   - Keyword matching in skill descriptions
   - Relevance scoring based on task requirements
   - Automatic chaining of multiple skills if needed
3. **Prompt Generation**: Creates optimized prompts based on each skill's structure:
   - Lists available scripts and encourages using multiple scripts
   - Lists available references and suggests when to use them
   - Adapts instructions based on what's available (scripts vs references)
4. **Skill Parsing**: Reads SKILL.md and extracts YAML frontmatter (name, description)
5. **Agent Conversion**: Converts skill metadata into CrewAI agent configuration:
   - Role: Derived from skill name
   - Goal: From skill description
   - Backstory: From SKILL.md content
6. **Tools**: Creates tools that allow the agent to:
   - Execute Python scripts from `scripts/` directory (can chain multiple scripts sequentially)
   - Read reference files from `references/` directory (can read multiple references)
   - Read SKILL.md (primary reference that guides resource usage)
   - Read PDF files (generic tool available to all skills)
   - List available files
7. **Execution**: Runs the agent(s) directly in your Python environment with the given task using OpenAI API

**Single Skill Resource Chaining:** Within a single skill execution, agents can:
- **Chain multiple scripts**: Execute scripts sequentially (e.g., `fetch_data.py` → `process_data.py` → `analyze.py`)
- **Read multiple references**: Access different reference files for different purposes (e.g., frameworks, methodologies, examples)
- **Combine scripts and references**: Use scripts for data processing and references for context/frameworks
- The agent follows SKILL.md guidance to determine which resources to use and in what order

**No Docker Required**: The prototype executes skills directly in your local Python environment. Docker support is available for future use but not needed for testing.

## Skill Structure

Skills should have:
- `SKILL.md` with YAML frontmatter containing `name` and `description`
- `scripts/` directory with Python scripts (optional)
- `references/` directory with documentation files (optional)

