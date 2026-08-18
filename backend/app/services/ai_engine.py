import re
import hashlib
import json
import logging
import random
import collections
from typing import List, Dict, Any, Optional, Tuple
from backend.app.config import settings
from backend.app.schemas.models import (
    ExtractedResume, JobDescriptionAnalysis, GroundedQuestion,
    AnswerEvaluation, ProjectDeepDive, ResumeImprovementItem,
    TopicPreparationItem, FinalInterviewEvaluation, QuestionEvaluationSummaryItem,
    AnswerGrounding
)
from backend.app.services.grounding_validator import GroundingValidator
from backend.app.services.intent_classifier import QuestionIntentClassifier, QuestionIntent, INTENT_STRUCTURE_MAP
from backend.app.services.diversity_manager import DiversityManager, MockInterviewSessionTracker

logger = logging.getLogger("ai_engine")

class QuestionCatalog:
    """Deterministic, highly grounded question templates linked to specific skills, project roles, and difficulty levels."""
    
    SKILL_QUESTIONS = {
        "Python": {
            "Easy": [
                ("What are the key differences between lists and tuples in Python, and when would you prefer one over the other?",
                 "Tests core data structures and mutability understanding.",
                 ["Tuples are immutable; lists are mutable", "Tuples have lower memory overhead", "Tuples can be used as dictionary keys if hashable"],
                 "Lists are mutable sequences suitable for collections that change, whereas tuples are immutable and memory-efficient. I prefer tuples for fixed data schemas, dictionary keys, and function return values to ensure data integrity."),
                ("How does Python handle memory management and garbage collection?",
                 "Checks awareness of reference counting and cyclic garbage collection in CPython.",
                 ["Reference counting mechanism", "Generational cyclic garbage collector (gc module)", "Memory leaks via circular references"],
                 "Python manages memory primarily through reference counting, where an object's memory is deallocated when its reference count drops to zero. To handle circular references, CPython uses a generational cyclic garbage collector that periodically traverses object graphs."),
            ],
            "Medium": [
                ("How do Python generators and the `yield` keyword optimize memory in data-heavy pipelines?",
                 "Evaluates understanding of lazy evaluation and generator iterators.",
                 ["Generators yield items one by one instead of loading full list in RAM", "State retention between yield calls", "Memory profiling comparison"],
                 "Generators produce items on-demand using the `yield` keyword rather than loading the entire dataset into memory at once. In data pipelines, this lazy evaluation allows processing multi-gigabyte files with a constant memory footprint."),
                ("Explain how Python decorators work under the hood and provide an example use case like logging or authentication.",
                 "Tests first-class function handling and closure concepts.",
                 ["Functions as first-class objects", "Wrapper function around the original function", "Common use cases: caching, RBAC, execution timing"],
                 "Decorators are higher-order functions that take a function as an argument and return an extended wrapper function using closures. I commonly use decorators for cross-cutting concerns like measuring execution time, enforcing role-based access control, and route authentication."),
            ],
            "Hard": [
                ("How does the Global Interpreter Lock (GIL) affect multithreading in CPU-bound vs I/O-bound Python programs?",
                 "Assesses deep concurrency understanding in CPython.",
                 ["GIL prevents multiple native threads from executing Python bytecodes simultaneously", "I/O bound benefits from threading/asyncio", "CPU bound requires multiprocessing"],
                 "The GIL ensures only one native thread executes Python bytecode at a time. For I/O-bound programs, threads release the GIL during network or disk waits, making threading or `asyncio` effective. For CPU-bound tasks, we bypass the GIL using multiprocessing or native C-extensions like NumPy."),
            ]
        },
        "YOLO": {
            "Easy": [
                ("What is YOLOv8 and why would you use it for real-time object detection?",
                 "Evaluates understanding of single-shot computer vision models.",
                 ["Anchor-free detection architecture", "Fast real-time inference with high mAP", "Pre-trained on COCO dataset"],
                 "YOLOv8 is an anchor-free object detection model used to detect and classify objects in real time. I used it because it delivers high accuracy (mAP) with fast inference speeds, making it ideal for live video feeds and traffic monitoring."),
            ],
            "Medium": [
                ("What is the difference between YOLO's single-shot approach and two-stage detectors like Faster R-CNN?",
                 "Tests architectural knowledge of deep learning vision models.",
                 ["Single pass bounding box regression vs region proposal network", "Inference latency comparison", "Speed vs small-object localization trade-offs"],
                 "YOLO performs bounding box regression and classification in a single forward pass across the image grid, achieving real-time inference (>30 FPS). Two-stage detectors like Faster R-CNN first generate region proposals and then classify them, which is slightly more accurate for small objects but significantly slower."),
            ],
            "Hard": [
                ("How do you optimize YOLOv8 inference for production deployment on edge or GPU devices?",
                 "Assesses model export, quantization, and TensorRT acceleration.",
                 ["ONNX and TensorRT export", "FP16 / INT8 quantization", "Batch inference and Non-Maximum Suppression (NMS) tuning"],
                 "We export the trained PyTorch YOLO model to ONNX, optimize the compute graph with TensorRT for INT8/FP16 quantization, and adjust IoU thresholds in Non-Maximum Suppression (NMS) to eliminate redundant boxes while minimizing GPU latency.")
            ]
        },
        "OpenCV": {
            "Easy": [
                ("How did you use OpenCV in your computer vision or image processing pipeline?",
                 "Tests core OpenCV frame processing operations.",
                 ["Frame capture from video stream", "Color conversion and thresholding", "Drawing bounding boxes and tracking IDs"],
                 "I used OpenCV for video stream ingestion (`cv2.VideoCapture`), frame-by-frame preprocessing (grayscale conversion and Gaussian blurring), and drawing real-time bounding boxes and vehicle count statistics on processed frames."),
            ],
            "Medium": [
                ("How do Region of Interest (ROI) masking and morphological operations improve video processing performance in OpenCV?",
                 "Evaluates practical computer vision optimization techniques.",
                 ["Cropping computational frame area", "Morphological opening/closing for noise removal", "Frame skipping and threaded I/O"],
                 "By applying an ROI mask to crop only the active traffic lanes, we reduce the number of pixels passed to downstream inference by over 50%. We also apply morphological transformations to remove sensor noise and isolate moving contours.")
            ]
        },
        "FastAPI": {
            "Easy": [
                ("What are the primary benefits of FastAPI compared to traditional frameworks like Flask or Django?",
                 "Evaluates knowledge of modern asynchronous Python frameworks.",
                 ["Native async/await support with Starlette", "Automatic OpenAPI/Swagger docs generation", "Pydantic validation for request/response bodies"],
                 "FastAPI provides native asynchronous support built on Starlette and Uvicorn, automatic interactive OpenAPI/Swagger documentation, and robust request/response validation using Pydantic type annotations."),
            ],
            "Medium": [
                ("How does FastAPI utilize Pydantic models for request validation and serialization?",
                 "Tests data validation, type hints, and API security.",
                 ["Automatic 422 Unprocessable Entity responses for invalid types", "Serialization to JSON", "Nested models and field validators"],
                 "FastAPI parses incoming JSON bodies against defined Pydantic schemas. If fields are missing or have incorrect data types, it automatically returns structured 422 Unprocessable Entity responses before executing the route handler."),
            ]
        },
        "React": {
            "Easy": [
                ("What is the difference between props and state in React, and how does one-way data flow work?",
                 "Tests foundational component architecture.",
                 ["Props are passed from parent (read-only); state is managed internally", "Unidirectional data flow simplifies debugging", "State updates trigger re-renders"],
                 "Props are immutable data passed down from parent to child components, whereas state is mutable local data managed within a component. React enforces unidirectional data flow, making state changes predictable and easier to debug."),
            ],
            "Medium": [
                ("Explain how `useEffect` works, including its dependency array and cleanup function.",
                 "Evaluates lifecycle management and side-effect handling.",
                 ["Runs after render", "Empty array = run once on mount; with dependencies = run when values change", "Cleanup function runs on unmount or before re-run"],
                 "`useEffect` performs side-effects such as API fetching or event subscriptions. An empty dependency array runs the effect once on mount, specified variables trigger re-execution when changed, and the returned cleanup function cancels subscriptions or timers on unmount."),
            ]
        },
        "CSS": {
            "Easy": [
                ("What is the CSS Box Model, and how does `box-sizing: border-box` change layout calculations?",
                 "Tests core CSS layout mechanics and standard box model calculations.",
                 ["Content, padding, border, and margin layers", "border-box includes padding and border in width/height", "Prevents layout overflow and calculation errors"],
                 "The CSS Box Model consists of content, padding, border, and margin. Under `content-box` (default), padding and border add to the element's declared dimensions, often causing layout overflows. Setting `box-sizing: border-box` ensures the declared width and height include padding and border, making responsive grid and flex layouts predictable."),
            ],
            "Medium": [
                ("How do CSS Grid and Flexbox differ, and when should you choose one over the other?",
                 "Evaluates 1D vs 2D layout architecture.",
                 ["Flexbox is 1D (row or column); Grid is 2D (rows and columns simultaneously)", "Flexbox for component-level alignment; Grid for page-level structural layouts", "Subgrid and gap alignment"],
                 "Flexbox is a 1-dimensional layout model ideal for aligning items along a single axis (such as navigation bars or form controls). CSS Grid is a 2-dimensional system designed for orchestrating complex macro-layouts across rows and columns simultaneously. I use Grid for page scaffolding and dashboard layouts, and Flexbox for micro-components within grid cells."),
                ("Can you explain a key performance or architectural decision you made when working with CSS3?",
                 "Tests rendering performance, reflow/repaint mitigation, and maintainability.",
                 ["Structure modular classes to prevent specificity conflicts", "Use box-sizing: border-box for layout predictability", "Minimize layout reflows and repaints with browser DevTools"],
                 "My resume shows experience with CSS3, although it does not specify a particular performance optimization project. If asked about this in an interview, I would explain that I approach CSS performance by reducing unnecessary selector complexity, establishing 'box-sizing: border-box' across elements for predictable layouts, and testing rendering speed using browser DevTools to prevent expensive layout reflows."),
            ],
            "Hard": [
                ("How does the browser rendering engine process CSS, and how do you prevent costly reflows and repaints?",
                 "Assesses deep understanding of DOM, CSSOM, Render Tree, and compositing layers.",
                 ["DOM + CSSOM = Render Tree", "Reflow (Layout) recalculates geometry; Repaint updates pixels", "Compositing on GPU layers via will-change or transform/opacity"],
                 "The browser constructs the DOM and CSSOM to build the Render Tree, followed by Layout (Reflow), Paint (Repaint), and Compositing. Reflows are computationally expensive because altering geometric properties triggers cascading recalculations across parent and sibling nodes. We prevent reflows by animating composited properties ('transform' and 'opacity') and batching DOM reads and writes.")
            ]
        },
        "CSS3": {
            "Easy": [
                ("What is the CSS Box Model, and how does `box-sizing: border-box` change layout calculations?",
                 "Tests core CSS layout mechanics.",
                 ["Content, padding, border, and margin layers", "border-box includes padding and border", "Layout predictability"],
                 "The CSS Box Model comprises content, padding, border, and margin. Applying `box-sizing: border-box` incorporates padding and border into the specified width and height, preventing accidental element overflow in responsive containers."),
            ],
            "Medium": [
                ("Can you explain a key performance or architectural decision you made when working with CSS3?",
                 "Evaluates rendering performance, reflow/repaint mitigation, and modular styling.",
                 ["Modular class structure", "Box-sizing layout consistency", "Testing with browser DevTools"],
                 "My resume shows experience with CSS3, although it does not detail a standalone CSS performance refactor project. If asked about this in an interview, I would explain that I approach CSS architecture by maintaining low selector specificity to minimize browser style recalculations, using 'box-sizing: border-box' across components for predictable sizing, and testing rendering performance using browser DevTools."),
            ]
        },
        "MongoDB": {
            "Easy": [
                ("What is the primary difference between a relational database and a document database like MongoDB?",
                 "Evaluates schema flexibility vs relational integrity understanding.",
                 ["BSON document model vs rigid tabular schemas", "Horizontal scaling capability", "Flexible schema evolution for nested JSON"],
                 "MongoDB stores data as flexible, hierarchical BSON documents with dynamic schemas, whereas relational databases use rigid tables and columns. MongoDB excels at horizontal scaling and storing nested JSON entities without complex joins."),
            ],
            "Medium": [
                ("How do you decide between embedding vs referencing documents in MongoDB, and what is the 16MB document size limit trade-off?",
                 "Tests schema design and data modeling trade-offs.",
                 ["Embedding for 1:1 and 1:few co-read relationships", "Referencing for 1:many unbounded growth to prevent exceeding 16MB", "Query performance vs update anomalies"],
                 "In MongoDB, I embed data when child entities are tightly coupled and always read together (e.g. addresses on a user), reducing query round-trips. I use referencing (normalization) when relationships are unbounded or updated frequently, ensuring documents never breach the 16MB BSON size limit and avoiding excessive document growth on disk."),
                ("How do compound indexes and the Equality-Sort-Range (ESR) rule optimize query performance in MongoDB?",
                 "Evaluates indexing strategies and query execution plans.",
                 ["Compound indexes across multiple fields", "ESR rule: Equality fields first, Sort fields second, Range fields last", "Covered queries eliminating document fetch from disk"],
                 "Compound indexes allow MongoDB to satisfy multi-field queries using a single B-tree index. We structure compound indexes following the Equality-Sort-Range (ESR) rule: placing exact-match equality filters first, sort keys second, and range filters (like $gt or $lt) last. When all projected fields exist in the index, MongoDB performs a covered query, bypassing disk reads entirely."),
            ],
            "Hard": [
                ("How does MongoDB implement replica set elections, write concerns (`w: 'majority'`), and read preferences?",
                 "Assesses distributed consensus, durability guarantees, and high availability.",
                 ["Raft/Paxos-like consensus algorithm with primary election within seconds", "Write concern w:'majority' and journal persistence (j:true)", "Read preferences (primary, secondaryPreferred) and replication lag trade-offs"],
                 "MongoDB replica sets maintain high availability through automatic failover using an internal consensus protocol. To guarantee durability and prevent rollback anomalies during network partitions, we set write concern to `w: 'majority'` with `j: true`. For read scaling, we use `secondaryPreferred` for latency-sensitive reporting while keeping transactional paths on the primary to avoid dirty reads caused by replication lag.")
            ]
        },
        "SQL": {
            "Easy": [
                ("Explain the differences between INNER JOIN, LEFT JOIN, and FULL OUTER JOIN with examples.",
                 "Evaluates relational algebra and SQL joining fundamentals.",
                 ["INNER JOIN returns matched rows in both", "LEFT JOIN returns all left rows + matching right rows", "NULL handling for unmatched rows"],
                 "An `INNER JOIN` returns only rows that have matching values in both tables. A `LEFT JOIN` returns all records from the left table along with matching rows from the right table (filling unmatched fields with NULL), and a `FULL OUTER JOIN` returns all records when there is a match in either table."),
            ],
            "Medium": [
                ("How do B-tree indexes improve query performance in relational databases, and when might an index degrade performance?",
                 "Tests indexing mechanics, query planning, and write amplification trade-offs.",
                 ["B-tree balanced tree traversal (O(log N) lookup)", "Index seeks vs sequential table scans", "Write overhead during INSERT/UPDATE/DELETE operations"],
                 "B-tree indexes organize column keys in a balanced search tree, allowing the database query optimizer to perform fast O(log N) index seeks instead of scanning millions of rows sequentially. However, every index incurs write amplification because all INSERT, UPDATE, and DELETE operations must update the underlying B-tree structures, so we avoid over-indexing low-cardinality columns."),
                ("What are ACID transactions, and how do database isolation levels balance concurrency against anomalies like dirty reads and phantom reads?",
                 "Evaluates database transaction guarantees and concurrency control.",
                 ["Atomicity, Consistency, Isolation, Durability", "Isolation levels: Read Uncommitted, Read Committed, Repeatable Read, Serializable", "Anomalies: Dirty reads, non-repeatable reads, phantom reads"],
                 "ACID guarantees that database transactions execute reliably. Isolation levels allow engineers to tune the trade-off between concurrency throughput and anomaly protection. `Read Committed` prevents dirty reads by locking modified rows, `Repeatable Read` uses MVCC snapshots to prevent non-repeatable reads, and `Serializable` enforces strict sequential order via two-phase locking or SSI, preventing phantom reads at the cost of concurrency."),
            ],
            "Hard": [
                ("How do you analyze and optimize a slow query using `EXPLAIN ANALYZE` in PostgreSQL or MySQL?",
                 "Assesses query execution plan interpretation and performance tuning.",
                 ["Interpreting sequential scans vs index scans", "Join algorithms (Nested Loop, Hash Join, Merge Join)", "Memory work_mem allocation and disk spillover"],
                 "We run `EXPLAIN (ANALYZE, BUFFERS)` to inspect the actual execution plan, looking for sequential table scans on large datasets, filter predicates discarding high row percentages, and nested loop joins on unbounded data. We resolve bottlenecks by adding composite or covering indexes, rewriting subqueries as Common Table Expressions (CTEs), and adjusting `work_mem` to prevent memory sorts from spilling over to disk.")
            ]
        },
        "Docker": {
            "Easy": [
                ("What is the difference between a Docker image and a Docker container?",
                 "Tests core containerization concepts.",
                 ["Image is a static read-only template; container is a running instance with a writable layer", "Layered filesystem", "Reproducibility across environments"],
                 "A Docker image is an immutable, read-only template containing the application code, runtime, libraries, and dependencies. A Docker container is a runnable, isolated instance of that image with a thin writable layer on top."),
            ],
            "Medium": [
                ("How do multi-stage Docker builds and `.dockerignore` optimize production image size and security?",
                 "Evaluates Docker build performance and image hardening.",
                 ["Separating build toolchain from minimal runtime image (e.g. Alpine/Distroless)", "Shrinking final image size by 70-90%", "Excluding sensitive files and node_modules/.git via .dockerignore"],
                 "Multi-stage builds allow compiling code and installing heavyweight build dependencies in an intermediate builder stage, then copying only the compiled artifacts into a lightweight runtime image (such as Alpine or Distroless). This reduces image size, minimizes the attack surface, and speeds up deployment rollouts."),
            ],
            "Hard": [
                ("How does Docker leverage Linux namespaces and cgroups under the hood to isolate containers?",
                 "Tests OS-level virtualization, kernel primitives, and resource quota enforcement.",
                 ["Linux namespaces for process, network, mount, and IPC isolation (PID, NET, MNT, UTS)", "Control groups (cgroups) for CPU, memory, and I/O rate limiting", "Rootless containers and seccomp syscall filtering"],
                 "Docker isolates containers using Linux kernel primitives: namespaces provide view isolation (PID isolates process trees, NET provides virtual network interfaces, and MNT isolates the filesystem root), while Control Groups (cgroups) enforce hard resource limits on CPU shares, memory caps, and disk I/O to prevent a single noisy container from starving the host system.")
            ]
        },
        "NLP": {
            "Easy": [
                ("How did you use NLP in your project for text processing or keyword extraction?",
                 "Evaluates core Natural Language Processing concepts and text preprocessing.",
                 ["Tokenization and stopword removal", "Named Entity Recognition (NER) for skill/entity extraction", "Vectorization or embeddings"],
                 "In my project, I used NLP for tokenizing raw text, stripping stopwords, and extracting domain entities using spaCy's Named Entity Recognition. We then computed TF-IDF or dense vector embeddings to match extracted skills with target requirements."),
            ],
            "Medium": [
                ("What is the difference between traditional TF-IDF keyword extraction and dense semantic embeddings like BERT/Word2Vec?",
                 "Tests understanding of sparse lexical matching vs dense semantic representations.",
                 ["TF-IDF is sparse frequency-based (exact keyword match)", "Dense embeddings capture semantic context and synonyms", "Cosine similarity calculation and computational trade-offs"],
                 "TF-IDF produces sparse frequency-inverse document frequency vectors that excel at exact keyword matching but fail on synonyms or context. Dense embeddings (like BERT or Word2Vec) project words into continuous semantic vector spaces where cosine similarity captures contextual meaning regardless of exact wording."),
            ],
            "Hard": [
                ("How do transformer attention mechanisms improve on recurrent architectures (RNN/LSTM) for long-document understanding?",
                 "Assesses deep understanding of self-attention and modern NLP architectures.",
                 ["Self-attention enables O(1) path length across distant tokens", "Elimination of sequential bottleneck allows full GPU parallelization", "Quadratic computational complexity and chunking strategies"],
                 "Transformers replace sequential recurrence with multi-head self-attention, allowing every token to attend directly to all other tokens in parallel. This eliminates the vanishing gradient and information bottlenecks of LSTMs on long contexts, while enabling full GPU compute parallelization during training and inference.")
            ]
        },
        "Machine Learning": {
            "Easy": [
                ("What is the difference between supervised and unsupervised learning, with practical examples?",
                 "Evaluates foundational machine learning paradigm comprehension.",
                 ["Supervised uses labeled target data (classification/regression)", "Unsupervised discovers latent patterns without labels (clustering/PCA)", "Evaluation metrics difference"],
                 "Supervised learning trains on labeled input-output pairs to predict continuous values or categorical classes. Unsupervised learning analyzes unlabeled datasets to identify inherent groupings, clusters (like K-Means), or reduce dimensionality without predefined target labels."),
            ],
            "Medium": [
                ("How do you detect and prevent overfitting in machine learning models?",
                 "Tests cross-validation, regularization, and model validation practices.",
                 ["Train vs validation loss divergence", "L1/L2 regularization and dropout", "K-fold cross-validation and feature selection"],
                 "We detect overfitting when training loss continues decreasing while validation error rises. We prevent it by applying K-fold cross-validation, L1/L2 regularization, early stopping, pruning decision trees or adding dropout, and expanding training data with augmentation."),
            ]
        },
        "JavaScript": {
            "Easy": [
                ("Explain the difference between `var`, `let`, and `const`, and how block scoping works.",
                 "Tests core JavaScript scoping and variable declarations.",
                 ["`var` is function-scoped and hoisted; `let` and `const` are block-scoped", "`const` prevents reassignment", "Temporal Dead Zone (TDZ)"],
                 "`var` is function-scoped and hoisted to the top of its execution context, often leading to subtle bugs. `let` and `const` are block-scoped within curly braces `{}` and reside in the Temporal Dead Zone until declared. `const` additionally enforces reference immutability."),
            ],
            "Medium": [
                ("How does the JavaScript Event Loop handle microtasks (Promises) vs macrotasks (setTimeout)?",
                 "Evaluates deep asynchronous runtime execution model understanding.",
                 ["Call stack execution -> Microtask queue drain -> Macrotask queue", "Promises and `queueMicrotask` run before the next render/macrotask", "`setTimeout` and I/O callbacks run in subsequent macrotask ticks"],
                 "The event loop continuously monitors the call stack. When synchronous code finishes, it drains all pending microtasks (Promises, MutationObservers) before picking the next macrotask (setTimeout, setInterval, I/O) from the task queue, ensuring Promise resolutions execute immediately within the current turn.")
            ]
        },
        "Node.js": {
            "Easy": [
                ("What makes Node.js non-blocking and how does it handle high-concurrency I/O?",
                 "Evaluates Node.js runtime and asynchronous event-driven model.",
                 ["Single-threaded event loop powered by libuv", "Non-blocking asynchronous I/O delegates to OS worker threads", "Event emitters and callback/Promise architecture"],
                 "Node.js uses a single-threaded event loop powered by libuv to handle requests asynchronously. When performing I/O (file, network, DB), it offloads the operation to kernel subsystems or libuv worker threads, immediately freeing the main thread to process subsequent requests without blocking."),
            ],
            "Medium": [
                ("How do Streams in Node.js prevent memory bottlenecks when processing large files?",
                 "Tests streaming data handling and backpressure.",
                 ["Reading and processing data in small chunks (buffers)", "Piping readable to writable streams", "Managing backpressure to prevent buffer overflows"],
                 "Streams process data sequentially in small chunks rather than buffering the entire payload into RAM at once. Using `stream.pipe()`, Node.js handles data transfer with built-in backpressure management, keeping memory usage constant even when processing multi-gigabyte files.")
            ]
        },
        "AWS": {
            "Easy": [
                ("What is the difference between AWS EC2, S3, and Lambda, and when would you use each?",
                 "Tests fundamental cloud compute, storage, and serverless architectures.",
                 ["EC2 is virtual server compute; S3 is object storage; Lambda is event-driven serverless", "Cost and scaling models", "Appropriate use cases for each service"],
                 "EC2 provides scalable virtual server instances for long-running workloads, S3 is highly durable object storage for static assets and blobs, and AWS Lambda provides event-driven serverless compute that executes code on-demand without provisioning servers, scaling automatically per request."),
            ],
            "Medium": [
                ("How do you architect a highly available, secure web application on AWS?",
                 "Evaluates cloud architecture, VPC design, and fault tolerance.",
                 ["Multi-AZ deployments behind Application Load Balancer (ALB)", "Auto Scaling Groups (ASG) and RDS multi-AZ replicas", "VPC private subnets, security groups, and IAM least-privilege policies"],
                 "We deploy stateless application servers across multiple Availability Zones (Multi-AZ) behind an Application Load Balancer with Auto Scaling Groups. Database storage uses RDS with Multi-AZ automated failover and read replicas. All backend instances reside in private VPC subnets with strict security group ingress rules and IAM least-privilege execution roles.")
            ]
        }
    }

    BEHAVIORAL_QUESTIONS = [
        ("Tell me about a challenging technical hurdle you faced in one of your projects and how you diagnosed and resolved it.",
         "Project Experience",
         "Evaluates problem-solving methodology, debugging persistence, and ownership.",
         ["Clearly define the problem", "Explain diagnostic steps and tools used", "Describe the solution and measurable outcome", "What you learned"],
         "In my project, we experienced processing latency during high request volume. I profiled execution bottlenecks, identified that synchronous file operations were blocking request handling, and resolved it by converting operations to asynchronous background tasks, restoring fast response times."),
        ("Describe a situation where you had to quickly learn a new framework or technology to deliver a project feature.",
         "Adaptability & Learning",
         "Assesses continuous learning, agility, and time management.",
         ["Context of the project requirement", "Systematic approach to learning (docs, tutorials, prototyping)", "Timely execution and quality delivery"],
         "When a project required adopting a new library, I studied official documentation and built isolated proof-of-concept prototypes to understand core APIs and edge cases, successfully integrating the feature on schedule.")
    ]

    PROJECT_TEMPLATES = [
        ("What is {tech} and why did you choose it in your '{title}' project?",
         "Project: {title}",
         "Tests core technology selection, architectural trade-offs, and practical application in your project.",
         ["Core mechanism and role of {tech}", "Why {tech} was selected over alternatives", "Role in workflow and practical benefit", "Production outcome in '{title}'"],
         "In '{title}', {tech} was selected as the core technology for its reliability, strong developer ecosystem, and direct fit for our project requirements. In our implementation, {tech} handled request processing, data transformation, and core domain logic. The key trade-off was balancing development velocity with runtime efficiency, which we managed by establishing structured validation models and isolating compute tasks."),
        ("How did you use {tech} in your '{title}' project?",
         "Project: {title}",
         "Evaluates hands-on implementation details, pipeline design, and framework usage.",
         ["Pipeline and architecture integration", "Data flow and request handling", "Validation and output handling", "Error recovery"],
         "In '{title}', I integrated {tech} to drive the core processing pipeline. It was responsible for ingesting input data, executing validation and business logic, and outputting formatted results. To ensure maintainability, I implemented structured schemas and modular handlers to keep data transformations clean and testable."),
        ("What was the primary architectural trade-off you made in '{title}' when selecting {tech}?",
         "Project: {title}",
         "Tests architectural justification, engineering trade-offs, and decision making in real projects.",
         ["Why {tech} was selected over alternatives", "Performance or scalability implications", "Challenges encountered", "Mitigation strategy"],
         "When building '{title}', the primary architectural trade-off was balancing rapid implementation with scalable design. Choosing {tech} gave us clean abstractions and strong library support, but required careful attention to data structures and resource usage. We addressed this by profiling key execution paths and modularizing components to prevent performance bottlenecks."),
        ("If '{title}' were to experience a 10x increase in volume, how would you scale your {tech} implementation?",
         "Project: {title}",
         "Assesses system design, bottleneck diagnosis, query optimization, and structured scaling.",
         ["Identify bottlenecks through monitoring and profiling", "Optimize database indexing and execution plans", "Introduce connection pooling and caching where appropriate", "Consider read replicas or horizontal scaling if read-heavy"],
         "For a 10x increase in volume in '{title}', my approach would be to first identify the primary bottleneck by profiling system metrics and execution times. For data access, I would optimize indexes and query execution plans to minimize full table scans, and introduce connection pooling to manage concurrent client traffic. If read traffic becomes the bottleneck, I would evaluate caching frequently queried read paths and consider read replicas. Since my background in '{title}' involved {tech}, I would apply these scaling optimizations based on measured application constraints rather than adding premature complexity.")
    ]


class AIEngine:
    @staticmethod
    def _generate_hash(text: str) -> str:
        return hashlib.md5(text.strip().lower().encode("utf-8")).hexdigest()

    @classmethod
    async def generate_questions(
        cls,
        resume: ExtractedResume,
        jd: Optional[JobDescriptionAnalysis] = None,
        difficulty: str = "Medium",
        question_type: str = "Mixed",
        count: int = 5,
        exclude_hashes: Optional[List[str]] = None
    ) -> List[GroundedQuestion]:
        """Generates strictly grounded, explainable questions with claim validation and anti-hallucination guarantees."""
        exclude_set = set(exclude_hashes or [])
        generated: List[GroundedQuestion] = []

        # Candidate's extracted entities
        skills = resume.skills if resume.skills else ["Python", "SQL", "React", "FastAPI"]
        projects = resume.projects if resume.projects else [
            type("Proj", (), {"title": "Full-Stack Web App", "technologies": skills[:3], "highlights": ["Built REST APIs"]})()
        ]
        experience = resume.experience if resume.experience else []

        # Target JD skills
        jd_skills = jd.technologies if jd and jd.technologies else []

        # 1. Check if Gemini / LLM is configured
        if settings.GEMINI_API_KEY:
            try:
                llm_questions = await cls._generate_with_gemini(
                    resume=resume,
                    jd=jd,
                    difficulty=difficulty,
                    question_type=question_type,
                    count=count,
                    exclude_hashes=list(exclude_set)
                )
                if llm_questions and len(llm_questions) >= 1:
                    for q in llm_questions:
                        q_hash = cls._generate_hash(q.question)
                        if q_hash not in exclude_set:
                            generated.append(q)
                            exclude_set.add(q_hash)
            except Exception as e:
                logger.warning(f"Gemini generation fallback to grounded catalog: {e}")

        # 2. Deterministic Grounded Catalog Generation (Guaranteed grounded & duplicate-free)
        if len(generated) < count:
            candidate_pool: List[Tuple[str, str, str, str, str, str, List[str], str]] = []

            # (a) Project Based questions
            for p in projects:
                p_tech = p.technologies if p.technologies else skills[:2]
                main_tech = p_tech[0] if p_tech else "Architecture"
                for tmpl, based_tmpl, why, pts, sample_tmpl in QuestionCatalog.PROJECT_TEMPLATES:
                    q_text = tmpl.format(title=p.title, tech=main_tech)
                    b_text = based_tmpl.format(title=p.title)
                    pts_formatted = [pt.format(title=p.title, tech=main_tech) for pt in pts]
                    sample_formatted = sample_tmpl.format(title=p.title, tech=main_tech)
                    candidate_pool.append((
                        q_text,
                        b_text,
                        main_tech,
                        difficulty,
                        "Project Based",
                        why,
                        pts_formatted,
                        sample_formatted
                    ))

            # (b) Technical & Resume Based questions
            for skill in skills:
                skill_catalog = QuestionCatalog.SKILL_QUESTIONS.get(skill)
                if not skill_catalog:
                    # Find matching root
                    for k, v in QuestionCatalog.SKILL_QUESTIONS.items():
                        if k.lower() in skill.lower() or skill.lower() in k.lower():
                            skill_catalog = v
                            break

                if skill_catalog:
                    diff_list = skill_catalog.get(difficulty) or skill_catalog.get("Medium", [])
                    for entry in diff_list:
                        q_text = entry[0]
                        why = entry[1]
                        pts = entry[2]
                        sample = entry[3] if len(entry) > 3 else f"A strong answer for {skill} covers {pts[0]} and practical trade-offs."
                        candidate_pool.append((
                            q_text,
                            f"Resume Skill: {skill}",
                            skill,
                            difficulty,
                            "Technical",
                            why,
                            pts,
                            sample
                        ))

            # (c) JD Based questions
            if jd and jd.required_skills:
                for jd_s in jd.required_skills[:4]:
                    in_resume = any(jd_s.lower() == s.lower() for s in skills)
                    based = f"JD Requirement: {jd_s} (Present in Resume)" if in_resume else f"JD Target Skill: {jd_s} (Job Requirement)"
                    jd_sample = f"To address {jd_s}, I explain core principles, describe relevant background from my listed skills, and structure my answer around production best practices."
                    candidate_pool.append((
                        f"The target job requires solid experience with {jd_s}. How have you applied {jd_s} in your projects, or how would you ramp up?",
                        based,
                        jd_s,
                        difficulty,
                        "Job Description Based",
                        f"Directly assesses qualification for the key required skill '{jd_s}' in the job description.",
                        [f"Core understanding of {jd_s}", f"Practical project application or learning plan", "Best practices"],
                        jd_sample
                    ))

            # (d) Behavioral & Situational
            for q_text, topic, why, pts, sample in QuestionCatalog.BEHAVIORAL_QUESTIONS:
                candidate_pool.append((
                    q_text,
                    f"Candidate Experience: {topic}",
                    "Soft Skills & Communication",
                    difficulty,
                    "Behavioral",
                    why,
                    pts,
                    sample
                ))

            # Filter by requested question_type if specified and not 'Mixed'
            if question_type != "Mixed":
                type_filtered = [c for c in candidate_pool if c[4].lower() == question_type.lower() or question_type.lower() in c[4].lower()]
                if type_filtered:
                    candidate_pool = type_filtered

            # Shuffle candidate pool with deterministic seed variation
            random.shuffle(candidate_pool)

            for item in candidate_pool:
                q_text, based, skill, diff, q_type, why, pts, sample = item
                q_hash = cls._generate_hash(q_text)
                if q_hash not in exclude_set:
                    exclude_set.add(q_hash)
                    generated.append(GroundedQuestion(
                        question=q_text,
                        based_on=based,
                        skill=skill,
                        difficulty=diff,
                        question_type=q_type,
                        why_this_question=why,
                        expected_answer_points=pts,
                        sample_answer=sample
                    ))
                if len(generated) >= count:
                    break

            # Fallback if pool exhausted
            if len(generated) < count:
                for i in range(count - len(generated)):
                    tech = skills[i % len(skills)] if skills else "Web Development"
                    q_text = f"Can you explain a key performance or architectural decision you made when working with {tech}?"
                    q_hash = cls._generate_hash(q_text + str(i))
                    if q_hash not in exclude_set:
                        exclude_set.add(q_hash)
                        generated.append(GroundedQuestion(
                            question=q_text,
                            based_on=f"Resume Skill: {tech}",
                            skill=tech,
                            difficulty=difficulty,
                            question_type="Technical",
                            why_this_question=f"Tests practical design and trade-off evaluation in {tech}.",
                            expected_answer_points=["Clear problem statement", f"Why {tech} was applied", "Measurable result"],
                            sample_answer=f"When working with {tech}, my approach focuses on understanding core performance trade-offs and applying structured modular patterns."
                        ))

        # 3. Comprehensive Validation & Grounding Enforcement
        finalized_questions: List[GroundedQuestion] = []
        for q in generated[:count]:
            q.resume_id = getattr(resume, "id", None)
            q.resume_hash = getattr(resume, "resume_hash", None)
            final_ans, grounding = GroundingValidator.validate_and_ground_answer(
                question_text=q.question,
                answer_text=q.sample_answer or "",
                skill=q.skill,
                based_on=q.based_on,
                question_type=q.question_type,
                difficulty=q.difficulty,
                resume=resume,
                jd=jd
            )
            q.sample_answer = final_ans
            q.answer_grounding = grounding
            finalized_questions.append(q)

        return finalized_questions

    @classmethod
    async def _generate_with_gemini(
        cls,
        resume: ExtractedResume,
        jd: Optional[JobDescriptionAnalysis],
        difficulty: str,
        question_type: str,
        count: int,
        exclude_hashes: List[str]
    ) -> List[GroundedQuestion]:
        """Calls Google Gemini API with strict anti-hallucination rules and candidate evidence grounding."""
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = f"""You are an expert technical interviewer assistant.
Your job is to generate exactly {count} interview questions and realistic suggested answers based ONLY on the candidate's verified resume evidence.

CANDIDATE RESUME EVIDENCE:
Candidate Name: {resume.name}
Verified Skills: {', '.join(resume.skills) if resume.skills else 'None specified'}
Verified Projects: {', '.join([f"{p.title} (Technologies: {', '.join(p.technologies)})" for p in resume.projects]) if resume.projects else 'None specified'}
Verified Work Experience: {', '.join([f"{e.role} at {e.company} (Technologies: {', '.join(e.technologies)})" for e in resume.experience]) if resume.experience else 'None specified'}

TARGET JOB DESCRIPTION:
Title: {jd.title if jd else "Software Developer"}
Target Required Skills: {', '.join(jd.required_skills) if jd else "General Engineering Stack"}

CRITICAL GROUNDING RULES:
1. NEVER fabricate candidate experience.
2. NEVER claim the candidate implemented a technology, tool, library, or framework unless that technology is explicitly supported by the resume.
3. NEVER invent projects, companies, responsibilities, performance metrics (e.g. "reduced latency by 40%"), achievements, or technical decisions not present in the resume.
4. A listed skill DOES NOT automatically mean professional production experience.
5. For hypothetical technical/scenario questions (e.g., "How would you scale X for 10x traffic?"), use conditional phrasing: "I would...", "My approach would be...", "I would consider...". Do NOT say "I implemented Redis/Kafka/HPA..." unless those technologies are in the resume.
6. For behavioral or experience-based questions, reference only actual verified resume projects or experiences.
7. If the resume only mentions a skill (e.g. CSS3) without project details, state: "My resume highlights experience with CSS3, although it does not detail a specific optimization project. If asked in an interview, I would explain that I approach..."
8. Make suggested answers natural, conversational, technically accurate, 4-6 sentences long, and easy for a student/candidate to explain. Avoid gratuitous buzzwords.
9. Use the Job Description ONLY to understand relevance. Do NOT treat JD requirements as candidate evidence.
10. Do not repeat any of these question hashes: {', '.join(exclude_hashes[:10]) if exclude_hashes else 'None'}

Output valid JSON only: a JSON array of objects with keys:
  "question": string,
  "based_on": string (e.g. "Project: XYZ" or "Resume Skill: ABC"),
  "skill": string,
  "difficulty": "{difficulty}",
  "question_type": "{question_type}",
  "why_this_question": string,
  "expected_answer_points": list of strings (3-4 concise points),
  "sample_answer": string (realistic, grounded model answer)

JSON Output:"""

        response = None
        for m_name in ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']:
            try:
                response = client.models.generate_content(
                    model=m_name,
                    contents=prompt,
                )
                if response and response.text:
                    break
            except Exception as e:
                logger.debug(f"Gemini {m_name} failed in question generation: {e}")
                continue

        if not response or not response.text:
            raise RuntimeError("Gemini model generation returned empty response")

        text = response.text.strip()
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0].strip()
        elif text.startswith("```"):
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)
        results = []
        for item in data:
            results.append(GroundedQuestion(
                question=item.get("question", ""),
                based_on=item.get("based_on", f"Resume Skill: {item.get('skill', 'General')}"),
                skill=item.get("skill", "General"),
                difficulty=item.get("difficulty", difficulty),
                question_type=item.get("question_type", question_type),
                why_this_question=item.get("why_this_question", "Tests core technical domain understanding."),
                expected_answer_points=item.get("expected_answer_points", []),
                sample_answer=item.get("sample_answer", "")
            ))
        return results

    @classmethod
    async def evaluate_answer(
        cls,
        question_id: str,
        question_text: str,
        based_on: str,
        skill: str,
        difficulty: str,
        user_answer: str,
        expected_points: Optional[List[str]] = None,
        sample_answer: Optional[str] = None,
        session_id: str = "default",
        resume_data: Optional[ExtractedResume] = None,
        jd_data: Optional[JobDescriptionAnalysis] = None,
        question_intent: Optional[str] = None,
        question_attempt_id: Optional[str] = None
    ) -> AnswerEvaluation:
        """Deep, rigorous evaluation of a candidate's answer across 6 criteria with question-intent classification, anti-repetition diversity, STAR analysis, and grounding validation."""
        cleaned_answer = user_answer.strip()
        lower_ans = cleaned_answer.lower()
        words = lower_ans.split()
        word_count = len(words)

        # -------------------------------------------------------------
        # 0. INTENT CLASSIFICATION & DIVERSE GROUNDED MODEL ANSWER
        # -------------------------------------------------------------
        detected_intent, answer_structure = QuestionIntentClassifier.classify(question_text, based_on=based_on)
        if question_intent:
            detected_intent = question_intent

        diverse_model_ans, detected_intent, answer_structure, rel_verdict = DiversityManager.generate_diverse_grounded_answer(
            question_text=question_text,
            skill=skill,
            based_on=based_on,
            difficulty=difficulty,
            resume=resume_data,
            jd=jd_data,
            session_id=session_id
        )

        # -------------------------------------------------------------
        # 1. SPAM / REPETITION / TRIVIAL / QUESTION ECHO DETECTION (Score 0)
        # -------------------------------------------------------------
        is_spam_or_empty = False
        spam_reason = ""

        if word_count < 4 or len(cleaned_answer) == 0:
            is_spam_or_empty = True
            spam_reason = "No answer or insufficient text was submitted."
        elif word_count >= 12:
            # Check unique word ratio (detects looped copy-pasted sentences)
            unique_words = set(words)
            unique_ratio = len(unique_words) / word_count
            if unique_ratio < 0.28:
                is_spam_or_empty = True
                spam_reason = "The submission contains looped, repeated sentences or copy-pasted text without an original technical explanation."

            # Check repeated sentence patterns (3+ repeats of sentence with >= 4 words)
            sentences = [s.strip() for s in re.split(r'[.!?\n]+', lower_ans) if len(s.strip().split()) >= 4]
            if len(sentences) >= 3:
                counts = collections.Counter(sentences)
                most_common_s, freq = counts.most_common(1)[0]
                repeated_words = freq * len(most_common_s.split())
                if freq >= 3 and (repeated_words / word_count) >= 0.45:
                    is_spam_or_empty = True
                    spam_reason = "The answer repeats the same sentence multiple times rather than providing a structured technical answer."

            # Check if user just echoed/repeated the question text back (including speech dictation repeats)
            stopwords_echo = {
                "the", "a", "an", "and", "or", "to", "for", "in", "on", "of", "at", "by", "with", "from",
                "as", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
                "can", "could", "should", "would", "will", "shall", "may", "might", "must", "what", "how", "why",
                "when", "which", "who", "whom", "where", "your", "you", "our", "my", "their", "his", "her", "its",
                "about", "this", "that", "these", "those"
            }
            q_clean = re.sub(r'[^a-z0-9\s]', ' ', question_text.lower())
            q_word_set = set(w for w in q_clean.split() if len(w) > 3 and w not in stopwords_echo)
            a_clean = re.sub(r'[^a-z0-9\s]', ' ', lower_ans)
            a_word_set = set(w for w in a_clean.split() if len(w) > 3 and w not in stopwords_echo)
            
            if len(a_word_set) >= 3 and len(q_word_set) >= 3:
                # Check overlap ratio
                matched_echo = sum(1 for w in a_word_set if any(w in qw or qw in w for qw in q_word_set))
                echo_ratio = matched_echo / max(1, len(a_word_set))
                non_echo_words = [w for w in a_word_set if not any(w in qw or qw in w for qw in q_word_set) and w not in ["submitting", "submit", "test", "answering", "answer"]]
                if (echo_ratio >= 0.65 and len(non_echo_words) <= 2) or (len(a_word_set) >= 4 and len(a_word_set - q_word_set) <= 1):
                    is_spam_or_empty = True
                    spam_reason = "The submission merely echoes or repeats the question text without providing an original answer."

        if is_spam_or_empty:
            concrete_model_ans, grounding_meta = GroundingValidator.validate_and_ground_answer(
                question_text=question_text,
                answer_text=diverse_model_ans,
                skill=skill,
                based_on=based_on,
                question_type="Technical",
                difficulty=difficulty,
                resume=resume_data,
                jd=jd_data
            )
            return AnswerEvaluation(
                question_id=question_id,
                question_attempt_id=question_attempt_id,
                session_id=session_id,
                overall_score=0,
                relevance_score=0,
                technical_accuracy_score=0,
                completeness_score=0,
                clarity_score=0,
                confidence_score=0,
                communication_score=0,
                verdict_rating="No Answer Provided" if word_count < 4 else "Irrelevant / Repetitive Input",
                question_intent=detected_intent,
                answer_structure=answer_structure,
                relevance_verdict="IRRELEVANT",
                concepts_covered=[],
                concepts_missed=expected_points or [f"{skill} core mechanism", "Production trade-offs", "Concrete implementation"],
                strengths=["No valid technical response was submitted."],
                weaknesses=[
                    f"The answer provided does not explain {skill} or answer the question asked.",
                    spam_reason or "Type or dictate a structured technical explanation to receive a detailed evaluation."
                ],
                improved_answer=concrete_model_ans,
                follow_up_question=f"Can you walk me through a specific code or architecture example where you worked with {skill}?",
                next_recommended_difficulty="Easy",
                feedback_summary=f"Invalid or repetitive input detected (0/100). {spam_reason}",
                star_feedback={
                    "situation": "Missing — Provide real-world context or problem statement.",
                    "task": "Missing — Specify the technical challenge.",
                    "action": "Missing — Describe the specific tools, algorithms, and design choices.",
                    "result": "Missing — Highlight performance improvements or business outcome."
                },
                answer_grounding=grounding_meta
            )

        # -------------------------------------------------------------
        # 2. LLM Evaluation (Gemini API) if configured
        # -------------------------------------------------------------
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                prompt = f"""You are a Principal Engineer and rigorous technical interviewer at a top tech company.
Evaluate this candidate's interview answer accurately, constructively, and without grade inflation.

STRICT ZERO / LOW-SCORE POLICY:
- If the candidate's answer is empty, repetitive spam, looped text, or completely irrelevant to the question asked about '{skill}' (e.g. talking about algorithms/data pipelines when asked about React or CSS3), score overall_score <= 15 and relevance <= 15 with verdict 'Off-Topic / Domain Mismatch' or 'Irrelevant / Random Input'.
- If the candidate provided a genuine, relevant technical explanation answering the question about '{skill}', evaluate fairly on technical accuracy, completeness, and clarity (scores 50-95).
- Every 'improved_answer' MUST be a realistic, senior-engineer first-person spoken response (4-6 sentences) answering the question directly as spoken in an interview.

INTERVIEW CONTEXT:
Question: "{question_text}"
Grounding Context: {based_on}
Target Domain/Skill: {skill}
Difficulty Level: {difficulty}
Expected Key Points: {', '.join(expected_points) if expected_points else 'Standard production best practices, mechanics, trade-offs'}

CANDIDATE ANSWER:
"{cleaned_answer}"

REQUIRED JSON OUTPUT FORMAT:
{{
  "overall_score": int (0-100),
  "relevance_score": int (0-100),
  "technical_accuracy_score": int (0-100),
  "completeness_score": int (0-100),
  "clarity_score": int (0-100),
  "confidence_score": int (0-100),
  "communication_score": int (0-100),
  "verdict_rating": "Exceptional" | "Strong Technical Answer" | "Adequate with Gaps" | "Needs Technical Depth" | "Off-Topic / Domain Mismatch" | "Irrelevant / Random Input" | "No Answer Provided",
  "concepts_covered": ["List of 2-4 specific technical concepts the candidate correctly mentioned"],
  "concepts_missed": ["List of 2-4 critical technical concepts or trade-offs the candidate omitted"],
  "strengths": ["2-3 specific, evidence-based strengths of their answer"],
  "weaknesses": ["2-3 actionable, technical points where the answer fell short"],
  "improved_answer": "A detailed, first-person senior-engineer response (4-6 sentences) directly answering the question with mechanisms, choices, and measurable results.",
  "follow_up_question": "A sharp, realistic follow-up question the interviewer would ask next.",
  "next_recommended_difficulty": "Easy" | "Medium" | "Hard" | "Expert",
  "feedback_summary": "1-2 sentence concise executive summary of the evaluation.",
  "star_feedback": {{
    "situation": "Brief assessment of context provided",
    "task": "Brief assessment of challenge stated",
    "action": "Brief assessment of technical implementation described",
    "result": "Brief assessment of outcome or metrics highlighted"
  }}
}}"""

                response = None
                for m_name in ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']:
                    try:
                        response = client.models.generate_content(
                            model=m_name,
                            contents=prompt
                        )
                        if response and response.text:
                            break
                    except Exception as e:
                        logger.debug(f"Gemini {m_name} failed in evaluation: {e}")
                        continue

                if not response or not response.text:
                    raise RuntimeError("Gemini model evaluation returned empty response")

                text = response.text.strip()
                if text.startswith("```json"):
                    text = text.split("```json")[1].split("```")[0].strip()
                elif text.startswith("```"):
                    text = text.split("```")[1].split("```")[0].strip()

                data = json.loads(text)
                raw_overall = int(data.get("overall_score", 0))
                verdict = data.get("verdict_rating", "Needs Technical Depth")

                if raw_overall <= 15 or "irrelevant" in verdict.lower() or "random" in verdict.lower() or "off-topic" in verdict.lower():
                    if raw_overall <= 10:
                        raw_overall = 0
                        rel_s = 0
                        tech_s = 0
                        comp_s = 0
                        clar_s = 0
                        conf_s = 0
                        comm_s = 0
                        verdict = "Irrelevant / Random Input"
                    else:
                        rel_s = int(data.get("relevance_score", 15))
                        tech_s = int(data.get("technical_accuracy_score", 10))
                        comp_s = int(data.get("completeness_score", 15))
                        clar_s = int(data.get("clarity_score", 55))
                        conf_s = int(data.get("confidence_score", 50))
                        comm_s = int(data.get("communication_score", 50))
                else:
                    rel_s = int(data.get("relevance_score", data.get("relevance", raw_overall)))
                    tech_s = int(data.get("technical_accuracy_score", data.get("technical_score", data.get("technical_accuracy", raw_overall))))
                    comp_s = int(data.get("completeness_score", data.get("completeness", raw_overall)))
                    clar_s = int(data.get("clarity_score", data.get("clarity", max(70, raw_overall))))
                    conf_s = int(data.get("confidence_score", data.get("confidence", max(70, raw_overall))))
                    comm_s = int(data.get("communication_score", data.get("communication", max(70, raw_overall))))

                if raw_overall <= 0 and (rel_s > 0 or tech_s > 0):
                    raw_overall = int((rel_s * 0.30) + (tech_s * 0.30) + (comp_s * 0.20) + (clar_s * 0.08) + (conf_s * 0.06) + (comm_s * 0.06))

                return AnswerEvaluation(
                    question_id=question_id,
                    question_attempt_id=question_attempt_id,
                    session_id=session_id,
                    overall_score=raw_overall,
                    relevance_score=rel_s,
                    technical_accuracy_score=tech_s,
                    completeness_score=comp_s,
                    clarity_score=clar_s,
                    confidence_score=conf_s,
                    communication_score=comm_s,
                    verdict_rating=verdict,
                    concepts_covered=data.get("concepts_covered", []),
                    concepts_missed=data.get("concepts_missed", []),
                    strengths=data.get("strengths", ["Clear technical terminology."]),
                    weaknesses=data.get("weaknesses", ["Expand on trade-offs and quantifiable impact."]),
                    improved_answer=data.get("improved_answer", f"In our project, we utilized {skill} to optimize core architecture and maintain high reliability."),
                    follow_up_question=data.get("follow_up_question", f"How would you optimize this {skill} implementation under heavy concurrent load?"),
                    next_recommended_difficulty=data.get("next_recommended_difficulty", "Medium"),
                    feedback_summary=data.get("feedback_summary", f"Evaluation complete: {raw_overall}/100."),
                    star_feedback=data.get("star_feedback")
                )
            except Exception as e:
                logger.warning(f"Gemini evaluation fallback to advanced deterministic engine: {e}")

        # -------------------------------------------------------------
        # 3. ADVANCED DETERMINISTIC SEMANTIC EVALUATION ENGINE (20+ Engineering Domains)
        # -------------------------------------------------------------
        TECHNICAL_DOMAINS = {
            "nlp": {
                "aliases": ["nlp", "natural language processing", "spacy", "nltk", "transformers", "bert", "huggingface", "llm", "text processing", "tokenization", "embeddings", "sentiment analysis", "named entity recognition", "ner", "tf-idf", "tfidf", "word2vec"],
                "keywords": ["nlp", "spacy", "nltk", "bert", "transformer", "tokenization", "tokens", "stopwords", "lemmatization", "stemming", "ner", "named entity", "tf-idf", "tfidf", "word2vec", "embeddings", "cosine similarity", "sentiment", "attention", "pos tagging", "vectorizer", "classification", "corpus", "intent", "fine-tuning", "llm", "prompt", "chunking", "parsing"],
                "concept_rules": [
                    ("Tokenization & Text Preprocessing (spaCy / NLTK)", r'\b(?:tokeniz(?:ation|e|er|ing)|lemmatiz(?:ation|e)|stemm(?:ing|er)|stop\s*words?|lower\s*casing|corpus|pos\s*tagg(?:ing|ed)|preprocessing)\b'),
                    ("Named Entity Recognition (NER) & Skill Extraction", r'\b(?:ner|named\s*entity|entity\s*recognition|spacy|information\s*extraction|keyword\s*extraction|entity\s*extraction|extract(?:ing)?\s*skills?)\b'),
                    ("Vectorization & Embeddings (TF-IDF / Word2Vec / BERT)", r'\b(?:tf-?idf|vectoriz(?:er|ation)|word2vec|embeddings?|bert|transformer(?:s)?|dense\s*vectors?|cosine\s*similarity|bag\s*of\s*words)\b'),
                    ("Attention Mechanisms & Transformer Encoders", r'\b(?:fine-?tuning|attention\s*mechanism|hugging\s*face|encoder|decoder|transformer\s*layer|self-?attention|prompt\s*engineering)\b'),
                    ("Semantic Similarity Scoring & Search", r'\b(?:cosine\s*similarity|similarity\s*scor(?:e|ing)|semantic\s*match(?:ing)?|faiss|vector\s*db|nearest\s*neighbor|semantic\s*search)\b')
                ],
                "model_answer": (
                    "In our NLP pipeline, we process raw text through multi-stage tokenization, stopword filtering, and lemmatization using spaCy. "
                    "We apply fine-tuned Named Entity Recognition (NER) models to extract specialized entities like skills, certifications, and job titles. "
                    "To compute semantic match scores, we project text into dense embedding spaces using transformer models (such as BERT) and calculate cosine similarity against target job descriptions."
                ),
                "follow_up": "How do you handle out-of-vocabulary words and domain-specific terminology when extracting entities with spaCy or BERT?"
            },
            "machine_learning": {
                "aliases": ["machine learning", "ml", "scikit-learn", "sklearn", "classification", "regression", "clustering", "random forest", "xgboost", "gradient boosting", "data science", "supervised learning", "unsupervised learning"],
                "keywords": ["scikit-learn", "sklearn", "random forest", "xgboost", "gradient boosting", "decision tree", "linear regression", "logistic regression", "svm", "cross-validation", "hyperparameter", "gridsearch", "overfitting", "underfitting", "bias-variance", "f1", "precision", "recall", "roc-auc", "confusion matrix", "feature engineering", "pca", "kmeans", "clustering", "train test split"],
                "concept_rules": [
                    ("Feature Engineering & Data Normalization", r'\b(?:feature\s*engineering|feature\s*selection|scaling|normalization|imputation|one-?hot|train[- ]test\s*split|pca|standardscaler)\b'),
                    ("Model Training & Ensemble Methods (Random Forest / XGBoost)", r'\b(?:random\s*forest|xgboost|gradient\s*boost(?:ing)?|decision\s*trees?|logistic\s*regression|svm|ensemble|classifiers?)\b'),
                    ("Cross-Validation & Regularization (Bias-Variance)", r'\b(?:cross[- ]validation|k-fold|gridsearch(?:cv)?|randomizedsearch|hyperparameters?|overfitting|underfitting|bias[- ]variance|l1|l2|regularization)\b'),
                    ("Evaluation Metrics (Precision, Recall, F1, ROC-AUC)", r'\b(?:precision|recall|f1[- ]score|roc[- ]auc|confusion\s*matrix|accuracy|r2\s*score|mean\s*squared\s*error|rmse|evaluat(?:e|ion))\b'),
                    ("Unsupervised Clustering (K-Means / PCA)", r'\b(?:k-means|clustering|dbscan|dimensionality\s*reduction|pca|t-sne|silhouette\s*score)\b')
                ],
                "model_answer": (
                    "When developing machine learning models, I structure the pipeline around rigorous feature engineering, imputation, and scaling via scikit-learn. "
                    "I train ensemble models like XGBoost and Random Forest, using stratified K-fold cross-validation and hyperparameter tuning to mitigate overfitting and manage the bias-variance trade-off. "
                    "For evaluation, I prioritize F1-score and ROC-AUC over raw accuracy to handle class imbalances effectively."
                ),
                "follow_up": "How do you diagnose and address data leakage when performing feature preprocessing in cross-validation splits?"
            },
            "deep_learning": {
                "aliases": ["deep learning", "neural network", "neural networks", "pytorch", "tensorflow", "keras", "cnn", "rnn", "lstm", "backpropagation"],
                "keywords": ["pytorch", "tensorflow", "keras", "neural network", "backpropagation", "loss function", "gradient descent", "adam", "learning rate", "epoch", "batch size", "dropout", "batch normalization", "cnn", "convolutional", "rnn", "lstm", "activation function", "relu", "softmax", "gpu", "cuda"],
                "concept_rules": [
                    ("Neural Architecture & Layer Design (CNN / RNN / LSTM)", r'\b(?:convolutional|cnn|rnn|lstm|dense\s*layer|hidden\s*layers?|activation\s*function|relu|softmax|sigmoid)\b'),
                    ("Optimization & Loss Computation (Adam / Backpropagation)", r'\b(?:loss\s*function|cross[- ]entropy|gradient\s*descent|adam|learning\s*rate|backpropagation|optimizers?|weight\s*updates?)\b'),
                    ("Regularization & Generalization (Dropout / BatchNorm)", r'\b(?:dropout|batch\s*norm(?:alization)?|weight\s*decay|early\s*stopping|regularization|data\s*augmentation)\b'),
                    ("Training Dynamics & GPU Acceleration (CUDA / PyTorch)", r'\b(?:batch\s*size|epochs?|cuda|gpu\s*acceleration|tensorboard|mixed\s*precision|dataloader|tensors?)\b')
                ],
                "model_answer": (
                    "In our deep learning architecture, we construct neural networks in PyTorch using modular layers and ReLU activations. "
                    "To ensure stable gradient flow and prevent overfitting, we integrate Batch Normalization and Dropout layers between hidden representations. "
                    "We train models on CUDA GPUs using the Adam optimizer with cosine learning rate scheduling and early stopping based on validation loss."
                ),
                "follow_up": "How do you detect and resolve exploding or vanishing gradients during backpropagation in deep neural networks?"
            },
            "javascript": {
                "aliases": ["javascript", "js", "typescript", "ts", "es6", "frontend scripting"],
                "keywords": ["javascript", "typescript", "async", "await", "promise", "closure", "prototype", "event loop", "dom", "callback", "interface", "generic", "types", "destructuring", "arrow function", "scope", "hoisting", "event bubbling", "module", "bundler", "vite", "webpack"],
                "concept_rules": [
                    ("Asynchronous Event Loop & Promises", r'\b(?:event\s*loop|promises?|async\s+await|microtasks?|macrotasks?|callback\s*queue)\b'),
                    ("Closures & Lexical Scope", r'\b(?:closure|lexical\s*scope|variable\s*hoisting|currying|prototype\s*chain|execution\s*context)\b'),
                    ("TypeScript Type Safety & Generics", r'\b(?:typescript|type\s*safety|interfaces?|generics?|type\s*guards?|union\s*types?|type\s*inference)\b'),
                    ("DOM Manipulation & Event Delegation", r'\b(?:event\s*delegation|bubbling|event\s*listener|virtual\s*dom|dom\s*mutation)\b')
                ],
                "model_answer": (
                    "JavaScript executes on a single-threaded runtime managed by the event loop. We structure asynchronous operations around Promises and async/await, ensuring microtasks resolve before rendering cycles. "
                    "We utilize closures to maintain private state, adopt TypeScript for compile-time type safety and interface contracts, and optimize DOM performance using event delegation."
                ),
                "follow_up": "How does the JavaScript V8 engine optimize hidden classes and inline caching for property lookups?"
            },
            "nodejs": {
                "aliases": ["node", "node.js", "nodejs", "express", "express.js", "nest.js", "nestjs"],
                "keywords": ["node", "nodejs", "express", "middleware", "stream", "buffer", "eventemitter", "non-blocking", "cluster", "pm2", "npm", "worker thread", "libuv", "route", "jwt", "cors"],
                "concept_rules": [
                    ("Event-Driven Architecture & Libuv I/O", r'\b(?:event[- ]driven|non[- ]blocking|libuv|single[- ]threaded|event\s*emitter|thread\s*pool)\b'),
                    ("Middleware Pipeline & Request Lifecycle", r'\b(?:middleware|next\(|error\s*handling\s*middleware|request\s*pipeline|express\s*router)\b'),
                    ("Streams, Buffers & Memory Efficiency", r'\b(?:streams?|piping|buffers?|chunked\s*transfer|backpressure)\b'),
                    ("Process Clustering & Concurrency (PM2 / Worker Threads)", r'\b(?:cluster\s*module|pm2|worker\s*threads?|child\s*process|load\s*balancing)\b')
                ],
                "model_answer": (
                    "Node.js utilizes a non-blocking, event-driven architecture powered by libuv, delegating heavy I/O operations to worker thread pools. "
                    "In Express services, we structure route handlers with reusable middleware for authentication and error boundary handling. "
                    "For large data payloads, we stream chunks with backpressure management using stream pipelines, scaling multi-core CPU throughput via PM2 clustering."
                ),
                "follow_up": "How do you handle unhandled Promise rejections and uncaught exceptions gracefully in production Node.js servers?"
            },
            "cloud_devops": {
                "aliases": ["aws", "cloud", "devops", "kubernetes", "k8s", "ci/cd", "terraform", "github actions", "s3", "ec2", "lambda", "infrastructure"],
                "keywords": ["aws", "cloud", "s3", "ec2", "lambda", "kubernetes", "k8s", "pod", "ingress", "deployment", "ci/cd", "pipeline", "github actions", "terraform", "helm", "cloudwatch", "iam", "load balancer", "api gateway", "serverless", "autoscaling"],
                "concept_rules": [
                    ("Infrastructure as Code & CI/CD Pipelines", r'\b(?:terraform|ci[- /]cd|github\s*actions?|jenkins|automation|infrastructure\s*as\s*code|iac)\b'),
                    ("Kubernetes Orchestration & Container Lifecycle", r'\b(?:kubernetes|k8s|pods?|deployments?|services?|ingress|helm|hpa|autoscaling)\b'),
                    ("Cloud Storage & Serverless Architecture (S3 / Lambda)", r'\b(?:aws|s3|lambda|serverless|api\s*gateway|cloudwatch|iam\s*roles?|blob\s*storage)\b'),
                    ("High Availability & Fault Tolerance (Multi-AZ / ALB)", r'\b(?:multi[- ]az|fault\s*tolerance|disaster\s*recovery|auto[- ]scaling|health\s*checks?|alb)\b')
                ],
                "model_answer": (
                    "We architect cloud systems on AWS using Terraform for reproducible Infrastructure as Code (IaC) and GitHub Actions for automated CI/CD. "
                    "Workloads are deployed across Kubernetes pods with Horizontal Pod Autoscalers (HPA) behind Application Load Balancers. "
                    "Static assets are stored securely in S3 with least-privilege IAM policies, while asynchronous compute is offloaded to serverless Lambda functions."
                ),
                "follow_up": "How do you structure rolling deployments and zero-downtime canary rollouts on Kubernetes?"
            },
            "rest_api": {
                "aliases": ["api", "rest", "restful", "http", "graphql", "microservice", "backend", "web services", "endpoints"],
                "keywords": ["rest", "api", "endpoint", "http", "status code", "get", "post", "put", "delete", "header", "payload", "json", "cors", "jwt", "oauth", "rate limiting", "graphql", "caching", "idempotent", "stateless"],
                "concept_rules": [
                    ("RESTful Principles & Idempotency", r'\b(?:restful|idempotent|http\s*methods?|status\s*codes?|stateless|resource[- ]oriented|crud)\b'),
                    ("API Authentication & Security Boundaries (JWT / CORS)", r'\b(?:jwt|bearer\s*token|oauth2?|cors|rate\s*limit(?:ing)?|api\s*key|input\s*sanitization)\b'),
                    ("Payload Serialization & Pydantic Validation", r'\b(?:json\s*schema|serialization|deserialization|data\s*validation|content[- ]type|pagination)\b'),
                    ("API Versioning & Caching Strategies", r'\b(?:api\s*versioning|etag|cache[- ]control|reverse\s*proxy|cdn)\b')
                ],
                "model_answer": (
                    "We design RESTful APIs adhering to stateless resource principles with consistent HTTP status codes and JSON envelopes. "
                    "Route handlers enforce JWT bearer token authentication and rate limiting to prevent abuse. "
                    "Payloads are strictly validated against structured schemas before persistence, with pagination and ETag headers applied on list endpoints."
                ),
                "follow_up": "What is the difference between PUT and PATCH operations in REST API design, and how does idempotency apply?"
            },
            "data_engineering": {
                "aliases": ["data engineering", "etl", "pandas", "numpy", "spark", "pyspark", "data pipeline", "kafka"],
                "keywords": ["etl", "pipeline", "pandas", "dataframe", "numpy", "spark", "pyspark", "data warehouse", "parquet", "batch processing", "streaming", "data modeling", "schema", "data quality", "ingestion"],
                "concept_rules": [
                    ("ETL Pipeline Architecture & Ingestion", r'\b(?:etl|extract[- ]transform[- ]load|data\s*pipeline|ingestion|batch\s*processing|stream\s*processing)\b'),
                    ("Dataframe Transformations & Vectorization (Pandas / NumPy)", r'\b(?:pandas|dataframe|numpy|vectoriz(?:ed|ation)|group[- ]by|filtering|broadcasting)\b'),
                    ("Distributed Data Processing (Spark / PySpark)", r'\b(?:spark|pyspark|rdd|mapreduce|parquet|distributed\s*compute|partitioning)\b'),
                    ("Data Quality, Deduplication & Storage", r'\b(?:data\s*quality|deduplication|schema\s*enforcement|data\s*warehouse|olap)\b')
                ],
                "model_answer": (
                    "In our data engineering pipelines, we build automated ETL workflows using Pandas for structured vectorization and PySpark for distributed batch processing. "
                    "We ingest heterogeneous data, apply schema validation and deduplication, and export partitioned Parquet files to cloud data warehouses for analytics."
                ),
                "follow_up": "How do you optimize partition skew and shuffling in distributed Spark data pipelines?"
            },
            "testing_qa": {
                "aliases": ["testing", "qa", "unit testing", "pytest", "jest", "mocking", "tdd", "integration testing"],
                "keywords": ["test", "unit test", "integration test", "pytest", "jest", "mock", "stub", "assert", "coverage", "tdd", "fixture", "regression", "e2e", "cypress", "selenium"],
                "concept_rules": [
                    ("Unit & Integration Test Automation (pytest / Jest)", r'\b(?:unit\s*tests?|integration\s*tests?|pytest|jest|test\s*suite|assertion|test\s*runner)\b'),
                    ("Mocking & Test Isolation Strategies", r'\b(?:mock(?:ing|s)?|stubs?|fixtures?|monkeypatch|test\s*isolation|dependency\s*mock)\b'),
                    ("Code Coverage & Edge-Case Validation", r'\b(?:code\s*coverage|regression\s*test(?:ing)?|boundary\s*conditions?|edge\s*cases?|tdd)\b')
                ],
                "model_answer": (
                    "We maintain software reliability by writing automated unit and integration tests with pytest and Jest. "
                    "We isolate external network and database dependencies using mocks and test fixtures, enforcing 80%+ code coverage gates in CI/CD before staging deployment."
                ),
                "follow_up": "How do you strike the right balance between unit tests, integration tests, and end-to-end tests in the testing pyramid?"
            },
            "css": {
                "aliases": ["css", "css3", "styling", "styles", "tailwind", "tailwind css", "sass", "scss", "bootstrap"],
                "keywords": ["css", "css3", "flexbox", "grid", "selector", "specificity", "reflow", "repaint", "box-sizing", "border-box", "transform", "transition", "animation", "media query", "responsive", "bem", "critical css", "dom", "layout", "will-change", "clamp", "rem", "vh", "vw", "z-index", "pseudo-class", "keyframes"],
                "concept_rules": [
                    ("Box Model & Layout Engines (Grid / Flexbox)", r'\b(?:box-sizing|border-box|flexbox|css\s*grid|display:\s*(?:flex|grid)|margin-collapse|flex|grid)\b'),
                    ("Critical Rendering Path (Reflow & Repaint)", r'\b(?:reflow|repaint|critical\s*css|render\s*tree|layout\s*thrashing|composite\s*layer|content-visibility)\b'),
                    ("Hardware-Accelerated Transforms & Animations", r'\b(?:transform(?:3d|s)?|will-change|gpu\s*acceleration|requestanimationframe|transition(?:s)?|keyframes?|animation(?:s)?)\b'),
                    ("Specificity & Cascade Architecture (BEM / CSS Modules)", r'\b(?:specificity|cascade|bem|css\s*modules?|css-in-js|utility[- ]first|styled-components)\b'),
                    ("Responsive Viewports & Fluid Units", r'\b(?:media\s*queries?|container\s*queries?|responsive|clamp\(|rem|em|vw|vh)\b')
                ],
                "model_answer": (
                    "When architecting CSS3 in production, I prioritize critical rendering path performance by inlining above-the-fold CSS and leveraging 'content-visibility: auto' for heavy off-screen sections. "
                    "To prevent layout thrashing and maintain 60 FPS, I replace JS animations with hardware-accelerated CSS transforms ('transform: translate3d' and 'will-change'). "
                    "For structural styling, I combine CSS Grid for macro-layouts with Flexbox for micro-components, structured with BEM naming to prevent specificity wars and reduce dead CSS by ~30%."
                ),
                "follow_up": "How do you prevent reflow and repaint bottlenecks when rendering high-frequency dynamic UI updates in CSS?"
            },
            "react": {
                "aliases": ["react", "react.js", "reactjs", "next.js", "nextjs", "jsx", "tsx"],
                "keywords": ["props", "state", "useeffect", "usememo", "usecallback", "usestate", "re-render", "virtual dom", "fiber", "reconciliation", "hooks", "component", "cleanup", "zustand", "redux", "context", "jsx", "suspense", "lifecycle"],
                "concept_rules": [
                    ("Unidirectional Data Flow & State Management", r'\b(?:unidirectional|one[- ]way\s*data|top[- ]down\s*data|lifting\s*state|state\s*lifting|state\s*management)\b'),
                    ("Lifecycle & Cleanup in `useEffect`", r'\b(?:useeffect|cleanup\s*function|unmount|componentwillunmount|abortcontroller|lifecycle)\b'),
                    ("Virtual DOM Reconciliation & Fiber Diffing", r'\b(?:virtual\s*dom|vdom|reconciliation|fiber|diffing\s*algorithm)\b'),
                    ("Memoization & Render Optimization", r'\b(?:usememo|usecallback|react\.memo|re-render(?:ing|s)?|shallow\s*compare)\b'),
                    ("Hooks & Context State Localization", r'\b(?:custom\s*hooks?|usecontext|zustand|redux|prop\s*drilling|hooks?)\b')
                ],
                "model_answer": (
                    "In our architecture, we structure React applications around unidirectional data flow and strict component modularity. "
                    "We isolate side-effects within 'useEffect' hooks, always supplying cleanup routines (like AbortController) to eliminate memory leaks upon component unmounting. "
                    "To optimize rendering performance, we prevent unnecessary Virtual DOM diffing passes using 'useMemo' and 'useCallback' on expensive child subtrees, sustaining smooth 60 FPS interactions."
                ),
                "follow_up": "Under what specific conditions can overuse of useMemo and useCallback actually degrade React application performance?"
            },
            "python": {
                "aliases": ["python", "python3", "cpython", "py", "pytest"],
                "keywords": ["gil", "thread", "asyncio", "generator", "yield", "decorator", "closure", "immutable", "tuple", "list", "dict", "memory", "reference count", "garbage collection", "cprofile", "typing", "dunder", "magic method"],
                "concept_rules": [
                    ("Global Interpreter Lock (GIL) & Concurrency", r'\b(?:gil|global\s*interpreter\s*lock|cpython|gil\s*release|multiprocessing)\b'),
                    ("Generators & Lazy Iterator Evaluation", r'\b(?:generators?|yield|lazy\s*evaluation|iterator|__iter__|__next__)\b'),
                    ("Decorators & First-Class Function Closures", r'\b(?:decorators?|closure|functools\.wraps|higher[- ]order\s*functions?|wrapper\s*function)\b'),
                    ("Reference Counting & Cyclic GC", r'\b(?:reference\s*counting|garbage\s*collect(?:ion|or)|gc\s*cycle|mutab(?:le|ility))\b'),
                    ("AsyncIO Event Loop Execution", r'\b(?:asyncio|event\s*loop|async\s+def|await|coroutine|task\s*group)\b')
                ],
                "model_answer": (
                    "In Python systems, I design memory-efficient pipelines by replacing eager list materialization with lazy generators and the 'yield' keyword, maintaining a flat memory footprint across multi-gigabyte files. "
                    "Because CPython's Global Interpreter Lock (GIL) restricts CPU-bound multithreading, I utilize 'asyncio' for I/O concurrency and multiprocessing/ProcessPoolExecutor for compute-heavy parallel workloads. "
                    "I encapsulate cross-cutting logic like auth and telemetry via decorator closures using functools.wraps."
                ),
                "follow_up": "How does Python's cyclical garbage collector detect and reclaim reference cycles that simple reference counting cannot handle?"
            },
            "fastapi": {
                "aliases": ["fastapi", "uvicorn", "starlette", "pydantic"],
                "keywords": ["pydantic", "validation", "async", "await", "depends", "dependency", "openapi", "swagger", "starlette", "uvicorn", "lifespan", "middleware", "background task", "status code", "endpoint", "schema", "basemodel"],
                "concept_rules": [
                    ("Pydantic Request/Response Data Validation", r'\b(?:pydantic|basemodel|field\s*validator|422\s*unprocessable|data\s*validation)\b'),
                    ("Dependency Injection (`Depends`) System", r'\b(?:dependency\s*injection|depends\(|security\s*dependency|db\s*session\s*dependency)\b'),
                    ("Asynchronous ASGI Event Loop (Starlette/Uvicorn)", r'\b(?:starlette|uvicorn|async\s+def|asgi|concurrent\s*requests?)\b'),
                    ("Automatic OpenAPI & Interactive Swagger Docs", r'\b(?:openapi|swagger|redoc|api\s*schema|docs\s*endpoint)\b'),
                    ("Lifespan Context Management & Middleware", r'\b(?:lifespan|startup\s*event|backgroundtasks?|middleware)\b')
                ],
                "model_answer": (
                    "FastAPI leverages native ASGI asynchronous execution on top of Starlette and Uvicorn, handling thousands of concurrent I/O-bound requests on a single process. "
                    "Incoming JSON payloads are strictly validated against Pydantic models with type hints, automatically rejecting malformed requests with 422 Unprocessable Entity status codes. "
                    "We utilize the 'Depends' dependency injection system for database session pooling and authentication, keeping route handlers clean and unit-testable."
                ),
                "follow_up": "How do you prevent blocking the main asyncio event loop when calling synchronous legacy libraries inside FastAPI route handlers?"
            },
            "mongodb": {
                "aliases": ["mongodb", "mongo", "nosql", "document database", "bson"],
                "keywords": ["bson", "document", "schema", "embed", "reference", "index", "aggregation", "pipeline", "sharding", "replica", "wiredtiger", "16mb", "collection", "nosql", "query", "compound index", "indexes", "indexing"],
                "concept_rules": [
                    ("BSON Document Model & Dynamic Schemas", r'\b(?:bson|document\s*model|schemaless|dynamic\s*schema|flexible\s*schema|nested\s*documents?|documents?)\b'),
                    ("Compound Indexing & Query Plans", r'\b(?:compound\s*index(?:es|ing)?|explain\(\)|index\s*scan|covered\s*query|b-tree|indexes|indexing)\b'),
                    ("Aggregation Pipeline & Multi-stage Queries", r'\b(?:aggregation\s*pipeline|\$match|\$group|\$project|\$lookup|\$unwind|aggregation)\b'),
                    ("Embedding vs Referencing Trade-offs (16MB Limit)", r'\b(?:embed(?:ding)?\s*vs\s*referenc(?:ing)?|16mb\s*limit|foreign\s*keys?\s*in\s*nosql|embed(?:ded)?|referenc(?:ed)?)\b'),
                    ("Horizontal Sharding & High-Availability Replica Sets", r'\b(?:sharding|shard\s*key|replica\s*set|write\s*concern|read\s*preference)\b')
                ],
                "model_answer": (
                    "MongoDB organizes unstructured and hierarchical data into flexible BSON documents. We balance embedding versus referencing based on access patterns: frequently co-read entities are embedded, while unbounded relationships are referenced to avoid the 16MB document size limit. "
                    "To maintain sub-50ms query latency, we establish compound indexes matching our query filter equality-sort-range patterns, and execute multi-stage aggregations for real-time analytics."
                ),
                "follow_up": "What criteria do you use to choose a shard key in MongoDB to prevent hot-spotting on write-heavy collections?"
            },
            "sql": {
                "aliases": ["sql", "postgresql", "postgres", "mysql", "sqlite", "relational database", "rdbms"],
                "keywords": ["acid", "transaction", "join", "index", "b-tree", "isolation", "deadlock", "foreign key", "normalization", "partition", "window function", "postgres", "mysql", "query plan", "3nf", "cascade", "cte"],
                "concept_rules": [
                    ("ACID Guarantees & Transaction Isolation Levels", r'\b(?:acid|isolation\s*levels?|serializable|repeatable\s*read|read\s*committed|commit|rollback|deadlock)\b'),
                    ("Index Seek vs Scan & B-Tree Optimization", r'\b(?:index\s*seek|index\s*scan|b-tree|clustered\s*index|covering\s*index|query\s*execution\s*plan|explain\s*analyze)\b'),
                    ("Relational JOIN Mechanics (Hash, Merge, Nested Loop)", r'\b(?:inner\s*join|left\s*join|hash\s*join|merge\s*join|nested\s*loop)\b'),
                    ("Normalization (3NF) & Referential Integrity", r'\b(?:normalization|3nf|third\s*normal|foreign\s*keys?|referential\s*integrity|cascade)\b'),
                    ("Window Functions & Common Table Expressions (CTEs)", r'\b(?:window\s*functions?|partition\s*by|over\s*\(|common\s*table\s*expressions?|cte)\b')
                ],
                "model_answer": (
                    "Relational databases enforce strict schemas and ACID guarantees to ensure transaction integrity. When optimizing complex queries, we analyze the execution plan via EXPLAIN ANALYZE to verify index seeks over sequential scans. "
                    "We model data up to Third Normal Form (3NF) to eliminate anomalies, adding covering B-tree indexes on join foreign keys and applying appropriate transaction isolation levels (e.g. Read Committed) to prevent phantom reads without blocking concurrency."
                ),
                "follow_up": "How does PostgreSQL implement Multi-Version Concurrency Control (MVCC), and why is VACUUM necessary?"
            },
            "docker": {
                "aliases": ["docker", "container", "containers", "dockerfile", "docker-compose", "containerization"],
                "keywords": ["image", "container", "layer", "multi-stage", "build", "network", "bridge", "host", "cgroups", "namespace", "daemon", "dockerfile", "volume", "rootless", "entrypoint", "alpine", "compose"],
                "concept_rules": [
                    ("Layered Filesystem & Build Caching", r'\b(?:layered\s*file\s*system|layer\s*caching|build\s*cache|\.dockerignore|dockerfile\s*layers?)\b'),
                    ("Multi-Stage Builds & Minimal Runtime Images", r'\b(?:multi[- ]stage\s*builds?|alpine|scratch|distroless|image\s*size)\b'),
                    ("Container Network Isolation (Bridge / Host)", r'\b(?:bridge\s*network|host\s*network|port\s*mapping|container\s*dns)\b'),
                    ("Kernel Namespaces & cgroups Resource Limits", r'\b(?:cgroups?|namespaces?|memory\s*limit|cpu\s*quota|process\s*isolation)\b'),
                    ("Non-Root Security Hardening & Volumes", r'\b(?:non[- ]root\s*user|read[- ]only\s*rootfs|persistent\s*volumes?|bind\s*mount)\b')
                ],
                "model_answer": (
                    "A Docker image is an immutable template constructed of read-only layered filesystems, whereas a container is a running instance executing on the host Linux kernel isolated via cgroups and namespaces. "
                    "We optimize CI/CD pipelines using multi-stage builds and Alpine bases to shrink final image sizes by ~80%, order Dockerfile commands from least to most frequently modified to maximize layer caching, and run containers under non-root users for defense-in-depth."
                ),
                "follow_up": "How do Linux namespaces and cgroups differ in their roles during container isolation?"
            },
            "yolo": {
                "aliases": ["yolo", "yolov8", "yolo-v8", "object detection", "computer vision", "cv"],
                "keywords": ["yolo", "yolov8", "bounding", "anchor", "detection", "inference", "onnx", "tensorrt", "map", "nms", "coco", "fp16", "fps", "latency", "real-time", "video", "iou", "precision", "recall"],
                "concept_rules": [
                    ("Anchor-free Single-Shot Detection Architecture", r'\b(?:anchor[- ]free|single[- ]shot|bounding\s*boxes?|yolov8|iou\s*threshold)\b'),
                    ("Non-Maximum Suppression (NMS) & Confidence Filtering", r'\b(?:non[- ]maximum\s*suppression|nms|confidence\s*threshold|map|precision[- ]recall)\b'),
                    ("TensorRT / ONNX Acceleration & Quantization", r'\b(?:tensorrt|onnx|fp16|int8|quantization|graph\s*optimization)\b'),
                    ("Real-Time Frame Rate (FPS) & Sub-50ms Latency", r'\b(?:frame\s*rate|fps|inference\s*latency|real[- ]time\s*inference)\b'),
                    ("Edge Deployment & Model Trade-offs", r'\b(?:edge\s*deployment|batch\s*inference|gpu\s*memory|mAP\s*vs\s*speed)\b')
                ],
                "model_answer": (
                    "YOLOv8 utilizes an anchor-free single-shot detection architecture that predicts bounding box coordinates and class probabilities in a single forward pass. "
                    "To deploy in real-time video pipelines, we export PyTorch models to ONNX and accelerate the compute graph with TensorRT INT8/FP16 quantization, achieving steady 38+ FPS inference. "
                    "We tune Non-Maximum Suppression (NMS) IoU thresholds to discard redundant overlapping bounding boxes without dropping genuine detections."
                ),
                "follow_up": "How do you handle occlusion and false positives when detecting small objects at a distance in YOLO?"
            },
            "opencv": {
                "aliases": ["opencv", "cv2", "image processing", "vision pipeline"],
                "keywords": ["opencv", "cv2", "frame", "videocapture", "grayscale", "blur", "roi", "mask", "threshold", "contour", "morphology", "image", "pipeline", "fps", "gaussian", "canny", "hsv"],
                "concept_rules": [
                    ("Frame Ingestion Pipeline (`cv2.VideoCapture`)", r'\b(?:videocapture|cv2\.read|frame\s*ingestion|stream\s*decoding)\b'),
                    ("Region of Interest (ROI) Masking & Optimization", r'\b(?:roi|region\s*of\s*interest|cropping|bounding\s*box\s*crop)\b'),
                    ("Morphological Filtering & Noise Reduction", r'\b(?:morpholog(?:y|ical)|gaussian\s*blur|grayscale|threshold(?:ing)?|noise\s*removal)\b'),
                    ("Contour Detection & Bounding Box Rendering", r'\b(?:findcontours|contour|bounding\s*rect|cv2\.rectangle)\b'),
                    ("Color Space Conversion (BGR / HSV / Grayscale)", r'\b(?:cvtcolor|bgr|rgb|hsv|grayscale\s*conversion)\b')
                ],
                "model_answer": (
                    "In our vision pipeline, OpenCV handles real-time video stream ingestion via 'cv2.VideoCapture' and preprocessing before deep learning inference. "
                    "We apply Region of Interest (ROI) masking to crop only the active detection zones, reducing downstream pixel processing volume by over 50%. "
                    "We utilize morphological opening and Gaussian blurring to suppress sensor noise, offloading frame rendering to background worker threads to maintain 30+ FPS."
                ),
                "follow_up": "How do you eliminate frame buffer lag when processing high-latency video streams in OpenCV?"
            },
            "algorithms": {
                "aliases": ["algorithms", "data structures", "dsa", "complexity", "big o", "trees", "graphs", "sorting"],
                "keywords": ["algorithm", "complexity", "big-o", "o(n)", "binary search", "hash map", "tree", "graph", "bfs", "dfs", "dynamic programming", "memoization", "queue", "stack", "recursion", "divide and conquer", "latency", "throughput", "optimization"],
                "concept_rules": [
                    ("Time & Space Complexity Analysis (Big-O)", r'\b(?:time\s*complexity|space\s*complexity|o\(n\)|o\(log\s*n\)|o\(1\)|big[- ]o)\b'),
                    ("Dynamic Programming & Memoization", r'\b(?:dynamic\s*programming|memoization|tabulation|subproblems?|optimal\s*substructure)\b'),
                    ("Graph & Tree Traversals (BFS / DFS)", r'\b(?:bfs|dfs|breadth[- ]first|depth[- ]first|dijkstra|topological\s*sort|tree\s*traversal)\b'),
                    ("Hash Table & Collision Resolution Strategies", r'\b(?:hash\s*table|hash\s*map|collision|separate\s*chaining|lookup\s*time)\b'),
                    ("Divide & Conquer and Binary Search", r'\b(?:binary\s*search|divide\s*and\s*conquer|quick\s*sort|merge\s*sort|heap)\b')
                ],
                "model_answer": (
                    "When designing data algorithms, we analyze time and space complexity trade-offs using Big-O notation. For frequent lookup paths, we replace linear O(N) searches with O(1) hash maps, handling potential collisions via separate chaining. "
                    "In multi-step optimization problems, we apply dynamic programming with memoization to eliminate exponential subproblem recomputation, keeping memory overhead predictable."
                ),
                "follow_up": "How do you detect and handle worst-case hash collision degradation when implementing custom hashing keys?"
            },
            "system_design": {
                "aliases": ["system design", "microservices", "distributed systems", "scalability", "architecture"],
                "keywords": ["microservices", "scalability", "load balancer", "caching", "redis", "kafka", "queue", "database sharding", "read replica", "stateless", "circuit breaker", "rate limit", "nginx", "horizontal scale", "availability", "latency"],
                "concept_rules": [
                    ("Horizontal Scaling & Load Balancing", r'\b(?:horizontal\s*scal(?:ing|e)|load\s*balanc(?:er|ing)|stateless|nginx|autoscal(?:ing|e))\b'),
                    ("Distributed Caching (Redis / Memcached)", r'\b(?:redis|memcached|cache[- ]aside|write[- ]through|ttl|cache\s*stampede)\b'),
                    ("Asynchronous Message Queues (Kafka / Celery)", r'\b(?:kafka|rabbitmq|message\s*queues?|event[- ]driven|pub[- ]sub|celery|decoupling)\b'),
                    ("Database Sharding & Read Replicas", r'\b(?:read\s*replicas?|cqrs|sharding|partitioning|replication\s*lag)\b'),
                    ("Resilience Patterns (Circuit Breakers & Rate Limits)", r'\b(?:circuit\s*breaker|rate\s*limit(?:ing|er)|retry\s*with\s*backoff|bulkhead)\b')
                ],
                "model_answer": (
                    "To scale our architecture, we decouple compute from data storage using stateless service instances behind an Nginx load balancer. "
                    "We implement a Redis cache-aside layer to eliminate repetitive database reads, reducing p99 latency to <20ms. "
                    "Compute-heavy background jobs are offloaded to asynchronous Kafka/Celery worker queues with retry backoff, maintaining 99.9% uptime during traffic surges."
                ),
                "follow_up": "How do you handle cache stampedes and distributed cache invalidation under sudden traffic spikes?"
            },
            "behavioral": {
                "aliases": ["behavioral", "soft skills", "communication", "leadership", "teamwork", "conflict"],
                "keywords": ["situation", "task", "action", "result", "team", "challenge", "stakeholder", "ownership", "conflict", "deadline", "debugged", "resolved", "learned", "collaborated", "mentored"],
                "concept_rules": [
                    ("STAR Method Structure (Situation & Task Context)", r'\b(?:situation|context|objective|challenge|faced\s*a\s*problem|the\s*task\s*was)\b'),
                    ("Individual Technical Ownership & Action", r'\b(?:i\s*led|i\s*implemented|i\s*diagnosed|i\s*decided|i\s*built|my\s*role|i\s*took\s*ownership)\b'),
                    ("Measurable Business & Engineering Result", r'\b(?:result|improved|reduced|increased|delivered|measured\s*by|\d+%\b|\d+x\b|outcome)\b'),
                    ("Cross-Functional Collaboration & Resolution", r'\b(?:stakeholders?|cross[- ]functional|peer|mentored|consensus|trade[- ]off)\b')
                ],
                "model_answer": (
                    "In my previous project, we faced critical latency spikes during live camera processing. As the lead engineer, I profiled CPU bottlenecks using runtime telemetry and identified thread contention in our video decoder. "
                    "I restructured the ingestion pipeline to offload decoding to background worker threads. As a result, we restored steady 30 FPS throughput and delivered the feature two days ahead of our release milestone."
                ),
                "follow_up": "Looking back at that experience, what architectural choice would you make differently today?"
            }
        }

        # -------------------------------------------------------------
        # 4. IDENTIFY TARGET DOMAIN & DETECT ANSWER DOMAINS
        # -------------------------------------------------------------
        target_domain_key = None
        target_domain_obj = None

        # 1. Primary match: check if the question's specific skill maps to a domain
        for d_key, d_data in TECHNICAL_DOMAINS.items():
            if any(re.search(r'\b' + re.escape(alias) + r'\b', skill, re.IGNORECASE) for alias in d_data["aliases"]) or skill.lower() == d_key:
                target_domain_key = d_key
                target_domain_obj = d_data
                break

        # 2. Secondary match: search the entire question text and expected points using word boundaries
        if not target_domain_obj:
            search_text = f"{skill} {question_text} {' '.join(expected_points or [])}".lower()
            for d_key, d_data in TECHNICAL_DOMAINS.items():
                if any(re.search(r'\b' + re.escape(alias) + r'\b', search_text, re.IGNORECASE) for alias in d_data["aliases"]) or re.search(r'\b' + re.escape(d_key) + r'\b', search_text, re.IGNORECASE):
                    target_domain_key = d_key
                    target_domain_obj = d_data
                    break

        # Detect which domain the candidate's answer ACTUALLY discusses
        detected_answer_domains = {}
        for d_key, d_data in TECHNICAL_DOMAINS.items():
            hits = sum(1 for kw in d_data["keywords"] if re.search(r'\b' + re.escape(kw) + r'\b', lower_ans))
            if hits > 0:
                detected_answer_domains[d_key] = hits

        # Check keyword hits against the target domain
        target_hits = 0
        if target_domain_obj:
            target_hits = sum(1 for kw in target_domain_obj["keywords"] if re.search(r'\b' + re.escape(kw) + r'\b', lower_ans))

        # Distinct question topical keywords (excluding common filler words)
        stopwords = {
            "the", "a", "an", "and", "or", "to", "for", "in", "on", "of", "at", "by", "with", "from",
            "as", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "can", "could", "should", "would", "will", "shall", "may", "might", "must", "what", "how", "why",
            "when", "which", "who", "whom", "where", "your", "you", "our", "my", "their", "his", "her", "its",
            "project", "projects", "job", "target", "require", "requires", "required", "solid", "experience",
            "experienced", "applied", "apply", "applying", "ramp", "work", "worked", "working", "explain",
            "describe", "tell", "detail", "details", "decision", "made", "key", "use", "used", "using",
            "about", "this", "that", "these", "those", "have", "with", "into"
        }
        q_tokens = [w for w in re.findall(r'\b[a-z0-9]{3,}\b', question_text.lower()) if w not in stopwords]
        q_token_matches = sum(1 for qw in q_tokens if re.search(r'\b' + re.escape(qw) + r'\b', lower_ans))

        # Check expected points coverage with flexible stemming and partial matching
        def _stem_match(kw: str, text: str) -> bool:
            base = re.sub(r'(?:ing|ed|es|s)$', '', kw.lower())
            if len(base) < 3:
                base = kw.lower()
            pattern = r'\b' + re.escape(base) + r'[a-z]*\b'
            return bool(re.search(pattern, text, re.IGNORECASE))

        exp_pts = expected_points or []
        expected_points_covered = []
        expected_points_missed = []
        for pt in exp_pts:
            pt_clean = re.sub(r'[^a-z0-9\s]', ' ', pt.lower())
            pt_keywords = [w for w in pt_clean.split() if len(w) > 3 and w not in stopwords]
            if not pt_keywords:
                continue
            matched_pt_kw = sum(1 for kw in pt_keywords if _stem_match(kw, lower_ans))
            if matched_pt_kw >= 1:
                expected_points_covered.append(pt)
            else:
                expected_points_missed.append(pt)

        # Extract verified concepts covered vs missed
        concepts_covered = []
        concepts_missed = []
        if target_domain_obj:
            for c_name, c_regex in target_domain_obj["concept_rules"]:
                if re.search(c_regex, lower_ans, re.IGNORECASE):
                    concepts_covered.append(c_name)
                else:
                    concepts_missed.append(c_name)
        else:
            concepts_covered = expected_points_covered
            concepts_missed = expected_points_missed

        # Check for Cross-Domain Mismatch ONLY if candidate completely discusses another distinct domain
        is_domain_mismatch = False
        mismatch_topic = ""
        if target_domain_key:
            if target_hits == 0 and len(concepts_covered) == 0 and skill.lower() not in lower_ans:
                top_detected = sorted(detected_answer_domains.items(), key=lambda x: x[1], reverse=True)
                if top_detected and top_detected[0][0] != target_domain_key and top_detected[0][1] >= 3:
                    is_domain_mismatch = True
                    mismatch_topic = top_detected[0][0].replace("_", " ").title()
                elif q_token_matches == 0 and word_count >= 20:
                    is_domain_mismatch = True
                    mismatch_topic = "an unrelated topic"

        # -------------------------------------------------------------
        # 5. COMPUTING 6-AXIS SCORES (Explainable, Balanced, Grounded)
        # -------------------------------------------------------------
        if is_domain_mismatch:
            # Clear low score with educational mismatch feedback
            relevance_score = 12
            technical_accuracy = 10
            completeness = 15
            clarity = 60 if word_count >= 25 else 45
            confidence = 50
            communication = 50
            overall = int(
                (relevance_score * 0.30) +
                (technical_accuracy * 0.30) +
                (completeness * 0.20) +
                (clarity * 0.08) +
                (confidence * 0.06) +
                (communication * 0.06)
            )
            verdict = "Off-Topic / Domain Mismatch"
            next_diff = "Easy"

            strengths = [
                f"Submitted technical text, but it focuses on {mismatch_topic or 'a different domain'} rather than {skill}."
            ]
            weaknesses = [
                f"The response does not address {skill} or the core question asked.",
                f"Structure your answer around {skill} mechanisms, architectural choices, and project trade-offs."
            ]
            feedback_summary = f"Off-topic response ({overall}/100). The answer discusses {mismatch_topic or 'unrelated concepts'} instead of addressing {skill}."

        else:
            # 1. Relevance Score (0-100)
            rel_pts = 0
            if skill.lower() in lower_ans:
                rel_pts += 35
            elif target_hits > 0:
                rel_pts += min(30, target_hits * 8)

            rel_pts += min(35, q_token_matches * 10)
            if exp_pts:
                exp_ratio = len(expected_points_covered) / max(1, len(exp_pts))
                rel_pts += int(exp_ratio * 30)
            else:
                rel_pts += min(25, word_count // 3)

            # Ensure minimum relevance for on-topic words
            if q_token_matches >= 1 or target_hits >= 1 or skill.lower() in lower_ans:
                relevance_score = min(96, max(45, rel_pts))
            else:
                relevance_score = min(96, max(20, rel_pts))

            # 2. Technical Accuracy Score (0-100)
            penalty = 0
            if "tuple is mutable" in lower_ans or "tuples are mutable" in lower_ans:
                penalty += 30
            if "mongodb is relational" in lower_ans or "mongodb foreign key" in lower_ans:
                penalty += 30
            if "useeffect runs before" in lower_ans:
                penalty += 25
            if "css grid is 1d" in lower_ans:
                penalty += 25

            if target_domain_obj:
                if len(concepts_covered) > 0:
                    tech_base = (len(concepts_covered) * 22) + min(35, target_hits * 7)
                elif target_hits >= 1:
                    tech_base = min(55, 20 + target_hits * 10)
                elif word_count >= 15 and (skill.lower() in lower_ans or q_token_matches >= 2):
                    tech_base = min(40, 20 + q_token_matches * 5 + word_count // 4)
                else:
                    tech_base = min(25, 10 + word_count // 5)
            else:
                # Dynamic domain fallback for unlisted/custom skills
                if len(expected_points_covered) > 0:
                    tech_base = min(90, (len(expected_points_covered) * 25) + (q_token_matches * 8) + min(20, word_count // 3))
                elif skill.lower() in lower_ans and q_token_matches >= 1:
                    tech_base = min(45, 20 + q_token_matches * 6 + word_count // 4)
                else:
                    tech_base = min(25, 10 + word_count // 5)

            technical_accuracy = min(96, max(0, tech_base - penalty))

            # 3. Completeness Score (Problem + Action + Result + Trade-offs)
            has_causal = any(c in lower_ans for c in ["because", "in order to", "which allowed", "so that", "leading to", "due to", "why we chose", "as a result", "using", "by using", "implemented via"])
            has_metric = bool(re.search(r'\d+%|\d+ms|\d+x|\$\d+|\d+\s*(?:users|sec|seconds|records|queries|fps|kb|mb|gb|rps|requests)', lower_ans))
            has_tradeoff = any(t in lower_ans for t in ["trade-off", "tradeoff", "downside", "limitation", "alternative", "however", "instead of", "compared to", "overhead", "versus"])

            comp_sub = (30 if target_hits >= 1 or len(concepts_covered) >= 1 or q_token_matches >= 1 else 10) + \
                       (25 if has_causal else 0) + \
                       (25 if has_tradeoff else 0) + \
                       (20 if has_metric else 0)

            if word_count >= 35 and relevance_score >= 50:
                completeness = min(95, max(50, comp_sub))
            elif word_count >= 15:
                completeness = min(80, max(35, int(comp_sub * 0.8)))
            else:
                completeness = min(50, max(20, comp_sub // 2))

            # 4. Clarity Score (0-100)
            has_sentences = lower_ans.count(".") >= 1 or lower_ans.count("\n") >= 1 or word_count >= 20
            clarity = 88 if has_sentences and word_count >= 25 else (75 if word_count >= 12 else 55)

            # 5. Confidence Score (0-100)
            hesitations = ["maybe", "i think", "i guess", "probably", "not really sure", "sort of", "kind of", "i don't know"]
            hesitation_count = sum(1 for h in hesitations if h in lower_ans)
            confidence = max(35, 90 - (hesitation_count * 15))

            # 6. Communication Score (0-100)
            comm_words = ["specifically", "architected", "implemented", "optimized", "ensured", "mitigated", "structured", "decoupled", "prioritized", "orchestrated", "extracted", "engineered", "processed", "integrated", "validated"]
            comm_hits = sum(1 for cw in comm_words if cw in lower_ans)
            communication = min(95, max(50, 60 + (comm_hits * 6) + (10 if has_sentences else 0)))

            # Weighted Overall Score
            overall = int(
                (relevance_score * 0.30) +
                (technical_accuracy * 0.30) +
                (completeness * 0.20) +
                (clarity * 0.08) +
                (confidence * 0.06) +
                (communication * 0.06)
            )

            # Clamp only if answer has zero relevance or is single-word trivial
            if word_count < 6 and q_token_matches == 0 and target_hits == 0:
                overall = min(overall, 30)

            # Verdict rating
            if overall >= 85:
                verdict = "Exceptional Technical Mastery"
                next_diff = "Hard" if difficulty in ["Easy", "Medium"] else "Expert"
            elif overall >= 70:
                verdict = "Strong Technical Answer"
                next_diff = "Hard" if difficulty == "Medium" else difficulty
            elif overall >= 55:
                verdict = "Adequate with Gaps"
                next_diff = difficulty
            elif overall >= 35:
                verdict = "Needs Technical Depth"
                next_diff = "Medium" if difficulty in ["Hard", "Expert"] else "Easy"
            elif overall >= 20:
                verdict = "Introductory / Brief Answer"
                next_diff = "Easy"
            else:
                verdict = "Incomplete / Insufficient"
                next_diff = "Easy"

            # Construct specific strengths
            strengths = []
            if concepts_covered:
                strengths.append(f"Correctly addressed core mechanisms: {', '.join(concepts_covered[:3])}.")
            if has_causal:
                strengths.append("Provided clear causal reasoning explaining the rationale behind design and technical choices.")
            if has_metric:
                strengths.append("Supported assertions with concrete metrics and quantifiable engineering outcomes.")
            if not strengths:
                if relevance_score >= 50:
                    strengths.append(f"Directly addressed the technical role of {skill} in the project workflow.")
                elif word_count >= 10:
                    strengths.append("Provided a relevant foundational response.")
                else:
                    strengths.append("Identified the core topic.")

            # Construct specific weaknesses
            weaknesses = []
            if concepts_missed:
                weaknesses.append(f"Missed discussing core architectural points: {', '.join(concepts_missed[:2])}.")
            if word_count < 20:
                weaknesses.append("Answer is brief; elaborate with specific libraries, methods, and practical production constraints.")
            if not has_tradeoff:
                weaknesses.append("Did not evaluate design trade-offs, potential drawbacks, or evaluated alternatives.")
            if not has_metric:
                weaknesses.append("Lacks quantifiable outcomes (e.g. latency figures, processing speed, accuracy %, memory reduction).")
            if hesitation_count > 0:
                weaknesses.append("Tone contains speculative phrasing ('I think', 'maybe'). State technical decisions assertively.")

            # Feedback summary
            if overall >= 75:
                feedback_summary = f"Strong answer ({overall}/100). Clear understanding of {skill} with solid technical context and mechanisms."
            elif overall >= 55:
                feedback_summary = f"Adequate answer ({overall}/100). Addresses {skill} effectively; expand on architectural trade-offs and concrete metrics."
            elif overall >= 35:
                feedback_summary = f"Developing answer ({overall}/100). Mentions {skill}, but needs deeper coverage of implementation mechanisms and alternatives."
            else:
                feedback_summary = f"Brief answer ({overall}/100). Elaborate with specific technical details, libraries, and design rationale."

        # Dynamically Synthesize Question-Tailored Suggested Model Answer
        if sample_answer and len(sample_answer.strip()) >= 20:
            overlap_words = set(lower_ans.split()).intersection(set(sample_answer.lower().split()))
            ratio_overlap = len(overlap_words) / max(1, len(set(sample_answer.lower().split())))
            if overall >= 75 or ratio_overlap >= 0.60:
                adv_context = f" Furthermore, to elevate this to Staff-level architecture, we establish distributed telemetry tracing and automated circuit breaking for {concepts_missed[0] if concepts_missed else 'high-load failure paths'}, maintaining <35ms p99 latency in production."
                candidate_improved = f"{sample_answer.rstrip('. ')}.{adv_context}"
            else:
                candidate_improved = sample_answer
        else:
            candidate_improved = diverse_model_ans

        improved_grounded, grounding_meta = GroundingValidator.validate_and_ground_answer(
            question_text=question_text,
            answer_text=candidate_improved,
            skill=skill,
            based_on=based_on,
            question_type="Technical",
            difficulty=difficulty,
            resume=resume_data,
            jd=jd_data
        )

        # Dynamic Follow-up Question
        if concepts_missed:
            follow_up = f"How would you address {concepts_missed[0]} if this {skill} implementation experienced a 10x traffic spike?"
        elif target_domain_obj and "follow_up" in target_domain_obj:
            follow_up = target_domain_obj["follow_up"]
        else:
            follow_up = f"If this {skill} implementation encountered a 10x spike in traffic or dataset size, where would the primary bottleneck emerge and how would you mitigate it?"

        star_fb = {
            "situation": "Clearly framed project/architecture context." if word_count >= 20 and relevance_score >= 40 else "Context could frame real-world system scale and constraints more clearly.",
            "task": f"Directly addressed requirement for {skill}." if relevance_score >= 50 else f"Target goal for {skill} needs sharper focus.",
            "action": f"Explained concrete implementation choices ({', '.join(concepts_covered[:2])})." if concepts_covered else f"Describe exact technical mechanisms of {skill} rather than high-level definitions.",
            "result": "Quantified impact and metrics included." if (has_metric if not is_domain_mismatch else False) else "Missing quantitative metrics (e.g. % improvement, latency reduction, bundle savings)."
        }

        return AnswerEvaluation(
            question_id=question_id,
            question_attempt_id=question_attempt_id,
            session_id=session_id,
            overall_score=overall,
            relevance_score=relevance_score,
            technical_accuracy_score=technical_accuracy,
            completeness_score=completeness,
            clarity_score=clarity,
            confidence_score=confidence,
            communication_score=communication,
            verdict_rating=verdict,
            question_intent=detected_intent,
            answer_structure=answer_structure,
            relevance_verdict=rel_verdict,
            concepts_covered=concepts_covered[:4],
            concepts_missed=concepts_missed[:4],
            strengths=strengths[:3],
            weaknesses=weaknesses[:3],
            improved_answer=improved_grounded or candidate_improved,
            follow_up_question=follow_up,
            next_recommended_difficulty=next_diff,
            feedback_summary=feedback_summary,
            star_feedback=star_fb,
            answer_grounding=grounding_meta
        )

    @classmethod
    def generate_project_deep_dive(cls, project_title: str, technologies: List[str], description: str) -> ProjectDeepDive:
        tech_list = technologies or ["Python", "FastAPI", "React", "MongoDB"]
        main_tech = tech_list[0] if tech_list else "Full Stack"
        db_tech = next((t for t in tech_list if t.lower() in ["mongodb", "postgresql", "mysql", "redis", "sqlite"]), "MongoDB / PostgreSQL")

        questions = [
            GroundedQuestion(
                question=f"Why did you choose {main_tech} for '{project_title}', and what other alternatives did you evaluate?",
                based_on=f"Project: {project_title}",
                skill=main_tech,
                difficulty="Medium",
                question_type="Project Based",
                why_this_question="Tests trade-off analysis and technical decision making in real systems.",
                expected_answer_points=[f"Key benefits of {main_tech}", "Why alternatives fell short", "Development speed vs performance"],
                sample_answer=f"We selected {main_tech} due to its high developer ergonomics, strong async ecosystem, and rapid API prototyping capabilities."
            ),
            GroundedQuestion(
                question=f"How is the data model designed in {db_tech} for '{project_title}', and how did you prevent performance bottlenecks?",
                based_on=f"Project: {project_title}",
                skill=db_tech,
                difficulty="Hard",
                question_type="Project Based",
                why_this_question="Evaluates database indexing, schema design, and query optimization.",
                expected_answer_points=["Document/Relational schema layout", "Indexing strategy for frequent queries", "Connection pooling"],
                sample_answer="We established indexes on foreign keys/lookup IDs and implemented pagination to avoid unbounded data retrieval."
            ),
            GroundedQuestion(
                question=f"What was the most challenging bug or architectural bottleneck you encountered in '{project_title}' and how did you resolve it?",
                based_on=f"Project: {project_title}",
                skill="System Architecture",
                difficulty="Hard",
                question_type="Project Based",
                why_this_question="Assesses debugging persistence, root-cause analysis, and incident resolution.",
                expected_answer_points=["Symptom and reproduction", "Profiling/logging methodology", "Root cause and permanent fix"],
                sample_answer="Walk through a concrete latency or state synchronization issue, how you profiled it, and the refactoring applied."
            ),
            GroundedQuestion(
                question=f"How did you implement security, authentication, and input validation in '{project_title}'?",
                based_on=f"Project: {project_title}",
                skill="Security & Validation",
                difficulty="Medium",
                question_type="Project Based",
                why_this_question="Checks secure coding practices, CORS, JWT handling, and input sanitization.",
                expected_answer_points=["JWT/Session auth", "Pydantic/Schema validation", "CORS policy and rate limiting"],
                sample_answer="All incoming payloads are strictly validated using schema models, and stateful endpoints require signed JWT bearer tokens."
            ),
            GroundedQuestion(
                question=f"If '{project_title}' needed to handle 10,000 requests per second, what changes would you introduce in caching and infrastructure?",
                based_on=f"Project: {project_title}",
                skill="Scalability",
                difficulty="Expert",
                question_type="Project Based",
                why_this_question="Tests horizontal scalability, distributed caching, and microservices readiness.",
                expected_answer_points=["Redis caching layer", "Load balancing with Nginx/k8s", "Database read replicas", "Asynchronous worker queues"],
                sample_answer="Introduce Redis for caching hot reads, decouple compute with background worker queues (Celery), and scale stateless backend instances behind a reverse proxy."
            )
        ]

        return ProjectDeepDive(
            project_name=project_title,
            objective=f"Develop a robust, user-centric application solving core workflow automation using {', '.join(tech_list[:3])}.",
            problem_statement=description[:250] if description else f"Providing seamless and responsive operations with real-time feedback for users.",
            architecture=f"Client-Server architecture with modular {tech_list[0] if tech_list else 'modern'} frontend communicating via RESTful APIs to an asynchronous Python backend, backed by {db_tech}.",
            technologies=tech_list,
            database_choice=f"Utilized {db_tech} for flexible schema management, high-throughput writes, and rapid iteration during development.",
            apis_design="RESTful JSON APIs adhering to standard HTTP verbs, structured error payloads, and Pydantic request/response validation.",
            challenges_solutions="Managing asynchronous state consistency and preventing query latency spikes by adding targeted indexing.",
            security_aspects="Token-based authentication, strict CORS origins, environment variable separation for secrets, and input sanitization.",
            scalability_notes="Stateless application design allowing horizontal container scaling across Docker/Kubernetes pods.",
            testing_strategy="Unit testing of core utility functions and end-to-end API integration tests verifying valid and error boundary conditions.",
            deployment_details="Containerized via Docker, automated CI/CD pipeline via GitHub Actions for testing and deployment.",
            future_improvements="Integrating real-time WebSocket notifications, advanced caching with Redis, and AI-driven automated recommendations.",
            interview_questions=questions
        )

    @classmethod
    def generate_resume_improvements(cls, resume: ExtractedResume) -> List[ResumeImprovementItem]:
        improvements: List[ResumeImprovementItem] = []

        # Check project descriptions for metrics
        has_metrics = any(re.search(r'\d+%|\d+x|\$\d+|\d+\s*(?:users|ms|seconds|hours)', p.description or "") for p in resume.projects)
        if not has_metrics:
            improvements.append(ResumeImprovementItem(
                category="Impact & Metrics",
                issue="Projects lack quantifiable results and business impact metrics.",
                suggestion="Use the Google X-Y-Z formula: 'Accomplished [X] as measured by [Y], by doing [Z]'.",
                impact_level="High",
                example_before="Built an API that processes user resumes and generates questions.",
                example_after="Architected an async FastAPI service processing 500+ resumes with <200ms latency, improving preparation speed by 40%."
            ))

        # Check action verbs
        weak_verbs = ["worked on", "helped with", "responsible for", "handled"]
        has_weak = any(any(v in (p.description or "").lower() for v in weak_verbs) for p in resume.projects)
        if has_weak or len(resume.projects) > 0:
            improvements.append(ResumeImprovementItem(
                category="Action Verbs",
                issue="Avoid passive phrases like 'worked on' or 'helped with'.",
                suggestion="Begin bullet points with strong power action verbs like 'Architected', 'Engineered', 'Optimized', 'Deployed'.",
                impact_level="Medium",
                example_before="Worked on the database integration and frontend UI.",
                example_after="Engineered responsive React interface and optimized MongoDB aggregation pipelines reducing load times by 35%."
            ))

        # Check skills grouping
        if len(resume.skills) < 8:
            improvements.append(ResumeImprovementItem(
                category="Skills Section",
                issue="Technical skill inventory could be more comprehensive.",
                suggestion="Explicitly list Languages, Frontend, Backend, Databases, Cloud & DevOps, and Testing tools in categorized groupings.",
                impact_level="High",
                example_before="Skills: Python, React, Database",
                example_after="Languages: Python, JavaScript, TypeScript | Backend: FastAPI, Node.js | Databases: MongoDB, PostgreSQL | DevOps: Docker, Git"
            ))

        # Check achievements
        if not resume.achievements:
            improvements.append(ResumeImprovementItem(
                category="Achievements & Leadership",
                issue="Missing a dedicated achievements or extracurricular leadership section.",
                suggestion="Highlight hackathons, open-source pull requests, certifications, or academic honors.",
                impact_level="Medium",
                example_before="No achievements section listed.",
                example_after="Finalist in University Hackathon 2024 (Top 5 of 120 teams) | Published open-source React component with 200+ GitHub stars."
            ))

        return improvements

    @classmethod
    def generate_preparation_topics(cls, resume: ExtractedResume, jd: Optional[JobDescriptionAnalysis] = None) -> List[TopicPreparationItem]:
        topics: List[TopicPreparationItem] = []
        skills = resume.skills if resume.skills else ["Python", "SQL", "React", "MongoDB", "FastAPI"]
        
        for s in skills[:8]:
            topics.append(TopicPreparationItem(
                topic=f"{s} Core Architecture & Internals",
                importance="High",
                why_it_matters=f"Frequently examined in live interviews to verify deep hands-on expertise beyond basic syntax.",
                resume_evidence=f"Featured prominently in your skills and project implementations.",
                expected_questions=[
                    f"How does {s} manage concurrency / memory?",
                    f"What are the common pitfalls and performance trade-offs in {s}?",
                    f"Explain a production scenario where you debugged an issue in {s}."
                ],
                recommended_level="Intermediate to Advanced"
            ))

        # Add System Design and Behavioral
        topics.append(TopicPreparationItem(
            topic="System Design & Scalability",
            importance="High",
            why_it_matters="Crucial for demonstrating engineering maturity, caching strategy, and database scaling.",
            resume_evidence=f"Demonstrated across your project architectures: {', '.join([p.title for p in resume.projects[:2]]) or 'Web applications'}.",
            expected_questions=[
                "How would you design a rate limiter or URL shortener?",
                "How do you ensure zero data loss during high database write traffic?",
                "When should you decouple monolithic services into microservices?"
            ],
            recommended_level="Intermediate"
        ))

        topics.append(TopicPreparationItem(
            topic="Behavioral & STAR Method Communication",
            importance="Medium",
            why_it_matters="Assesses culture fit, conflict resolution, ownership, and cross-functional teamwork.",
            resume_evidence="Evaluated across your past work experience and team project collaborations.",
            expected_questions=[
                "Tell me about a time you resolved a major production bug.",
                "How do you handle scope changes or tight release deadlines?",
                "Describe a situation where you convinced a team to adopt a better tech stack."
            ],
            recommended_level="All Candidates"
        ))

        return topics[:10]

    @classmethod
    async def generate_final_interview_evaluation(
        cls,
        questions: List[GroundedQuestion],
        evaluations: List[AnswerEvaluation],
        resume: Optional[ExtractedResume] = None,
        jd: Optional[JobDescriptionAnalysis] = None
    ) -> FinalInterviewEvaluation:
        """Generates a holistic, synthesis final evaluation report after completing all interview questions."""
        total_evals = len(evaluations)
        if total_evals == 0:
            return FinalInterviewEvaluation(
                overall_score=0,
                hiring_verdict="Not Evaluated",
                verdict_badge="danger",
                executive_summary="No interview answers were submitted for evaluation.",
                competency_scores={
                    "Technical Depth": 0,
                    "Relevance": 0,
                    "Completeness": 0,
                    "Clarity": 0,
                    "Confidence": 0,
                    "Communication": 0
                },
                key_strengths=[],
                critical_weaknesses=["No questions were answered during this session."],
                missed_concepts=[],
                per_question_breakdown=[],
                actionable_recommendations=["Complete a full set of mock interview questions to generate a performance evaluation."],
                total_questions=0
            )

        # Build Question Map
        q_map = {q.id: q for q in questions}

        # Calculate Averages across 6 axes
        overall_scores = [e.overall_score for e in evaluations]
        avg_overall = int(sum(overall_scores) / total_evals)

        avg_tech = int(sum(e.technical_accuracy_score for e in evaluations) / total_evals)
        avg_rel = int(sum(e.relevance_score for e in evaluations) / total_evals)
        avg_comp = int(sum(e.completeness_score for e in evaluations) / total_evals)
        avg_clar = int(sum(e.clarity_score for e in evaluations) / total_evals)
        avg_conf = int(sum(e.confidence_score for e in evaluations) / total_evals)
        avg_comm = int(sum(e.communication_score for e in evaluations) / total_evals)

        competency_scores = {
            "Technical Depth": avg_tech,
            "Relevance": avg_rel,
            "Completeness": avg_comp,
            "Clarity": avg_clar,
            "Confidence": avg_conf,
            "Communication": avg_comm
        }

        # Per-question breakdown
        breakdown: List[QuestionEvaluationSummaryItem] = []
        all_strengths: List[str] = []
        all_weaknesses: List[str] = []
        all_missed_concepts: List[str] = []

        for e in evaluations:
            q = q_map.get(e.question_id)
            q_text = q.question if q else "Interview Question"
            q_skill = q.skill if q else "General"
            q_diff = q.difficulty if q else "Medium"

            for s in e.strengths:
                if s and s not in all_strengths and not s.startswith("Submitted text, but no"):
                    all_strengths.append(s)
            for w in e.weaknesses:
                if w and w not in all_weaknesses:
                    all_weaknesses.append(w)
            for m in (e.concepts_missed or []):
                if m and m not in all_missed_concepts:
                    all_missed_concepts.append(m)

            breakdown.append(QuestionEvaluationSummaryItem(
                question_id=e.question_id,
                question_text=q_text,
                skill=q_skill,
                difficulty=q_diff,
                score=e.overall_score,
                verdict=e.verdict_rating or ("Strong Answer" if e.overall_score >= 70 else "Needs Improvement"),
                user_answer_snippet=e.improved_answer[:120] + "..." if e.improved_answer else "",
                key_feedback=e.feedback_summary or ("Good technical foundation with minor gaps." if e.overall_score >= 70 else "Review core concepts and trade-offs."),
                strengths=e.strengths or [],
                missed_concepts=e.concepts_missed or []
            ))

        # Hiring Verdict
        if avg_overall >= 85:
            verdict = "Strong Hire"
            verdict_badge = "success"
        elif avg_overall >= 70:
            verdict = "Hire"
            verdict_badge = "success"
        elif avg_overall >= 55:
            verdict = "Lean Hire"
            verdict_badge = "warning"
        elif avg_overall >= 35:
            verdict = "Needs Technical Depth"
            verdict_badge = "warning"
        else:
            verdict = "Not Recommended / Significant Gaps"
            verdict_badge = "danger"

        # Try Gemini LLM for high-level executive synthesis if API key is configured
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                candidate_name = resume.name if resume else "Candidate"
                target_role = jd.title if jd else "Target Engineering Role"

                eval_summaries = []
                for b in breakdown:
                    eval_summaries.append(f"- Question: '{b.question_text}' (Skill: {b.skill}, Diff: {b.difficulty}) -> Score: {b.score}/100, Verdict: {b.verdict}, Feedback: {b.key_feedback}")

                prompt = f"""You are a Principal Engineering Hiring Director at a leading tech firm evaluating a full mock interview session.
Candidate: {candidate_name}
Target Role: {target_role}
Total Questions Evaluated: {total_evals}
Average Overall Score: {avg_overall}/100
Average Technical Depth: {avg_tech}/100
Average Communication: {avg_comm}/100

PER-QUESTION RESULTS:
{chr(10).join(eval_summaries)}

AGGREGATED MISSED CONCEPTS:
{', '.join(all_missed_concepts[:10]) if all_missed_concepts else 'None'}

Provide an executive synthesis in valid JSON format:
{{
  "executive_summary": "3-4 concise sentences synthesizing the candidate's overall readiness, strengths, architectural depth, and core vulnerabilities.",
  "hiring_verdict": "{verdict}",
  "top_strengths": ["3 prioritized, specific technical strengths demonstrated"],
  "critical_weaknesses": ["3 prioritized areas where the candidate showed technical gaps or omitted trade-offs"],
  "actionable_recommendations": ["3-4 concrete next steps / study priorities the candidate should complete before live interviews"]
}}"""

                response = None
                for m_name in ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']:
                    try:
                        response = client.models.generate_content(
                            model=m_name,
                            contents=prompt
                        )
                        if response and response.text:
                            break
                    except Exception as e:
                        logger.debug(f"Gemini {m_name} failed in final evaluation: {e}")
                        continue

                if not response or not response.text:
                    raise RuntimeError("Gemini model final evaluation returned empty response")

                text = response.text.strip()
                if text.startswith("```json"):
                    text = text.split("```json")[1].split("```")[0].strip()
                elif text.startswith("```"):
                    text = text.split("```")[1].split("```")[0].strip()

                data = json.loads(text)

                return FinalInterviewEvaluation(
                    overall_score=avg_overall,
                    hiring_verdict=data.get("hiring_verdict", verdict),
                    verdict_badge=verdict_badge,
                    executive_summary=data.get("executive_summary", f"{candidate_name} completed {total_evals} interview questions with an overall score of {avg_overall}/100."),
                    competency_scores=competency_scores,
                    key_strengths=data.get("top_strengths", all_strengths[:4]),
                    critical_weaknesses=data.get("critical_weaknesses", all_weaknesses[:4]),
                    missed_concepts=all_missed_concepts[:8],
                    per_question_breakdown=breakdown,
                    actionable_recommendations=data.get("actionable_recommendations", [
                        "Deepen knowledge in system architecture trade-offs and performance bottlenecks.",
                        "Structure responses using the STAR method with quantifiable outcome metrics.",
                        "Practice explaining underlying mechanisms rather than high-level tool definitions."
                    ]),
                    total_questions=total_evals
                )
            except Exception as e:
                logger.warning(f"Gemini final evaluation fallback: {e}")

        # Deterministic fallback synthesis
        candidate_name = resume.name if resume else "The candidate"
        target_role = jd.title if jd else "the target role"

        if avg_overall >= 80:
            exec_summary = (
                f"{candidate_name} demonstrated strong technical competence across the question set with an average score of {avg_overall}/100. "
                f"Answers reflected solid domain knowledge, clear architectural reasoning, and direct problem-solving alignment for {target_role}. "
                f"Minor refinements in articulating production edge cases and scaling trade-offs will further solidify their performance."
            )
        elif avg_overall >= 60:
            exec_summary = (
                f"{candidate_name} completed the interview session with an adequate foundation, scoring {avg_overall}/100 across {total_evals} questions. "
                f"While core concepts were understood, several answers lacked deep technical mechanics and concrete metrics. "
                f"Focusing on system design nuances and structured communication will elevate performance to the next tier."
            )
        else:
            exec_summary = (
                f"{candidate_name} achieved an overall score of {avg_overall}/100 across {total_evals} questions, indicating noticeable technical and communication gaps. "
                f"Key concepts were omitted in several technical questions, and responses often lacked trade-off analyses. "
                f"Dedicated preparation on fundamental system mechanics and hands-on implementation details is strongly recommended."
            )

        # Default actionable recommendations
        action_recs = []
        if avg_tech < 70:
            action_recs.append("Review underlying framework and database mechanics (e.g., indexing strategies, async event loops, caching layers).")
        if avg_comp < 70:
            action_recs.append("Always include architectural trade-offs, alternative approaches evaluated, and failure modes in technical answers.")
        if avg_comm < 70 or avg_clar < 70:
            action_recs.append("Structure answers using the STAR methodology (Situation, Task, Action, Result) to deliver concise, impact-focused explanations.")
        if not action_recs:
            action_recs = [
                "Practice high-concurrency system design scenarios and real-time distributed architecture trade-offs.",
                "Incorporate specific benchmark numbers, latency figures, and business impact metrics into your responses.",
                "Review edge case handling, error boundaries, and observability patterns across your tech stack."
            ]

        return FinalInterviewEvaluation(
            overall_score=avg_overall,
            hiring_verdict=verdict,
            verdict_badge=verdict_badge,
            executive_summary=exec_summary,
            competency_scores=competency_scores,
            key_strengths=all_strengths[:4] if all_strengths else ["Demonstrated familiarity with target technical domain.", "Engaged with the interview format constructively."],
            critical_weaknesses=all_weaknesses[:4] if all_weaknesses else ["Could expand more on trade-offs and alternative solutions."],
            missed_concepts=all_missed_concepts[:8],
            per_question_breakdown=breakdown,
            actionable_recommendations=action_recs,
            total_questions=total_evals
        )

