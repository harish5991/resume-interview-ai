import re
from typing import Tuple, Dict, Any, List

class QuestionIntent:
    PROJECT_OVERVIEW = "PROJECT_OVERVIEW"
    PROJECT_ROLE = "PROJECT_ROLE"
    TECHNICAL_DECISION = "TECHNICAL_DECISION"
    WHY_TECHNOLOGY = "WHY_TECHNOLOGY"
    PROBLEM_SOLVING = "PROBLEM_SOLVING"
    CHALLENGE = "CHALLENGE"
    FAILURE = "FAILURE"
    LEARNING = "LEARNING"
    SCALABILITY = "SCALABILITY"
    PERFORMANCE = "PERFORMANCE"
    DATABASE = "DATABASE"
    ARCHITECTURE = "ARCHITECTURE"
    SECURITY = "SECURITY"
    DEBUGGING = "DEBUGGING"
    TEAMWORK = "TEAMWORK"
    CONFLICT = "CONFLICT"
    LEADERSHIP = "LEADERSHIP"
    BEHAVIORAL = "BEHAVIORAL"
    TRADEOFF = "TRADEOFF"
    IMPROVEMENT = "IMPROVEMENT"
    FUTURE_ENHANCEMENT = "FUTURE_ENHANCEMENT"
    CONCEPTUAL = "CONCEPTUAL"
    SCENARIO = "SCENARIO"

INTENT_STRUCTURE_MAP: Dict[str, str] = {
    QuestionIntent.PROJECT_OVERVIEW: "Problem → Solution → Architecture & Tech → Result",
    QuestionIntent.PROJECT_ROLE: "Responsibility → Hands-on Implementation → Key Milestone",
    QuestionIntent.TECHNICAL_DECISION: "Decision Context → Rationale vs Alternatives → Outcome",
    QuestionIntent.WHY_TECHNOLOGY: "Requirement → Alternatives Evaluated → Why Chosen → Trade-off",
    QuestionIntent.CHALLENGE: "Challenge → Diagnostic Investigation → Action Taken → Result & Learning",
    QuestionIntent.PROBLEM_SOLVING: "Problem Breakdown → Diagnostic Method → Solution Applied → Outcome",
    QuestionIntent.FAILURE: "Incident Context → Root Cause Analysis → Permanent Fix → Prevention",
    QuestionIntent.LEARNING: "Retrospective Reflection → Key Insight → Future Application",
    QuestionIntent.SCALABILITY: "Current Architecture → Bottleneck Analysis → Layered Scaling → Trade-offs",
    QuestionIntent.PERFORMANCE: "Baseline Metric → Profiling & Bottleneck → Optimization → Measured Gain",
    QuestionIntent.DATABASE: "Data Requirements → Schema Design → Indexing/Query Strategy → Consistency",
    QuestionIntent.ARCHITECTURE: "System Overview → Component Contracts → Data Flow → Resilience",
    QuestionIntent.SECURITY: "Threat Model → Security Controls & Sanitization → Verification",
    QuestionIntent.DEBUGGING: "Observed Anomaly → Diagnostic Tooling → Root Cause Fix → Verification",
    QuestionIntent.TEAMWORK: "Collaborative Context → Alignment & Reviews → Shared Success",
    QuestionIntent.CONFLICT: "Technical Disagreement → Data-Driven Evaluation → Consensus → Outcome",
    QuestionIntent.LEADERSHIP: "Opportunity / Initiative → Execution Strategy → Team Enablement → Impact",
    QuestionIntent.BEHAVIORAL: "Situation → Task → Action → Result → Learning",
    QuestionIntent.TRADEOFF: "Design Dilemma → Evaluation Criteria → Chosen Compromise → Mitigation",
    QuestionIntent.IMPROVEMENT: "Current Limitation → Proposed Improvement → Expected Benefit",
    QuestionIntent.FUTURE_ENHANCEMENT: "Next Roadmap Feature → Technical Design → Anticipated Value",
    QuestionIntent.CONCEPTUAL: "Core Definition → Internal Mechanism → Practical Example",
    QuestionIntent.SCENARIO: "Initial Triage & Alerting → Isolation Strategy → Remediation Plan"
}

class QuestionIntentClassifier:
    """Classifies interview questions into 23 distinct intents with specific answer structures."""

    PATTERNS: List[Tuple[str, re.Pattern]] = [
        # Scalability
        (QuestionIntent.SCALABILITY, re.compile(r'\b(?:10x|scale|scaling|scalability|high\s+volume|million\s+requests|horizontal\s+pod|load\s+balancing|traffic\s+spike|10x\s+traffic)\b', re.IGNORECASE)),
        
        # Improvement & Future
        (QuestionIntent.IMPROVEMENT, re.compile(r'\b(?:what\s+would\s+you\s+improve|if\s+you\s+had\s+more\s+time|current\s+limitation|what\s+are\s+the\s+limitations|re-architect|how\s+would\s+you\s+improve)\b', re.IGNORECASE)),
        (QuestionIntent.FUTURE_ENHANCEMENT, re.compile(r'\b(?:next\s+steps?|future\s+enhancement|future\s+roadmap|what\s+features?\s+would\s+you\s+add|upcoming\s+milestone)\b', re.IGNORECASE)),

        # Why Technology
        (QuestionIntent.WHY_TECHNOLOGY, re.compile(r'\b(?:why\s+did\s+you\s+choose|why\s+choose|why\s+select|why\s+\w+\s+for|what\s+is\s+\w+\s+and\s+why\s+did\s+you\s+choose|why\s+not\s+use|over\s+alternatives)\b', re.IGNORECASE)),

        # Challenge & Failure
        (QuestionIntent.CHALLENGE, re.compile(r'\b(?:biggest\s+(?:technical\s+)?challenge|challenging\s+technical|hurdle|obstacle|most\s+difficult|complex\s+issue\s+you\s+faced|challenge\s+you\s+faced)\b', re.IGNORECASE)),
        (QuestionIntent.FAILURE, re.compile(r'\b(?:failure|what\s+went\s+wrong|broke\s+in\s+production|incident|outage|failed\s+deployment|mistake\s+you\s+made)\b', re.IGNORECASE)),
        (QuestionIntent.LEARNING, re.compile(r'\b(?:what\s+did\s+you\s+learn|do\s+differently|key\s+takeaway|lessons?\s+learned)\b', re.IGNORECASE)),

        # Debugging & Performance & Database
        (QuestionIntent.DEBUGGING, re.compile(r'\b(?:debug|debugging|troubleshoot|diagnos(?:e|is)|root\s+cause|fix\s+a\s+bug|stack\s*trace|how\s+you\s+debugged|debugged\s+a\s+difficult)\b', re.IGNORECASE)),
        (QuestionIntent.PERFORMANCE, re.compile(r'\b(?:performance|latency|throughput|optimization|optimize|profiling|memory\s+leak|reflow|bottleneck|speed\s+up|reduce\s+latency)\b', re.IGNORECASE)),
        (QuestionIntent.DATABASE, re.compile(r'\b(?:database|sql|nosql|mongodb|mysql|postgres|indexing|query\s+optimization|schema\s+design|queries\s+in|database\s+schema|normalization|acid|join)\b', re.IGNORECASE)),
        (QuestionIntent.SECURITY, re.compile(r'\b(?:security|authentication|authorization|jwt|oauth|xss|csrf|sql\s+injection|encryption|sanitize|vulnerability)\b', re.IGNORECASE)),
        (QuestionIntent.ARCHITECTURE, re.compile(r'\b(?:architecture|system\s+design|high[- ]level\s+design|components|data\s+flow|microservices|monolith|api\s+contracts?)\b', re.IGNORECASE)),
        (QuestionIntent.TRADEOFF, re.compile(r'\b(?:trade[- ]off|compromise|pros?\s+and\s+cons?|balancing|versus|velocity\s+vs)\b', re.IGNORECASE)),
        (QuestionIntent.TECHNICAL_DECISION, re.compile(r'\b(?:decision|architectural\s+decision|technical\s+choice|why\s+did\s+you\s+architect|how\s+did\s+you\s+use)\b', re.IGNORECASE)),

        # Behavioral & Teamwork & Leadership
        (QuestionIntent.BEHAVIORAL, re.compile(r'\b(?:tell\s+me\s+about\s+a\s+time|describe\s+a\s+situation|tight\s+deadline|prioritiz|handle\s+pressure|star\s+method|deliver\s+under\s+a\s+tight\s+deadline)\b', re.IGNORECASE)),
        (QuestionIntent.CONFLICT, re.compile(r'\b(?:disagreement|conflict|differing\s+opinions?|pushback|convince|disagree)\b', re.IGNORECASE)),
        (QuestionIntent.LEADERSHIP, re.compile(r'\b(?:lead|leadership|initiative|mentoring|ownership|stepped\s+up)\b', re.IGNORECASE)),
        (QuestionIntent.TEAMWORK, re.compile(r'\b(?:teamwork|collaboration|collaborate|working\s+with\s+others|code\s+review|peer\s+review)\b', re.IGNORECASE)),

        # Project Role & Overview
        (QuestionIntent.PROJECT_ROLE, re.compile(r'\b(?:what\s+was\s+your\s+role|your\s+specific\s+responsibility|what\s+did\s+you\s+personally\s+build|key\s+contribution|your\s+role|role\s+and\s+key\s+contribution)\b', re.IGNORECASE)),
        (QuestionIntent.PROJECT_OVERVIEW, re.compile(r'\b(?:tell\s+me\s+about\s+(?:your\s+)?(?:the\s+)?(?:[\w-]+\s+){0,4}project(?:\b|\?|\.|$)|walk\s+me\s+through\s+(?:your\s+)?(?:[\w-]+\s+){0,4}project|overview\s+of\s+(?:your\s+)?(?:[\w-]+\s+){0,4}project|what\s+does\s+(?:your\s+)?(?:[\w-]+\s+){0,4}project\s+do|describe\s+(?:your\s+)?(?:[\w-]+\s+){0,4}project|give\s+me\s+an\s+overview)\b', re.IGNORECASE)),

        # Conceptual & Scenario
        (QuestionIntent.CONCEPTUAL, re.compile(r'\b(?:what\s+is|what\s+are|difference\s+between|explain\s+how|how\s+does\s+[\w\s]+\s+work|under\s+the\s+hood|core\s+concept)\b', re.IGNORECASE)),
        (QuestionIntent.SCENARIO, re.compile(r'\b(?:what\s+would\s+you\s+do\s+if|imagine|suppose|scenario|user\s+reports\s+that)\b', re.IGNORECASE)),
    ]

    @classmethod
    def classify(cls, question_text: str, question_type: str = "Technical", based_on: str = "") -> Tuple[str, str]:
        """
        Classifies the question text into an intent and returns (intent_name, answer_structure).
        """
        q_clean = question_text.strip()
        
        # Match ordered patterns
        for intent, pattern in cls.PATTERNS:
            if pattern.search(q_clean):
                return intent, INTENT_STRUCTURE_MAP.get(intent, "Problem → Solution → Outcome")

        # Fallbacks based on category metadata
        q_type_lower = question_type.lower()
        if "behavioral" in q_type_lower or "hr" in q_type_lower:
            return QuestionIntent.BEHAVIORAL, INTENT_STRUCTURE_MAP[QuestionIntent.BEHAVIORAL]
        if "project" in q_type_lower or "project:" in based_on.lower():
            return QuestionIntent.TECHNICAL_DECISION, INTENT_STRUCTURE_MAP[QuestionIntent.TECHNICAL_DECISION]
        if "conceptual" in q_type_lower or "what is" in q_clean.lower():
            return QuestionIntent.CONCEPTUAL, INTENT_STRUCTURE_MAP[QuestionIntent.CONCEPTUAL]

        return QuestionIntent.TECHNICAL_DECISION, INTENT_STRUCTURE_MAP[QuestionIntent.TECHNICAL_DECISION]
# STAR Diagnostic Scoring Heuristics - Gajapuram Bhavya Sri 
