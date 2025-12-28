"""
Deep Agent - Advanced AI Agent with planning, reflection, and goal tracking.

Features:
- Multi-step task planning and decomposition
- Self-reflection and response evaluation
- Automatic tool chaining
- Goal tracking and progress monitoring
- Error recovery with intelligent retry
- Feedback-based learning
- Reasoning transparency
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Generator
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import threading


class TaskStatus(Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReasoningType(Enum):
    """Types of reasoning steps."""
    PLANNING = "planning"
    ANALYSIS = "analysis"
    EXECUTION = "execution"
    REFLECTION = "reflection"
    ERROR_RECOVERY = "error_recovery"
    TOOL_SELECTION = "tool_selection"


@dataclass
class ReasoningStep:
    """A step in the agent's reasoning process."""
    step_type: str
    content: str
    timestamp: str = ""
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SubTask:
    """A subtask in a multi-step plan."""
    id: str
    description: str
    status: str = TaskStatus.PENDING.value
    tool: str = ""
    result: str = ""
    error: str = ""
    duration_ms: int = 0
    attempts: int = 0
    max_attempts: int = 3


@dataclass
class TaskPlan:
    """A plan for executing a complex task."""
    id: str
    goal: str
    subtasks: List[SubTask] = field(default_factory=list)
    status: str = TaskStatus.PENDING.value
    created_at: str = ""
    completed_at: str = ""
    total_duration_ms: int = 0
    reasoning: List[ReasoningStep] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Feedback:
    """User feedback on agent response."""
    id: str
    task_id: str
    rating: int  # 1-5
    comment: str = ""
    timestamp: str = ""
    response_improved: bool = False


class DeepAgent:
    """
    Advanced AI Agent with deep reasoning capabilities.
    
    Capabilities:
    - Task decomposition and planning
    - Self-reflection and quality evaluation
    - Automatic tool chaining based on context
    - Goal tracking with progress updates
    - Intelligent error recovery
    - Learning from user feedback
    """
    
    def __init__(self, base_agent, config_dir: Optional[Path] = None):
        """
        Initialize DeepAgent.
        
        Args:
            base_agent: The underlying LangGraph agent
            config_dir: Directory for storing agent data
        """
        self.base_agent = base_agent
        self.config_dir = config_dir or Path.home() / ".config" / "sysagent" / "deep_agent"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.plans_file = self.config_dir / "plans.json"
        self.feedback_file = self.config_dir / "feedback.json"
        self.patterns_file = self.config_dir / "patterns.json"
        
        self.current_plan: Optional[TaskPlan] = None
        self.reasoning_callbacks: List[Callable[[ReasoningStep], None]] = []
        self.progress_callbacks: List[Callable[[str, float], None]] = []
        
        self.plans_history: List[TaskPlan] = []
        self.feedback_history: List[Feedback] = []
        self.learned_patterns: Dict[str, Any] = {}
        
        self._load_data()
    
    def _load_data(self):
        """Load historical data."""
        try:
            if self.plans_file.exists():
                data = json.loads(self.plans_file.read_text())
                self.plans_history = [TaskPlan(**p) for p in data[-100:]]
        except Exception:
            pass
        
        try:
            if self.feedback_file.exists():
                data = json.loads(self.feedback_file.read_text())
                self.feedback_history = [Feedback(**f) for f in data[-500:]]
        except Exception:
            pass
        
        try:
            if self.patterns_file.exists():
                self.learned_patterns = json.loads(self.patterns_file.read_text())
        except Exception:
            pass
    
    def _save_data(self):
        """Save data to disk."""
        try:
            self.plans_file.write_text(json.dumps(
                [asdict(p) for p in self.plans_history[-100:]],
                indent=2
            ))
            self.feedback_file.write_text(json.dumps(
                [asdict(f) for f in self.feedback_history[-500:]],
                indent=2
            ))
            self.patterns_file.write_text(json.dumps(self.learned_patterns, indent=2))
        except Exception:
            pass
    
    def add_reasoning_callback(self, callback: Callable[[ReasoningStep], None]):
        """Add callback for reasoning steps."""
        self.reasoning_callbacks.append(callback)
    
    def add_progress_callback(self, callback: Callable[[str, float], None]):
        """Add callback for progress updates."""
        self.progress_callbacks.append(callback)
    
    def _emit_reasoning(self, step: ReasoningStep):
        """Emit a reasoning step to callbacks."""
        for callback in self.reasoning_callbacks:
            try:
                callback(step)
            except Exception:
                pass
    
    def _emit_progress(self, message: str, progress: float):
        """Emit progress update to callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(message, progress)
            except Exception:
                pass
    
    # ==================== TASK PLANNING ====================
    
    def analyze_task_complexity(self, task: str) -> Dict[str, Any]:
        """
        Analyze task complexity to determine if planning is needed.
        
        Returns:
            Dict with complexity analysis
        """
        # Simple heuristics for complexity
        complexity_indicators = {
            'multi_step': any(word in task.lower() for word in 
                ['and then', 'after that', 'first', 'next', 'finally', 'steps', 'process']),
            'conditional': any(word in task.lower() for word in 
                ['if', 'when', 'unless', 'depending', 'based on']),
            'iterative': any(word in task.lower() for word in 
                ['each', 'every', 'all', 'multiple', 'batch', 'loop']),
            'analytical': any(word in task.lower() for word in 
                ['analyze', 'compare', 'evaluate', 'assess', 'review', 'check']),
            'creative': any(word in task.lower() for word in 
                ['create', 'generate', 'design', 'build', 'make', 'write']),
        }
        
        complexity_score = sum(complexity_indicators.values())
        needs_planning = complexity_score >= 2 or len(task.split()) > 15
        
        return {
            'score': complexity_score,
            'indicators': complexity_indicators,
            'needs_planning': needs_planning,
            'estimated_steps': max(1, complexity_score + 1)
        }
    
    def create_plan(self, goal: str) -> TaskPlan:
        """
        Create a multi-step plan for a complex goal.
        
        Args:
            goal: The user's goal/request
            
        Returns:
            TaskPlan with subtasks
        """
        plan_id = f"plan_{int(time.time() * 1000)}"
        
        self._emit_reasoning(ReasoningStep(
            step_type=ReasoningType.PLANNING.value,
            content=f"Analyzing goal: {goal}"
        ))
        
        # Analyze complexity
        complexity = self.analyze_task_complexity(goal)
        
        plan = TaskPlan(id=plan_id, goal=goal)
        
        # Use LLM to decompose if complex
        if complexity['needs_planning']:
            self._emit_reasoning(ReasoningStep(
                step_type=ReasoningType.PLANNING.value,
                content="Task requires multi-step planning, decomposing..."
            ))
            
            subtasks = self._decompose_with_llm(goal)
            plan.subtasks = subtasks
        else:
            # Simple single-step task
            plan.subtasks = [SubTask(
                id=f"{plan_id}_1",
                description=goal
            )]
        
        plan.reasoning.append(ReasoningStep(
            step_type=ReasoningType.PLANNING.value,
            content=f"Created plan with {len(plan.subtasks)} steps",
            metadata={'complexity': complexity}
        ))
        
        self.current_plan = plan
        return plan
    
    def _decompose_with_llm(self, goal: str) -> List[SubTask]:
        """Use LLM to decompose a complex goal into subtasks."""
        try:
            # Create a planning prompt
            planning_prompt = f"""Break down this task into clear, sequential steps:

Task: {goal}

Respond with a JSON array of steps, each with:
- "description": what to do
- "tool": suggested tool to use (if known)

Example format:
[
  {{"description": "Check current system status", "tool": "system_info"}},
  {{"description": "Identify issues", "tool": ""}},
  {{"description": "Apply fixes", "tool": ""}}
]

Only return the JSON array, nothing else."""

            # Use base agent's LLM directly if available
            if hasattr(self.base_agent, 'llm') and self.base_agent.llm:
                from langchain_core.messages import HumanMessage
                response = self.base_agent.llm.invoke([HumanMessage(content=planning_prompt)])
                
                # Parse response
                content = response.content.strip()
                # Extract JSON from response
                if '[' in content:
                    json_start = content.index('[')
                    json_end = content.rindex(']') + 1
                    steps_json = json.loads(content[json_start:json_end])
                    
                    subtasks = []
                    for i, step in enumerate(steps_json):
                        subtasks.append(SubTask(
                            id=f"step_{i+1}",
                            description=step.get('description', ''),
                            tool=step.get('tool', '')
                        ))
                    return subtasks
        except Exception as e:
            self._emit_reasoning(ReasoningStep(
                step_type=ReasoningType.ERROR_RECOVERY.value,
                content=f"Failed to decompose with LLM: {e}, using simple decomposition"
            ))
        
        # Fallback: simple decomposition based on keywords
        return [SubTask(id="step_1", description=goal)]
    
    # ==================== EXECUTION ====================
    
    def execute_plan(self, plan: TaskPlan) -> Generator[Dict[str, Any], None, None]:
        """
        Execute a plan step by step with progress updates.
        
        Yields:
            Progress updates and results
        """
        plan.status = TaskStatus.IN_PROGRESS.value
        start_time = time.time()
        
        total_steps = len(plan.subtasks)
        
        for i, subtask in enumerate(plan.subtasks):
            # Update progress
            progress = i / total_steps
            self._emit_progress(f"Step {i+1}/{total_steps}: {subtask.description[:50]}...", progress)
            
            yield {
                'type': 'progress',
                'step': i + 1,
                'total': total_steps,
                'description': subtask.description,
                'progress': progress
            }
            
            # Execute subtask with retry
            result = self._execute_subtask(subtask)
            
            yield {
                'type': 'step_result',
                'step': i + 1,
                'success': subtask.status == TaskStatus.COMPLETED.value,
                'result': subtask.result,
                'error': subtask.error
            }
            
            # Check if we should continue
            if subtask.status == TaskStatus.FAILED.value:
                # Try error recovery
                if not self._attempt_recovery(subtask, plan):
                    plan.status = TaskStatus.FAILED.value
                    break
        
        # Final status
        if all(st.status == TaskStatus.COMPLETED.value for st in plan.subtasks):
            plan.status = TaskStatus.COMPLETED.value
        
        plan.completed_at = datetime.now().isoformat()
        plan.total_duration_ms = int((time.time() - start_time) * 1000)
        
        # Save plan
        self.plans_history.append(plan)
        self._save_data()
        
        # Final progress
        self._emit_progress("Complete", 1.0)
        
        yield {
            'type': 'complete',
            'success': plan.status == TaskStatus.COMPLETED.value,
            'duration_ms': plan.total_duration_ms
        }
    
    def _execute_subtask(self, subtask: SubTask) -> Dict[str, Any]:
        """Execute a single subtask with retry logic."""
        subtask.status = TaskStatus.IN_PROGRESS.value
        start_time = time.time()
        
        while subtask.attempts < subtask.max_attempts:
            subtask.attempts += 1
            
            self._emit_reasoning(ReasoningStep(
                step_type=ReasoningType.EXECUTION.value,
                content=f"Executing: {subtask.description} (attempt {subtask.attempts})"
            ))
            
            try:
                # Use base agent to execute
                result = self.base_agent.process_command(subtask.description)
                
                if result.get('success'):
                    subtask.status = TaskStatus.COMPLETED.value
                    subtask.result = result.get('message', 'Success')
                    break
                else:
                    subtask.error = result.get('message', 'Unknown error')
                    
                    # Don't retry for certain errors
                    if 'permission' in subtask.error.lower() or 'not found' in subtask.error.lower():
                        subtask.status = TaskStatus.FAILED.value
                        break
                    
            except Exception as e:
                subtask.error = str(e)
            
            # Wait before retry
            if subtask.attempts < subtask.max_attempts:
                time.sleep(1)
        
        if subtask.status != TaskStatus.COMPLETED.value:
            subtask.status = TaskStatus.FAILED.value
        
        subtask.duration_ms = int((time.time() - start_time) * 1000)
        
        return {
            'success': subtask.status == TaskStatus.COMPLETED.value,
            'result': subtask.result,
            'error': subtask.error
        }
    
    def _attempt_recovery(self, failed_subtask: SubTask, plan: TaskPlan) -> bool:
        """Attempt to recover from a failed subtask."""
        self._emit_reasoning(ReasoningStep(
            step_type=ReasoningType.ERROR_RECOVERY.value,
            content=f"Attempting recovery for: {failed_subtask.description}"
        ))
        
        # Analyze error and try alternative approach
        error = failed_subtask.error.lower()
        
        # Check if we can skip this step
        if 'optional' in failed_subtask.description.lower():
            self._emit_reasoning(ReasoningStep(
                step_type=ReasoningType.ERROR_RECOVERY.value,
                content="Step appears optional, continuing..."
            ))
            return True
        
        # Try rephrasing the task
        if failed_subtask.attempts < failed_subtask.max_attempts:
            alternative = f"Alternative approach: {failed_subtask.description}"
            self._emit_reasoning(ReasoningStep(
                step_type=ReasoningType.ERROR_RECOVERY.value,
                content=f"Trying alternative: {alternative}"
            ))
            
            failed_subtask.description = alternative
            result = self._execute_subtask(failed_subtask)
            return result.get('success', False)
        
        return False
    
    # ==================== SELF-REFLECTION ====================
    
    def reflect_on_response(self, query: str, response: str) -> Dict[str, Any]:
        """
        Reflect on and evaluate a response.
        
        Args:
            query: Original user query
            response: Agent's response
            
        Returns:
            Reflection analysis
        """
        self._emit_reasoning(ReasoningStep(
            step_type=ReasoningType.REFLECTION.value,
            content="Evaluating response quality..."
        ))
        
        # Quality checks
        checks = {
            'addresses_query': self._check_relevance(query, response),
            'is_complete': self._check_completeness(response),
            'is_accurate': self._check_accuracy(response),
            'is_helpful': self._check_helpfulness(response),
            'has_errors': self._check_for_errors(response),
        }
        
        score = sum(1 for v in checks.values() if v) / len(checks) * 100
        
        reflection = {
            'score': score,
            'checks': checks,
            'needs_improvement': score < 70,
            'suggestions': []
        }
        
        if not checks['addresses_query']:
            reflection['suggestions'].append("Response may not fully address the query")
        if not checks['is_complete']:
            reflection['suggestions'].append("Response may be incomplete")
        if checks['has_errors']:
            reflection['suggestions'].append("Response may contain errors")
        
        self._emit_reasoning(ReasoningStep(
            step_type=ReasoningType.REFLECTION.value,
            content=f"Quality score: {score:.0f}%",
            metadata=reflection
        ))
        
        return reflection
    
    def _check_relevance(self, query: str, response: str) -> bool:
        """Check if response is relevant to query."""
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words & response_words)
        return overlap >= min(3, len(query_words) // 2)
    
    def _check_completeness(self, response: str) -> bool:
        """Check if response appears complete."""
        # Check for truncation indicators
        truncation_indicators = ['...', '[truncated]', '[more]', 'etc.']
        if any(ind in response for ind in truncation_indicators):
            return False
        # Check minimum length
        return len(response) > 20
    
    def _check_accuracy(self, response: str) -> bool:
        """Basic accuracy check."""
        # Check for uncertainty markers
        uncertainty = ['i think', 'maybe', 'possibly', 'not sure', 'might be']
        return not any(u in response.lower() for u in uncertainty)
    
    def _check_helpfulness(self, response: str) -> bool:
        """Check if response is helpful."""
        # Check for actionable content
        helpful_indicators = ['here', 'you can', 'try', 'use', 'run', 'execute', 'result']
        return any(h in response.lower() for h in helpful_indicators)
    
    def _check_for_errors(self, response: str) -> bool:
        """Check if response contains error indicators."""
        error_indicators = ['error', 'failed', 'exception', 'cannot', 'unable']
        return any(e in response.lower() for e in error_indicators)
    
    def improve_response(self, query: str, response: str, reflection: Dict) -> str:
        """
        Attempt to improve a response based on reflection.
        
        Args:
            query: Original query
            response: Initial response
            reflection: Reflection analysis
            
        Returns:
            Improved response or original if improvement fails
        """
        if not reflection.get('needs_improvement'):
            return response
        
        self._emit_reasoning(ReasoningStep(
            step_type=ReasoningType.REFLECTION.value,
            content="Attempting to improve response..."
        ))
        
        try:
            improvement_prompt = f"""The following response may need improvement:

Original Query: {query}

Current Response: {response}

Issues identified:
{chr(10).join('- ' + s for s in reflection.get('suggestions', []))}

Please provide an improved, more complete response."""
            
            if hasattr(self.base_agent, 'llm') and self.base_agent.llm:
                from langchain_core.messages import HumanMessage
                improved = self.base_agent.llm.invoke([HumanMessage(content=improvement_prompt)])
                return improved.content
        except Exception:
            pass
        
        return response
    
    # ==================== TOOL CHAINING ====================
    
    def suggest_tool_chain(self, goal: str) -> List[Dict[str, Any]]:
        """
        Suggest a chain of tools to accomplish a goal.
        
        Args:
            goal: User's goal
            
        Returns:
            List of tool suggestions with order
        """
        self._emit_reasoning(ReasoningStep(
            step_type=ReasoningType.TOOL_SELECTION.value,
            content=f"Analyzing tools needed for: {goal}"
        ))
        
        # Common tool chains based on patterns
        tool_chains = {
            'system health': [
                {'tool': 'system_info', 'action': 'overview'},
                {'tool': 'monitoring', 'action': 'metrics'},
                {'tool': 'system_insights', 'action': 'health_check'},
            ],
            'cleanup': [
                {'tool': 'system_info', 'action': 'disk_usage'},
                {'tool': 'file_tool', 'action': 'find_large'},
                {'tool': 'file_tool', 'action': 'cleanup'},
            ],
            'security': [
                {'tool': 'security_tool', 'action': 'scan'},
                {'tool': 'network_tool', 'action': 'connections'},
                {'tool': 'process_tool', 'action': 'list'},
            ],
            'performance': [
                {'tool': 'monitoring', 'action': 'cpu'},
                {'tool': 'monitoring', 'action': 'memory'},
                {'tool': 'process_tool', 'action': 'top'},
            ],
        }
        
        # Match goal to patterns
        goal_lower = goal.lower()
        for pattern, chain in tool_chains.items():
            if pattern in goal_lower:
                return chain
        
        # Default: let the agent decide
        return []
    
    # ==================== FEEDBACK & LEARNING ====================
    
    def record_feedback(self, task_id: str, rating: int, comment: str = "") -> Feedback:
        """
        Record user feedback on a task.
        
        Args:
            task_id: ID of the task
            rating: 1-5 rating
            comment: Optional comment
            
        Returns:
            Feedback object
        """
        feedback = Feedback(
            id=f"fb_{int(time.time() * 1000)}",
            task_id=task_id,
            rating=max(1, min(5, rating)),
            comment=comment,
            timestamp=datetime.now().isoformat()
        )
        
        self.feedback_history.append(feedback)
        self._save_data()
        
        # Learn from feedback
        self._learn_from_feedback(feedback)
        
        return feedback
    
    def _learn_from_feedback(self, feedback: Feedback):
        """Learn patterns from feedback."""
        # Find the associated plan
        plan = next((p for p in self.plans_history if p.id == feedback.task_id), None)
        
        if not plan:
            return
        
        # Update patterns based on feedback
        if feedback.rating >= 4:
            # Good feedback - remember this approach
            pattern_key = self._extract_pattern_key(plan.goal)
            if pattern_key:
                if pattern_key not in self.learned_patterns:
                    self.learned_patterns[pattern_key] = {
                        'success_count': 0,
                        'approaches': []
                    }
                
                self.learned_patterns[pattern_key]['success_count'] += 1
                
                # Remember successful subtask sequence
                if plan.subtasks:
                    approach = [st.description for st in plan.subtasks if st.status == TaskStatus.COMPLETED.value]
                    if approach and approach not in self.learned_patterns[pattern_key]['approaches']:
                        self.learned_patterns[pattern_key]['approaches'].append(approach)
        
        self._save_data()
    
    def _extract_pattern_key(self, goal: str) -> str:
        """Extract a pattern key from a goal."""
        # Simple extraction of main intent
        keywords = ['check', 'show', 'list', 'find', 'create', 'delete', 'update', 
                   'clean', 'analyze', 'fix', 'run', 'start', 'stop']
        
        goal_lower = goal.lower()
        for kw in keywords:
            if kw in goal_lower:
                # Find what comes after the keyword
                idx = goal_lower.index(kw)
                rest = goal_lower[idx:].split()[:3]
                return ' '.join(rest)
        
        return goal_lower[:30]
    
    def get_learned_approach(self, goal: str) -> Optional[List[str]]:
        """
        Get a previously learned successful approach for a goal.
        
        Args:
            goal: User's goal
            
        Returns:
            List of steps if found, None otherwise
        """
        pattern_key = self._extract_pattern_key(goal)
        
        if pattern_key in self.learned_patterns:
            pattern = self.learned_patterns[pattern_key]
            if pattern['approaches']:
                self._emit_reasoning(ReasoningStep(
                    step_type=ReasoningType.ANALYSIS.value,
                    content=f"Found previously successful approach for '{pattern_key}'"
                ))
                return pattern['approaches'][0]
        
        return None
    
    # ==================== HIGH-LEVEL INTERFACE ====================
    
    def process_with_reasoning(self, query: str) -> Generator[Dict[str, Any], None, None]:
        """
        Process a query with full reasoning transparency.
        
        Yields:
            Reasoning steps, progress updates, and final result
        """
        start_time = time.time()
        
        # 1. Analyze task
        yield {'type': 'reasoning', 'step': 'Analyzing request...'}
        
        complexity = self.analyze_task_complexity(query)
        
        yield {
            'type': 'analysis',
            'complexity': complexity['score'],
            'needs_planning': complexity['needs_planning']
        }
        
        # 2. Check for learned approaches
        learned = self.get_learned_approach(query)
        if learned:
            yield {
                'type': 'reasoning',
                'step': f'Using previously successful approach with {len(learned)} steps'
            }
        
        # 3. Create plan if needed
        if complexity['needs_planning']:
            yield {'type': 'reasoning', 'step': 'Creating execution plan...'}
            plan = self.create_plan(query)
            
            yield {
                'type': 'plan',
                'steps': [{'description': st.description} for st in plan.subtasks]
            }
            
            # 4. Execute plan
            for update in self.execute_plan(plan):
                yield update
            
            # Compile results
            results = [st.result for st in plan.subtasks if st.result]
            final_response = '\n'.join(results) if results else "Task completed."
        
        else:
            # Simple execution
            yield {'type': 'reasoning', 'step': 'Executing directly...'}
            
            result = self.base_agent.process_command(query)
            final_response = result.get('message', 'Done')
            
            yield {
                'type': 'step_result',
                'step': 1,
                'success': result.get('success', False),
                'result': final_response
            }
        
        # 5. Self-reflection
        yield {'type': 'reasoning', 'step': 'Evaluating response quality...'}
        
        reflection = self.reflect_on_response(query, final_response)
        
        if reflection.get('needs_improvement'):
            yield {'type': 'reasoning', 'step': 'Improving response...'}
            final_response = self.improve_response(query, final_response, reflection)
        
        # 6. Final result
        duration_ms = int((time.time() - start_time) * 1000)
        
        yield {
            'type': 'final',
            'response': final_response,
            'quality_score': reflection.get('score', 0),
            'duration_ms': duration_ms
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get agent statistics."""
        total_plans = len(self.plans_history)
        successful = sum(1 for p in self.plans_history if p.status == TaskStatus.COMPLETED.value)
        
        avg_rating = 0
        if self.feedback_history:
            avg_rating = sum(f.rating for f in self.feedback_history) / len(self.feedback_history)
        
        return {
            'total_plans': total_plans,
            'successful_plans': successful,
            'success_rate': successful / total_plans * 100 if total_plans > 0 else 0,
            'total_feedback': len(self.feedback_history),
            'average_rating': avg_rating,
            'learned_patterns': len(self.learned_patterns)
        }


# Factory function
def create_deep_agent(base_agent) -> DeepAgent:
    """Create a DeepAgent wrapping a base agent."""
    return DeepAgent(base_agent)
