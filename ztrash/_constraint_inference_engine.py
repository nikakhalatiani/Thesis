# from abc import ABC, abstractmethod
# import requests
# import subprocess
# import time
#
# from util.grammar_config import GrammarConfig
# from core.library.property_test import ExecutionTrace
#
#
#
# class ConstraintModel(ABC):
#     """Model interface for inferring constraints from execution traces."""
#
#     @abstractmethod
#     def infer_constraints(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> list[str]:
#         """Return a list of constraint expressions using grammar nonterminals."""
#         ...
#
#
# class ModelService(ABC):
#     """Abstract service for interacting with language models."""
#
#     @abstractmethod
#     def generate(self, prompt: str, options=None) -> str:
#         """Generate text using the model service."""
#         ...
#
#
# class OllamaService(ModelService):
#     """Service for interacting with Ollama API."""
#
#     def __init__(self, model_name: str, api_url: str = "http://localhost:11434/api/generate"):
#         self.model_name = model_name
#         self.api_url = api_url
#
#     def generate(self, prompt: str, options=None) -> str:
#         """Generate text using Ollama API."""
#         default_options = {
#             "temperature": 0.1,
#             "top_p": 0.5,
#             "num_predict": 500,
#             "stop": ["\n\n", "Explanation:", "Analysis:"]
#         }
#
#         if options:
#             default_options.update(options)
#
#         payload = {
#             "model": self.model_name,
#             "prompt": prompt,
#             "stream": False,
#             "options": default_options
#         }
#
#         try:
#             response = requests.post(self.api_url, json=payload)
#             response.raise_for_status()
#             result = response.json()
#             return result.get("response", "")
#         except Exception as e:
#             raise RuntimeError(f"Ollama API request failed: {e}")
#
#
# class ServiceHealthChecker(ABC):
#     """Abstract health checker for external services."""
#
#     @abstractmethod
#     def is_healthy(self) -> bool:
#         """Check if the service is healthy and accessible."""
#         ...
#
#     @abstractmethod
#     def start_if_needed(self) -> None:
#         """Start the service if it's not running."""
#         ...
#
#
# class OllamaHealthChecker(ServiceHealthChecker):
#     """Health checker for Ollama service."""
#
#     def __init__(self, health_check_url: str = "http://localhost:11434/api/tags"):
#         self.health_check_url = health_check_url
#
#     def is_healthy(self) -> bool:
#         """Check if Ollama server is running and accessible."""
#         try:
#             response = requests.get(self.health_check_url, timeout=5)
#             return response.status_code == 200
#         except requests.RequestException:
#             return False
#
#     def start_if_needed(self) -> None:
#         """Attempt to start Ollama if it's not running."""
#         if not self.is_healthy():
#             try:
#                 subprocess.Popen(
#                     ["ollama", "serve"],
#                     stdout=subprocess.DEVNULL,
#                     stderr=subprocess.DEVNULL
#                 )
#                 # Give it time to start
#                 time.sleep(2)
#
#                 if not self.is_healthy():
#                     raise RuntimeError("Failed to start Ollama service")
#             except (subprocess.SubprocessError, FileNotFoundError) as e:
#                 raise RuntimeError(f"Could not start Ollama: {e}")
#
#
# class PromptBuilder:
#     """Builder for creating constraint inference prompts."""
#
#     @staticmethod
#     def build_constraint_prompt(traces: list[ExecutionTrace], grammar: GrammarConfig) -> str:
#         """Build a prompt for constraint inference."""
#         nonterminals = grammar.nonterminals()
#         nonterminals_text = ", ".join(f"<{nt}>" for nt in nonterminals)
#
#         examples_text = PromptBuilder._get_examples_text()
#         cheatsheet = PromptBuilder._get_cheatsheet()
#         cases_text = PromptBuilder._format_traces(traces)
#
#         return (
#             "You are an expert in mathematical property testing and constraint inference.\n"
#             "Your main goal is to analyze the provided execution traces and discover correlations "
#             "between the patterns of passing and failing inputs.\n"
#             "You must generate new constraints that, when applied, will cause future generated inputs "
#             "to follow these correlations—so that inputs likely to pass the property are included, "
#             "and those likely to fail are excluded.\n\n"
#             f"{examples_text}\n\n"
#             f"{cheatsheet}\n"
#             "IMPORTANT: Only use non-terminals listed below.\n"
#             f"Available grammar nonterminals: {nonterminals_text}\n"
#             "Do NOT invent or use any nonterminals that are not present in the grammar.\n"
#             "- Cast to int() **only** non-terminals that expand exclusively to plain digits.\n"
#             "- Cast to len() **only** non-terminals that expand to strings or sequences.\n"
#             f"Current constraints: {grammar.extra_constraints or 'None'}\n\n"
#             f"{cases_text}\n\n"
#             "Feedback Loop Instructions:\n"
#             "- Carefully compare the patterns in passing and failing execution traces.\n"
#             "- IMPORTANT: You must produce NEW constraints that are different from existing ones. "
#             "Repeating existing constraints is not optimal as it clearly won't change the outcome.\n"
#             "- Your main objective is to propose Fandango constraint expressions that will generate inputs matching "
#             "the observed correlations: inputs that pass should be allowed, and those that fail should be excluded.\n"
#             "- Prefer constraints that are as general as possible, while still excluding the failing cases.\n"
#             "- Each constraint must use only the allowed grammar nonterminals.\n"
#             "- Constraints must be syntactically valid for the Fandango constraint system.\n"
#             "- Focus on constraints that are likely to distinguish between passing and failing input patterns.\n"
#             "- Return only the constraint expressions, one per line, with no extra explanation.\n"
#         )
#
#     @staticmethod
#     def _get_examples_text() -> str:
#         """Get examples text for the prompt."""
#         valid_examples = [
#             "int(<number>) != 0",
#             "abs(int(<number>)) >= 1",
#             "int(<number>) == int(<number>)",
#             "int(<number>) + int(<number>) < 100",
#             "len(<word>) > 0",
#         ]
#
#         invalid_examples = [
#             "int(<term>) != 0                        # <term> may be algebraic text",
#             "int(<expr>) == int(<expr>)              # <expr> can expand to '1,2'",
#             "<number> > 10                           # raw NT not allowed",
#         ]
#
#         return (
#                 "Examples of valid constraints:\n"
#                 + "\n".join(f"- {c}" for c in valid_examples)
#                 + "\n\nExamples of invalid constraints:\n"
#                 + "\n".join(f"- {c}" for c in invalid_examples)
#         )
#
#     @staticmethod
#     def _get_cheatsheet() -> str:
#         """Get cheatsheet text for the prompt."""
#         return (
#             "ALLOWED CONSTRUCTS:\n"
#             "int(<numeric_nt>) – where <numeric_nt> expands to digits only\n"
#             "len(<string_nt>) – where <string_nt> expands to a sequence of characters\n"
#             "abs(), min(), max(), sum() on numeric expressions already wrapped in int()\n"
#             "\n"
#             "FORBIDDEN CONSTRUCTS (never output these):\n"
#             "int(<any_nt>) if <any_nt> may contain non-digits or commas\n"
#             "len(<numeric_nt>)\n"
#             "Mixing int() and len() in the same comparison\n"
#             "Using raw <nonterminal> without a wrapper\n"
#         )
#
#     @staticmethod
#     def _format_traces(traces: list[ExecutionTrace]) -> str:
#         """Format execution traces for the prompt."""
#         passing_traces = [t for t in traces if t.get("comparison_result")]
#         failing_traces = [t for t in traces if not t.get("comparison_result")]
#
#         lines = []
#
#         if passing_traces:
#             prop = passing_traces[0]["property_name"]
#             lines.append(f"PASSING TEST CASES for {prop}:")
#             for trace in passing_traces:
#                 lines.append(f"  input={trace['input']}")
#         else:
#             lines.append("NO PASSING TEST CASES")
#
#         if failing_traces:
#             prop = failing_traces[0]["property_name"]
#             lines.append(f"\nFAILING TEST CASES for {prop}:")
#             for trace in failing_traces:
#                 lines.append(f"  input={trace['input']}")
#         else:
#             lines.append("\nNO FAILING TEST CASES")
#
#         return "\n".join(lines)
#
#
# class ConstraintParser:
#     """Parser for extracting valid constraints from model output."""
#
#     @staticmethod
#     def parse_constraints(raw_text: str, grammar: GrammarConfig) -> list[str]:
#         """Parse and validate constraints from raw model output."""
#         lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
#         valid_constraints = []
#
#         for line in lines:
#             # Skip explanation lines
#             if ConstraintParser._is_explanation_line(line):
#                 continue
#
#             # Validate and collect constraints
#             if grammar.validate_constraint(line):
#                 valid_constraints.append(line)
#
#         return valid_constraints
#
#     @staticmethod
#     def _is_explanation_line(line: str) -> bool:
#         """Check if a line is an explanation rather than a constraint."""
#         explanation_keywords = ['analysis:', 'explanation:', 'note:', 'based on']
#         return any(word in line.lower() for word in explanation_keywords)
#
#
# class LocalModel(ConstraintModel):
#     """Local inference model using dependency injection for better testability."""
#
#     def __init__(
#             self,
#             model_service: ModelService,
#             health_checker: ServiceHealthChecker | None = None,
#             prompt_builder: PromptBuilder | None = None,
#             constraint_parser: ConstraintParser | None = None
#     ):
#         self.model_service = model_service
#         self.health_checker = health_checker
#         self.prompt_builder = prompt_builder or PromptBuilder()
#         self.constraint_parser = constraint_parser or ConstraintParser()
#
#         # Ensure service is healthy if health checker is provided
#         if self.health_checker:
#             self.health_checker.start_if_needed()
#
#     def infer_constraints(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> list[str]:
#         """Infer constraints using the injected model service."""
#         if not traces:
#             return []
#
#         prompt = self.prompt_builder.build_constraint_prompt(traces, grammar)
#
#         try:
#             raw_text = self.model_service.generate(prompt)
#             return self.constraint_parser.parse_constraints(raw_text, grammar)
#         except Exception as e:
#             raise RuntimeError(f"Constraint inference failed: {e}")
#
#
# class ConstraintInferenceEngine:
#     """Engine coordinating constraint inference and grammar updates."""
#
#     def __init__(self, model: ConstraintModel) -> None:
#         self.model = model
#
#     def infer(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> list[str]:
#         """Infer new constraints from execution traces."""
#         return self.model.infer_constraints(traces, grammar)




# from dotenv import load_dotenv
#
# load_dotenv()
# import json
# import os
# from urllib import request, error

# class GeminiModel(ConstraintModel):
#     """Inference model backed by the Gemini generative API (v1beta, generateContent)."""
#
#     def __init__(self, api_key: str | None = None, model: str = "gemini-2.0-flash") -> None:
#         if api_key is None:
#             api_key = os.environ.get("GEMINI_API_KEY")
#         if not api_key:
#             raise ValueError("Gemini API key not provided. Please set GEMINI_API_KEY in your environment or .env file.")
#         self.api_key = api_key
#         self.model = model
#
#
#     def infer_constraints(self, traces: list[ExecutionTrace], grammar: GrammarConfig) -> list[str]:
#         if not traces:
#             return []
#         prompt = self._build_prompt(traces, grammar)
#
#         url = (
#             "https://generativelanguage.googleapis.com/v1beta/"
#             f"models/{self.model}:generateContent?key={self.api_key}"
#         )
#
#         body = {
#             "contents": [{"parts": [{"text": prompt}]}],
#             "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500, "topP": 0.8},
#         }
#         data = json.dumps(body).encode("utf-8")
#
#         req = request.Request(url, data=data, method="POST") # type: ignore[arg-type]
#         req.add_header("Content-Type", "application/json")
#
#         try:
#             with request.urlopen(req) as resp:
#                 resp_data = json.load(resp)
#         except error.HTTPError as e:
#             if e.code == 404:
#                 raise RuntimeError(f"Gemini endpoint not found: check API version & model name ({self.model})") from e
#             elif e.code == 400:
#                 raise RuntimeError("Gemini API error (400): Invalid request - check API key and model") from e
#             raise RuntimeError(f"Gemini request failed: {e.reason}") from e
#
#         try:
#             raw_text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
#         except (KeyError, IndexError, TypeError):
#             raise RuntimeError("Unexpected Gemini response structure")
#
#         lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
#         valid_constraints = []
#         for line in lines:
#             if any(word in line.lower() for word in ['analysis:', 'explanation:', 'note:', 'based on']):
#                 continue
#             if grammar.validate_constraint(line):
#                 valid_constraints.append(line)
#         return valid_constraints
