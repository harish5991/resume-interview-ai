export const FALLBACK_RESUMES = [
  {
    id: "sample-fullstack",
    title: "Alex Chen — Full Stack Developer (React & Python)",
    name: "Alex Chen",
    email: "alex.chen@example.com",
    phone: "+1 (555) 234-5678",
    location: "San Francisco, CA",
    summary: "Full Stack Software Engineer with 3+ years experience building scalable web applications using React, Python, FastAPI, and MongoDB.",
    skills: ["Python", "JavaScript", "TypeScript", "React", "FastAPI", "Node.js", "MongoDB", "PostgreSQL", "Docker", "Git", "REST APIs", "Tailwind CSS"],
    skill_categories: {
      "Languages": ["Python", "JavaScript", "TypeScript"],
      "Frontend": ["React", "Tailwind CSS"],
      "Backend & APIs": ["FastAPI", "Node.js", "REST APIs"],
      "Databases": ["MongoDB", "PostgreSQL"],
      "Cloud & DevOps": ["Docker", "Git"]
    },
    experience: [
      {
        role: "Full Stack Engineer",
        company: "CloudScale Systems",
        duration: "2022 - Present",
        location: "San Francisco, CA",
        responsibilities: [
          "Engineered asynchronous REST APIs using FastAPI and MongoDB serving 50k+ daily active users.",
          "Built real-time dashboard in React with modular state management and responsive styling.",
          "Containerized microservices using Docker and implemented CI/CD deployment pipelines."
        ],
        technologies: ["Python", "FastAPI", "React", "MongoDB", "Docker"]
      }
    ],
    projects: [
      {
        title: "Resume Interview AI",
        description: "An AI-powered interview preparation platform that analyzes candidate resumes and generates grounded, explainable questions with adaptive mock interview scoring.",
        technologies: ["Python", "FastAPI", "React", "MongoDB", "Tailwind CSS"],
        highlights: [
          "Implemented TF-IDF cosine matching and PyMuPDF text extraction pipeline.",
          "Designed 6-axis answer evaluation system with dynamic difficulty scaling.",
          "Built clean responsive frontend with Recharts analytics and PDF report export."
        ]
      },
      {
        title: "Distributed Task Queue",
        description: "High-throughput asynchronous job processing system with Redis-backed message broker and worker pooling.",
        technologies: ["Python", "Redis", "Docker", "PostgreSQL"],
        highlights: [
          "Handled 10k messages/minute with automatic retry and dead-letter queue recovery.",
          "Implemented token-bucket rate limiting middleware to prevent worker starvation."
        ]
      },
      {
        title: "Smart Traffic Vision & Monitoring Platform",
        description: "Real-time edge computer vision platform for vehicular density tracking and traffic light orchestration.",
        technologies: ["Python", "YOLOv8", "OpenCV", "FastAPI", "Docker"],
        highlights: [
          "Trained YOLOv8 object detector achieving 38 FPS inference on HD video streams.",
          "Constructed OpenCV ROI pipeline reducing false positive bounding boxes by 34%."
        ]
      }
    ],
    education: [
      {
        degree: "B.S. in Computer Science",
        institution: "University of California, Berkeley",
        year: "2022"
      }
    ],
    certifications: [
      { name: "AWS Certified Solutions Architect — Associate" }
    ],
    achievements: [
      "1st Place Winner at Berkeley AI Hackathon 2023",
      "Published open-source React component with 400+ GitHub stars"
    ],
    raw_text: "Alex Chen\nFull Stack Software Engineer\nalex.chen@example.com | San Francisco, CA\n\nSKILLS\nLanguages: Python, JavaScript, TypeScript\nFrontend: React, Tailwind CSS\nBackend: FastAPI, Node.js, REST APIs\nDatabases: MongoDB, PostgreSQL\nDevOps: Docker, Git\n\nEXPERIENCE\nFull Stack Engineer | CloudScale Systems (2022 - Present)\n• Engineered asynchronous REST APIs using FastAPI and MongoDB serving 50k+ daily active users.\n• Built real-time dashboard in React with modular state management.\n• Containerized microservices using Docker and CI/CD pipelines.\n\nPROJECTS\nResume Interview AI | Python, FastAPI, React, MongoDB\n• Implemented TF-IDF cosine matching and PyMuPDF text extraction pipeline.\n• Designed 6-axis answer evaluation system with dynamic difficulty scaling.\n• Built clean responsive frontend with Recharts analytics and PDF report export.\n\nDistributed Task Queue | Python, Redis, Docker, PostgreSQL\n• Handled 10k messages/minute with automatic retry and dead-letter queue recovery.\n\nSmart Traffic Vision & Monitoring Platform | Python, YOLOv8, OpenCV, FastAPI\n• Trained YOLOv8 object detector achieving 38 FPS inference on HD video streams.\n\nEDUCATION\nB.S. in Computer Science | UC Berkeley (2022)"
  },
  {
    id: "sample-backend",
    title: "Samantha Ray — Python & Backend Systems Engineer",
    name: "Samantha Ray",
    email: "samantha.ray@example.com",
    phone: "+1 (555) 890-1234",
    location: "Austin, TX",
    summary: "Backend Software Engineer specializing in distributed Python services, SQL optimization, Redis caching, and microservices architecture.",
    skills: ["Python", "FastAPI", "Django", "SQL", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS", "Kafka", "Microservices", "CI/CD"],
    skill_categories: {
      "Languages": ["Python", "SQL"],
      "Backend & APIs": ["FastAPI", "Django", "Microservices"],
      "Databases": ["PostgreSQL", "Redis"],
      "Cloud & DevOps": ["Docker", "Kubernetes", "AWS", "Kafka", "CI/CD"]
    },
    experience: [
      {
        role: "Backend Engineer",
        company: "Apex Data Corp",
        duration: "2021 - 2024",
        location: "Austin, TX",
        responsibilities: [
          "Architected high-throughput data ingestion pipelines using Kafka and Python.",
          "Optimized complex PostgreSQL relational queries reducing p99 latency from 450ms to 60ms.",
          "Maintained 99.95% API uptime across Kubernetes clusters on AWS."
        ],
        technologies: ["Python", "PostgreSQL", "Kafka", "Docker", "AWS"]
      }
    ],
    projects: [
      {
        title: "Real-time Event Ingestion Service",
        description: "High-throughput asynchronous data streaming pipeline processing 25,000 events/sec with fault tolerance.",
        technologies: ["Python", "FastAPI", "Kafka", "PostgreSQL"],
        highlights: [
          "Architected Kafka partition consumers with batch database insertion.",
          "Implemented dead-letter queues and Prometheus latency alerting metrics."
        ]
      },
      {
        title: "Intelligent Traffic Management System",
        description: "Automated video stream vehicle detection and adaptive traffic light signal scheduling system.",
        technologies: ["Python", "YOLOv8", "OpenCV", "FastAPI", "PostgreSQL"],
        highlights: [
          "Engineered OpenCV frame preprocessing with multi-lane vehicle detection using YOLOv8.",
          "Integrated FastAPI telemetry endpoints delivering sub-30ms real-time status updates."
        ]
      },
      {
        title: "Distributed Redis Cache Gateway",
        description: "High-concurrency caching layer providing sub-millisecond query offloading for database read replicas.",
        technologies: ["Python", "Redis", "Docker", "FastAPI"],
        highlights: [
          "Reduced primary database read IOPS by 74% using write-through cache invalidation.",
          "Implemented token-bucket rate limiting middleware for public API consumers."
        ]
      }
    ],
    education: [
      {
        degree: "B.Tech in Information Technology",
        institution: "Texas Tech University",
        year: "2021"
      }
    ],
    certifications: [
      { name: "HashiCorp Certified Terraform Associate" }
    ],
    achievements: [
      "Delivered zero-downtime database migration for 10M+ user records"
    ],
    raw_text: "Samantha Ray\nBackend Software Engineer\nsamantha.ray@example.com | Austin, TX\n\nSKILLS: Python, FastAPI, Django, SQL, PostgreSQL, Redis, Docker, Kubernetes, AWS, Kafka, Microservices\n\nEXPERIENCE:\nBackend Engineer at Apex Data Corp (2021 - 2024)\n• Architected high-throughput data ingestion pipelines using Kafka and Python.\n• Optimized complex PostgreSQL queries reducing p99 latency by 85%.\n\nPROJECTS:\nReal-time Event Ingestion Service | Python, FastAPI, Kafka, PostgreSQL\n• Processed 25,000 events/second with async connection pooling.\n\nEDUCATION:\nB.Tech in Information Technology, Texas Tech University (2021)"
  }
];

export const FALLBACK_JDS = [
  {
    id: "jd-fullstack",
    title: "Full Stack Engineer (React, Python & Cloud)",
    company: "NextGen Technologies",
    experience_years: "2-4+ years",
    required_skills: ["Python", "FastAPI", "React", "TypeScript", "MongoDB", "PostgreSQL", "Docker", "REST APIs"],
    preferred_skills: ["AWS", "Redis", "CI/CD", "Tailwind CSS", "Microservices"],
    responsibilities: [
      "Design and build responsive frontend user interfaces using React and modern CSS.",
      "Architect robust RESTful APIs in Python (FastAPI/Django) and manage database schema migrations.",
      "Write comprehensive automated unit and integration tests.",
      "Collaborate with product and design teams in an agile environment."
    ],
    technologies: ["Python", "FastAPI", "React", "TypeScript", "MongoDB", "PostgreSQL", "Docker", "REST APIs", "AWS", "Redis", "CI/CD"],
    keywords: ["FastAPI", "React", "Python", "MongoDB", "REST APIs", "Docker", "TypeScript", "PostgreSQL", "Agile"],
    summary: "Seeking a talented Full Stack Developer to build modern cloud applications using React, Python, and MongoDB.",
    raw_text: "Full Stack Engineer (React, Python & Cloud) at NextGen Technologies\nLocation: Remote / Hybrid\nExperience: 2-4+ years\n\nJob Summary:\nWe are looking for a passionate Full Stack Engineer proficient in React and Python/FastAPI to design, build, and maintain high-performance web applications.\n\nRequired Qualifications:\n• Strong proficiency with Python and modern web frameworks like FastAPI or Django\n• Hands-on experience building frontend web applications with React and TypeScript\n• Solid understanding of SQL (PostgreSQL) and NoSQL (MongoDB) databases\n• Experience with REST APIs, containerization using Docker, and Git\n\nPreferred Qualifications:\n• Experience with AWS cloud infrastructure and Redis caching\n• Familiarity with CI/CD automation pipelines and Tailwind CSS\n\nResponsibilities:\n• Develop modular web components in React and clean REST endpoints in FastAPI\n• Optimize database query performance and maintain data integrity\n• Participate in code reviews and agile sprints"
  },
  {
    id: "jd-data-analyst",
    title: "Data Analyst & Business Intelligence Specialist",
    company: "Insight Analytics Corp",
    experience_years: "1-3+ years",
    required_skills: ["Python", "SQL", "Power BI", "Tableau", "Pandas", "Data Analysis"],
    preferred_skills: ["PostgreSQL", "Scikit-Learn", "Machine Learning", "Excel"],
    responsibilities: [
      "Build interactive dashboards and KPI reports in Power BI and Tableau.",
      "Write complex SQL queries and data transformation scripts in Python (Pandas/NumPy).",
      "Perform statistical analysis to identify trends and operational bottlenecks.",
      "Present actionable findings to executive stakeholders."
    ],
    technologies: ["Python", "SQL", "Power BI", "Tableau", "Pandas", "PostgreSQL", "Data Analysis"],
    keywords: ["SQL", "Power BI", "Tableau", "Python", "Pandas", "Dashboards", "Metrics", "Analytics"],
    summary: "Join our analytics team to build data pipelines, interactive dashboards in Power BI and Tableau, and deliver business insights.",
    raw_text: "Data Analyst & Business Intelligence Specialist at Insight Analytics Corp\nExperience: 1-3+ years\n\nRequirements:\n• Strong proficiency in SQL for extracting and aggregating complex datasets\n• Proven experience creating dashboards with Power BI and Tableau\n• Working knowledge of Python and Pandas for data manipulation\n• Excellent communication skills for presenting analytical findings\n\nResponsibilities:\n• Create automated reporting dashboards for business leadership\n• Identify patterns and KPI trends using statistical analysis"
  }
];
