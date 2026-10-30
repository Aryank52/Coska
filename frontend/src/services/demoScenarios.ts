export interface DemoScenario {
  id: string
  name: string
  service: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  symptoms: string
  errorRate: string
  blastRadius: string[]
  databaseStatus: string
  expectedRootCause: string
  verificationState: 'VERIFIED' | 'READY' | 'RUNNING'
  configBefore: string
  configAfter: string
  configKey: string
  risk: string
  rollback: string
  expectedEffect: string
  traceSteps: Array<{
    id: string
    title: string
    tool?: string
    durationMs: number
    status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING'
  }>
  ragDocuments: Array<{
    title: string
    similarity: number
    source: string
    summary: string
    category: string
    whyRetrieved: string
  }>
  causalGraph: {
    nodes: Array<{
      id: string
      label: string
      sublabel: string
      type: 'root' | 'event' | 'symptom' | 'impact'
    }>
    edges: Array<{ from: string; to: string }>
  }
  hypotheses: Array<{
    id: string
    title: string
    confidence: number
    isLeading: boolean
    supportingEvidence: string[]
    rejectedReason?: string
  }>
  rootCause: {
    title: string
    confidence: number
    supportingCount: number
    contradictingCount: number
    whySummary: string
  }
  verification: {
    baseline: { status: 'FAILED'; label: 'FAILED (Expected failure)'; code: 1 }
    postfix: { status: 'PASSED'; label: 'PASSED (Fix resolved problem)'; code: 0 }
    health: { status: 'PASSED'; label: 'PASSED (200 OK)'; code: 0 }
    control: { status: 'FAILED'; label: 'FAILED (Proves causality)'; code: 1 }
    receiptId: string
    timestamp: string
  }
}

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: 'payment_pool_exhaustion',
    name: 'Payment Pool Exhaustion',
    service: 'payment-api',
    severity: 'CRITICAL',
    symptoms: 'HTTP 500 error rate spiked from 1.2% to 38% under 20 concurrent transactions.',
    errorRate: '1.2% → 38%',
    blastRadius: ['Checkout Service', 'Payment Gateway', 'Order Processing'],
    databaseStatus: 'Connection Timeout (QueuePool exhausted)',
    expectedRootCause: 'Database Connection Pool Exhaustion (DB_POOL_SIZE=5)',
    verificationState: 'VERIFIED',
    configBefore: 'DB_POOL_SIZE=5\nDB_POOL_TIMEOUT=5\nDATABASE_URL=sqlite+aiosqlite:///./payments.db',
    configAfter: 'DB_POOL_SIZE=30\nDB_POOL_TIMEOUT=5\nDATABASE_URL=sqlite+aiosqlite:///./payments.db',
    configKey: 'DB_POOL_SIZE: 5 -> 30',
    risk: 'LOW',
    rollback: 'Available (revert DB_POOL_SIZE to 5)',
    expectedEffect: 'Increase connection capacity from 5 to 30 workers, eliminating pool starvation.',
    traceSteps: [
      { id: '1', title: 'Incident received: HTTP 500 error spike on payment-api', tool: 'telemetry_listener', durationMs: 40, status: 'COMPLETED' },
      { id: '2', title: 'Planner created autonomous investigation plan', tool: 'orchestrator', durationMs: 120, status: 'COMPLETED' },
      { id: '3', title: 'Inspecting logs: Found 17 connection pool timeouts in 90s', tool: 'inspect_logs', durationMs: 310, status: 'COMPLETED' },
      { id: '4', title: 'Inspecting configuration: Discovered DB_POOL_SIZE=5', tool: 'inspect_configuration', durationMs: 180, status: 'COMPLETED' },
      { id: '5', title: 'Retrieving operational knowledge: 3 runbooks matched', tool: 'rag_engine', durationMs: 240, status: 'COMPLETED' },
      { id: '6', title: 'Comparing hypotheses: Formulated 4 competing candidates', tool: 'hypothesis_engine', durationMs: 410, status: 'COMPLETED' },
      { id: '7', title: 'External research: PostgreSQL connection pool sizing heuristics', tool: 'tavily', durationMs: 580, status: 'COMPLETED' },
      { id: '8', title: 'Root cause identified: Database Connection Pool Exhaustion (92%)', tool: 'nemotron_ai', durationMs: 350, status: 'COMPLETED' },
      { id: '9', title: 'Remediation simulated: DB_POOL_SIZE scaled to 30', tool: 'sandbox_engine', durationMs: 290, status: 'COMPLETED' },
      { id: '10', title: 'Baseline test: Reproduced failure under DB_POOL_SIZE=5 (FAILED)', tool: 'verifier', durationMs: 450, status: 'COMPLETED' },
      { id: '11', title: 'Post-fix test: Verified recovery under DB_POOL_SIZE=30 (PASSED)', tool: 'verifier', durationMs: 480, status: 'COMPLETED' },
      { id: '12', title: 'Health verification: HTTP 200 OK across all synthetic probes (PASSED)', tool: 'verifier', durationMs: 260, status: 'COMPLETED' },
      { id: '13', title: 'Control test: Reverted fix; verified failure strictly returns (FAILED)', tool: 'verifier', durationMs: 510, status: 'COMPLETED' },
      { id: '14', title: 'VERIFIED: Causal recovery proven by independent control execution', tool: 'verifier', durationMs: 60, status: 'COMPLETED' },
    ],
    ragDocuments: [
      {
        title: 'PostgreSQL Pool Exhaustion Runbook',
        similarity: 94,
        source: 'docs/runbooks/postgres-pool.md',
        summary: 'Under high request concurrency, undersized connection pools cause queue starvation and HTTP 500 timeouts.',
        category: 'Database / Operations',
        whyRetrieved: 'Matched incident symptoms: connection pool + timeout + HTTP 500',
      },
      {
        title: 'Payment API Postmortem (INC-2025-08)',
        similarity: 88,
        source: 'docs/postmortems/payment-api-timeout.md',
        summary: 'Historical postmortem where DB_POOL_SIZE was accidentally set to 5 after staging merge, causing payment failures.',
        category: 'Postmortems',
        whyRetrieved: 'Matched service payment-api and connection pool exhaustion signature',
      },
      {
        title: 'Database Timeout Troubleshooting Guide',
        similarity: 81,
        source: 'docs/guides/db-timeouts.md',
        summary: 'Best practices for distinguishing between slow queries, network saturation, and client pool starvation.',
        category: 'Architecture Guides',
        whyRetrieved: 'Matched error signature: QueuePool limit exceeded',
      },
    ],
    causalGraph: {
      nodes: [
        { id: 'n1', label: 'DB_POOL_SIZE=5', sublabel: 'Root Configuration', type: 'root' },
        { id: 'n2', label: 'Connection Exhaustion', sublabel: 'Resource Starvation', type: 'event' },
        { id: 'n3', label: 'Database Timeout', sublabel: 'QueuePool Limit (5s)', type: 'event' },
        { id: 'n4', label: 'Payment API Failure', sublabel: 'Worker Thread Crash', type: 'symptom' },
        { id: 'n5', label: 'HTTP 500 Spike', sublabel: '1.2% → 38% Error Rate', type: 'impact' },
      ],
      edges: [
        { from: 'n1', to: 'n2' },
        { from: 'n2', to: 'n3' },
        { from: 'n3', to: 'n4' },
        { from: 'n4', to: 'n5' },
      ],
    },
    hypotheses: [
      {
        id: 'H1',
        title: 'Database Connection Pool Exhaustion',
        confidence: 92,
        isLeading: true,
        supportingEvidence: ['DB_POOL_SIZE=5 in .env', '17 connection pool timeouts in logs', 'QueuePool limit exceeded'],
      },
      {
        id: 'H2',
        title: 'Database Host CPU/IOPS Saturation',
        confidence: 61,
        isLeading: false,
        supportingEvidence: ['Increased concurrency during flash traffic'],
        rejectedReason: 'Database CPU utilization remained at 18%; only client connection queue was starved.',
      },
      {
        id: 'H3',
        title: 'Network Partition / Instability',
        confidence: 23,
        isLeading: false,
        supportingEvidence: ['Intermittent connection timeouts'],
        rejectedReason: 'Database host responds to direct ping in 0.4ms; no packet loss detected.',
      },
      {
        id: 'H4',
        title: 'Application Memory Pressure / GC Thrashing',
        confidence: 12,
        isLeading: false,
        supportingEvidence: ['High HTTP response latency'],
        rejectedReason: 'Memory usage steady at 180MB/512MB; no major GC pauses recorded.',
      },
    ],
    rootCause: {
      title: 'Database Connection Pool Exhaustion',
      confidence: 92,
      supportingCount: 8,
      contradictingCount: 0,
      whySummary: 'DB_POOL_SIZE=5 + connection wait events + timeout correlation + matching runbook',
    },
    verification: {
      baseline: { status: 'FAILED', label: 'FAILED (Expected failure)', code: 1 },
      postfix: { status: 'PASSED', label: 'PASSED (Fix resolved problem)', code: 0 },
      health: { status: 'PASSED', label: 'PASSED (200 OK)', code: 0 },
      control: { status: 'FAILED', label: 'FAILED (Proves causality)', code: 1 },
      receiptId: 'VR-7F9C2B4E',
      timestamp: '2026-10-30T15:50:53Z',
    },
  },
  {
    id: 'retry_storm',
    name: 'Retry Storm',
    service: 'payment-gateway',
    severity: 'HIGH',
    symptoms: 'Upstream payment processor experiencing 45% failure rate due to cascading 504 gateway timeout retries.',
    errorRate: '3.1% → 45%',
    blastRadius: ['Stripe Ingestion', 'Billing Webhooks', 'Checkout API'],
    databaseStatus: 'Normal (12ms latency)',
    expectedRootCause: 'Aggressive Retry Loop (RETRY_COUNT=10 without backoff)',
    verificationState: 'VERIFIED',
    configBefore: 'UPSTREAM_TIMEOUT=5\nRETRY_COUNT=10\nRETRY_BACKOFF=1\nCIRCUIT_BREAKER_THRESHOLD=50%',
    configAfter: 'UPSTREAM_TIMEOUT=5\nRETRY_COUNT=3\nRETRY_BACKOFF=2\nCIRCUIT_BREAKER_THRESHOLD=50%',
    configKey: 'RETRY_COUNT: 10 -> 3',
    risk: 'LOW',
    rollback: 'Available (revert RETRY_COUNT to 10)',
    expectedEffect: 'Dampen retry amplification, allowing upstream gateway to recover queue headroom.',
    traceSteps: [
      { id: '1', title: 'Incident received: 504 Gateway Timeout cascade on payment-gateway', tool: 'telemetry_listener', durationMs: 45, status: 'COMPLETED' },
      { id: '2', title: 'Planner created autonomous investigation plan', tool: 'orchestrator', durationMs: 110, status: 'COMPLETED' },
      { id: '3', title: 'Inspecting logs: 320 retry attempts in 60s for 32 transactions', tool: 'inspect_logs', durationMs: 290, status: 'COMPLETED' },
      { id: '4', title: 'Inspecting configuration: Found RETRY_COUNT=10 without jitter', tool: 'inspect_configuration', durationMs: 160, status: 'COMPLETED' },
      { id: '5', title: 'Retrieving operational knowledge: Cascading failure playbooks matched', tool: 'rag_engine', durationMs: 220, status: 'COMPLETED' },
      { id: '6', title: 'Comparing hypotheses: Formulated 4 competing candidates', tool: 'hypothesis_engine', durationMs: 380, status: 'COMPLETED' },
      { id: '7', title: 'External research: Distributed systems retry amplification', tool: 'tavily', durationMs: 510, status: 'COMPLETED' },
      { id: '8', title: 'Root cause identified: Cascading Retry Storm (88%)', tool: 'nemotron_ai', durationMs: 330, status: 'COMPLETED' },
      { id: '9', title: 'Remediation simulated: RETRY_COUNT capped to 3 with backoff', tool: 'sandbox_engine', durationMs: 270, status: 'COMPLETED' },
      { id: '10', title: 'Baseline test: Simulated upstream lag caused retry deadlock (FAILED)', tool: 'verifier', durationMs: 440, status: 'COMPLETED' },
      { id: '11', title: 'Post-fix test: Bounded retries enabled graceful recovery (PASSED)', tool: 'verifier', durationMs: 470, status: 'COMPLETED' },
      { id: '12', title: 'Health verification: Circuit breaker disengaged, HTTP 200 (PASSED)', tool: 'verifier', durationMs: 250, status: 'COMPLETED' },
      { id: '13', title: 'Control test: Reintroduced RETRY_COUNT=10; storm reappeared (FAILED)', tool: 'verifier', durationMs: 490, status: 'COMPLETED' },
      { id: '14', title: 'VERIFIED: Causal recovery proven by independent control execution', tool: 'verifier', durationMs: 50, status: 'COMPLETED' },
    ],
    ragDocuments: [
      {
        title: 'Upstream Retry Storm Runbook',
        similarity: 95,
        source: 'docs/runbooks/retry-storm.md',
        summary: 'Aggressive retries during minor upstream latency create self-reinforcing queue amplification and 504 timeouts.',
        category: 'Resilience / Networking',
        whyRetrieved: 'Matched incident symptoms: 504 gateway timeout + retry storm + cascading failure',
      },
      {
        title: 'Circuit Breaker Tuning Guide',
        similarity: 86,
        source: 'docs/guides/circuit-breaker.md',
        summary: 'Guidelines for configuring exponential backoff with full jitter to break cascading request loops.',
        category: 'Architecture Guides',
        whyRetrieved: 'Matched configuration key: CIRCUIT_BREAKER_THRESHOLD',
      },
    ],
    causalGraph: {
      nodes: [
        { id: 'n1', label: 'RETRY_COUNT=10', sublabel: 'Configured Multiplier', type: 'root' },
        { id: 'n2', label: 'Retry Amplification', sublabel: '10x Multiplier per Request', type: 'event' },
        { id: 'n3', label: 'Thread Starvation', sublabel: 'Workers Blocked on Sockets', type: 'event' },
        { id: 'n4', label: '504 Gateway Timeout', sublabel: 'Upstream Exhaustion', type: 'symptom' },
        { id: 'n5', label: '45% Failure Spike', sublabel: 'Systemic Checkout Drop', type: 'impact' },
      ],
      edges: [
        { from: 'n1', to: 'n2' },
        { from: 'n2', to: 'n3' },
        { from: 'n3', to: 'n4' },
        { from: 'n4', to: 'n5' },
      ],
    },
    hypotheses: [
      {
        id: 'H1',
        title: 'Upstream Timeout & Cascading Retry Storm',
        confidence: 88,
        isLeading: true,
        supportingEvidence: ['RETRY_COUNT=10 without backoff', 'HTTP 504 Gateway Timeout bursts', '10 retries per failed charge'],
      },
      {
        id: 'H2',
        title: 'Gateway Network Disconnection',
        confidence: 42,
        isLeading: false,
        supportingEvidence: ['Gateway timeouts observed'],
        rejectedReason: 'DNS and TCP handshakes to payment provider complete in 12ms.',
      },
      {
        id: 'H3',
        title: 'Database Lock Contention',
        confidence: 19,
        isLeading: false,
        supportingEvidence: [],
        rejectedReason: 'No database queries active during the upstream HTTP exchange.',
      },
    ],
    rootCause: {
      title: 'Cascading Retry Storm via RETRY_COUNT=10',
      confidence: 88,
      supportingCount: 7,
      contradictingCount: 0,
      whySummary: 'RETRY_COUNT=10 + rapid repeat attempts + upstream queue backup + matching retry storm runbook',
    },
    verification: {
      baseline: { status: 'FAILED', label: 'FAILED (Expected failure)', code: 1 },
      postfix: { status: 'PASSED', label: 'PASSED (Fix resolved problem)', code: 0 },
      health: { status: 'PASSED', label: 'PASSED (200 OK)', code: 0 },
      control: { status: 'FAILED', label: 'FAILED (Proves causality)', code: 1 },
      receiptId: 'VR-8A1D3C5F',
      timestamp: '2026-10-30T15:52:10Z',
    },
  },
  {
    id: 'bad_deployment',
    name: 'Bad Deployment',
    service: 'user-service',
    severity: 'CRITICAL',
    symptoms: 'User service returning HTTP 500 errors across all auth routes immediately following release v3.2.1.',
    errorRate: '0.1% → 99.4%',
    blastRadius: ['User Authentication', 'SSO Login', 'Customer Portal'],
    databaseStatus: 'Healthy (0.8ms query response)',
    expectedRootCause: 'Deprecated Token Auth Scheme in v3.2.1 deployment config',
    verificationState: 'VERIFIED',
    configBefore: 'AUTH_METHOD=legacy_tokens\nJWT_ALGORITHM=HS256\nDEPLOYED_VERSION=v3.2.1',
    configAfter: 'AUTH_METHOD=modern_jwt\nJWT_ALGORITHM=HS256\nDEPLOYED_VERSION=v3.2.1',
    configKey: 'AUTH_METHOD: legacy_tokens -> modern_jwt',
    risk: 'LOW',
    rollback: 'Available (safe rollback to v3.2.0)',
    expectedEffect: 'Restore modern JWT validation scheme, enabling clients to authenticate successfully.',
    traceSteps: [
      { id: '1', title: 'Incident received: 99.4% auth failure post-deploy v3.2.1', tool: 'telemetry_listener', durationMs: 35, status: 'COMPLETED' },
      { id: '2', title: 'Planner created autonomous investigation plan', tool: 'orchestrator', durationMs: 105, status: 'COMPLETED' },
      { id: '3', title: 'Inspecting deployment: v3.2.1 promoted 8 minutes ago', tool: 'inspect_deployment', durationMs: 240, status: 'COMPLETED' },
      { id: '4', title: 'Inspecting configuration: Found AUTH_METHOD=legacy_tokens', tool: 'inspect_configuration', durationMs: 150, status: 'COMPLETED' },
      { id: '5', title: 'Retrieving operational knowledge: Deployment rollback runbooks', tool: 'rag_engine', durationMs: 210, status: 'COMPLETED' },
      { id: '6', title: 'Comparing hypotheses: Formulated 3 competing candidates', tool: 'hypothesis_engine', durationMs: 360, status: 'COMPLETED' },
      { id: '7', title: 'External research: JWT Bearer token migration validation', tool: 'tavily', durationMs: 490, status: 'COMPLETED' },
      { id: '8', title: 'Root cause identified: Auth Config Regression in v3.2.1 (94%)', tool: 'nemotron_ai', durationMs: 320, status: 'COMPLETED' },
      { id: '9', title: 'Remediation simulated: Switched AUTH_METHOD to modern_jwt', tool: 'sandbox_engine', durationMs: 260, status: 'COMPLETED' },
      { id: '10', title: 'Baseline test: Auth tokens rejected under legacy_tokens (FAILED)', tool: 'verifier', durationMs: 410, status: 'COMPLETED' },
      { id: '11', title: 'Post-fix test: Modern bearer tokens verified and accepted (PASSED)', tool: 'verifier', durationMs: 430, status: 'COMPLETED' },
      { id: '12', title: 'Health verification: All auth endpoints return 200 OK (PASSED)', tool: 'verifier', durationMs: 240, status: 'COMPLETED' },
      { id: '13', title: 'Control test: Reverted to legacy_tokens; 500 error returned (FAILED)', tool: 'verifier', durationMs: 480, status: 'COMPLETED' },
      { id: '14', title: 'VERIFIED: Causal recovery proven by independent control execution', tool: 'verifier', durationMs: 45, status: 'COMPLETED' },
    ],
    ragDocuments: [
      {
        title: 'Deployment Rollback Standard Operating Procedure',
        similarity: 96,
        source: 'docs/runbooks/rollback-sop.md',
        summary: 'Emergency procedures for config regressions and schema mismatches introduced during continuous delivery.',
        category: 'Deployment / Release',
        whyRetrieved: 'Matched incident symptoms: auth regression + invalid JWT scheme + deployment mismatch',
      },
    ],
    causalGraph: {
      nodes: [
        { id: 'n1', label: 'Release v3.2.1 Deploy', sublabel: 'Config Regression', type: 'root' },
        { id: 'n2', label: 'AUTH_METHOD=legacy', sublabel: 'Deprecated Scheme', type: 'event' },
        { id: 'n3', label: 'Signature Mismatch', sublabel: 'Token Parse Failure', type: 'event' },
        { id: 'n4', label: 'HTTP 500 on /auth', sublabel: 'Endpoint Exception', type: 'symptom' },
        { id: 'n5', label: 'Total SSO Outage', sublabel: '99.4% Auth Failure', type: 'impact' },
      ],
      edges: [
        { from: 'n1', to: 'n2' },
        { from: 'n2', to: 'n3' },
        { from: 'n3', to: 'n4' },
        { from: 'n4', to: 'n5' },
      ],
    },
    hypotheses: [
      {
        id: 'H1',
        title: 'Authentication Protocol Configuration Regression',
        confidence: 94,
        isLeading: true,
        supportingEvidence: ['AUTH_METHOD set to deprecated legacy_tokens', 'Timing corresponds exactly with v3.2.1 rollout'],
      },
      {
        id: 'H2',
        title: 'Redis Session Store Outage',
        confidence: 32,
        isLeading: false,
        supportingEvidence: [],
        rejectedReason: 'Redis ping response latency is 0.5ms; sessions exist and are healthy.',
      },
    ],
    rootCause: {
      title: 'Authentication Scheme Misconfiguration in Release v3.2.1',
      confidence: 94,
      supportingCount: 9,
      contradictingCount: 0,
      whySummary: 'Deployment timing + legacy_tokens mismatch + token signature failure + rollback SOP',
    },
    verification: {
      baseline: { status: 'FAILED', label: 'FAILED (Expected failure)', code: 1 },
      postfix: { status: 'PASSED', label: 'PASSED (Fix resolved problem)', code: 0 },
      health: { status: 'PASSED', label: 'PASSED (200 OK)', code: 0 },
      control: { status: 'FAILED', label: 'FAILED (Proves causality)', code: 1 },
      receiptId: 'VR-9B2E4D7A',
      timestamp: '2026-10-30T15:53:40Z',
    },
  },
  {
    id: 'cache_stampede',
    name: 'Cache Stampede',
    service: 'catalog-service',
    severity: 'HIGH',
    symptoms: 'Simultaneous expiration of 150,000 product keys causing thundering herd to backend database.',
    errorRate: '0.8% → 28.5%',
    blastRadius: ['Product Catalog', 'Search Index', 'Storefront UI'],
    databaseStatus: 'High Latency (2,200ms query queue)',
    expectedRootCause: 'Missing Cache TTL Jitter causing synchronized expiration',
    verificationState: 'VERIFIED',
    configBefore: 'CACHE_TTL_JITTER=false\nCACHE_DEFAULT_TTL=300\nREDIS_HOST=localhost',
    configAfter: 'CACHE_TTL_JITTER=true\nCACHE_DEFAULT_TTL=300\nREDIS_HOST=localhost',
    configKey: 'CACHE_TTL_JITTER: false -> true',
    risk: 'LOW',
    rollback: 'Available (set CACHE_TTL_JITTER to false)',
    expectedEffect: 'Add randomized spread to key expirations to smooth database read traffic.',
    traceSteps: [
      { id: '1', title: 'Incident received: Catalog latency surge to 2200ms', tool: 'telemetry_listener', durationMs: 40, status: 'COMPLETED' },
      { id: '2', title: 'Planner created autonomous investigation plan', tool: 'orchestrator', durationMs: 110, status: 'COMPLETED' },
      { id: '3', title: 'Inspecting logs: 74% cache miss burst at exact 5-minute interval', tool: 'inspect_logs', durationMs: 270, status: 'COMPLETED' },
      { id: '4', title: 'Inspecting configuration: Found CACHE_TTL_JITTER=false', tool: 'inspect_configuration', durationMs: 160, status: 'COMPLETED' },
      { id: '5', title: 'Retrieving operational knowledge: Thundering herd mitigation guides', tool: 'rag_engine', durationMs: 230, status: 'COMPLETED' },
      { id: '6', title: 'Comparing hypotheses: Formulated 4 competing candidates', tool: 'hypothesis_engine', durationMs: 370, status: 'COMPLETED' },
      { id: '7', title: 'External research: Probabilistic early expiration algorithms', tool: 'tavily', durationMs: 500, status: 'COMPLETED' },
      { id: '8', title: 'Root cause identified: Cache Stampede via Synchronized TTL (91%)', tool: 'nemotron_ai', durationMs: 340, status: 'COMPLETED' },
      { id: '9', title: 'Remediation simulated: Enabled CACHE_TTL_JITTER=true', tool: 'sandbox_engine', durationMs: 280, status: 'COMPLETED' },
      { id: '10', title: 'Baseline test: All keys expired in unison causing 2200ms stall (FAILED)', tool: 'verifier', durationMs: 440, status: 'COMPLETED' },
      { id: '11', title: 'Post-fix test: Randomized TTL dispersed database reads evenly (PASSED)', tool: 'verifier', durationMs: 460, status: 'COMPLETED' },
      { id: '12', title: 'Health verification: Catalog response time reduced to 18ms (PASSED)', tool: 'verifier', durationMs: 250, status: 'COMPLETED' },
      { id: '13', title: 'Control test: Reverted to false; synchronized herd returned (FAILED)', tool: 'verifier', durationMs: 490, status: 'COMPLETED' },
      { id: '14', title: 'VERIFIED: Causal recovery proven by independent control execution', tool: 'verifier', durationMs: 55, status: 'COMPLETED' },
    ],
    ragDocuments: [
      {
        title: 'Redis Thundering Herd Runbook',
        similarity: 93,
        source: 'docs/runbooks/thundering-herd.md',
        summary: 'Synchronized key expiration spikes read queries against the primary database. Mitigate by applying TTL jitter.',
        category: 'Caching / Performance',
        whyRetrieved: 'Matched incident symptoms: cache miss spike + Redis CPU saturation + thundering herd',
      },
    ],
    causalGraph: {
      nodes: [
        { id: 'n1', label: 'CACHE_TTL_JITTER=false', sublabel: 'Synchronous TTL', type: 'root' },
        { id: 'n2', label: '150k Keys Expire', sublabel: 'Simultaneous Expiration', type: 'event' },
        { id: 'n3', label: '74% Cache Miss Burst', sublabel: 'Cache Bypass', type: 'event' },
        { id: 'n4', label: 'Database Overload', sublabel: '2,200ms Latency', type: 'symptom' },
        { id: 'n5', label: 'Catalog Degraded', sublabel: 'Storefront Slowdown', type: 'impact' },
      ],
      edges: [
        { from: 'n1', to: 'n2' },
        { from: 'n2', to: 'n3' },
        { from: 'n3', to: 'n4' },
        { from: 'n4', to: 'n5' },
      ],
    },
    hypotheses: [
      {
        id: 'H1',
        title: 'Cache Stampede via Synchronized TTL Expiration',
        confidence: 91,
        isLeading: true,
        supportingEvidence: ['CACHE_TTL_JITTER disabled', '74% cache miss burst on 5-minute boundaries'],
      },
      {
        id: 'H2',
        title: 'Redis Process Crash',
        confidence: 25,
        isLeading: false,
        supportingEvidence: [],
        rejectedReason: 'Redis uptime is 42 days; process never restarted.',
      },
    ],
    rootCause: {
      title: 'Cache Stampede via Synchronized TTL Expiration',
      confidence: 91,
      supportingCount: 7,
      contradictingCount: 0,
      whySummary: 'CACHE_TTL_JITTER=false + synchronized 300s expiration + database query storm + thundering herd runbook',
    },
    verification: {
      baseline: { status: 'FAILED', label: 'FAILED (Expected failure)', code: 1 },
      postfix: { status: 'PASSED', label: 'PASSED (Fix resolved problem)', code: 0 },
      health: { status: 'PASSED', label: 'PASSED (200 OK)', code: 0 },
      control: { status: 'FAILED', label: 'FAILED (Proves causality)', code: 1 },
      receiptId: 'VR-3C6F1E8B',
      timestamp: '2026-10-30T15:54:20Z',
    },
  },
  {
    id: 'memory_leak',
    name: 'Memory Leak',
    service: 'auth-service',
    severity: 'HIGH',
    symptoms: 'Worker heap exhaustion (95% memory limit) resulting in heavy GC pauses and HTTP 503 drops.',
    errorRate: '0.4% → 19.8%',
    blastRadius: ['Token Verification', 'Session Refresh', 'API Gateway Auth'],
    databaseStatus: 'Normal (1.1ms latency)',
    expectedRootCause: 'Unbounded Session Token Map (MAX_CACHE_ENTRIES=unlimited)',
    verificationState: 'VERIFIED',
    configBefore: 'MAX_CACHE_ENTRIES=unlimited\nTOKEN_CACHE_EXPIRY=0\nHEAP_LIMIT=512m',
    configAfter: 'MAX_CACHE_ENTRIES=10000\nTOKEN_CACHE_EXPIRY=3600\nHEAP_LIMIT=512m',
    configKey: 'MAX_CACHE_ENTRIES: unlimited -> 10000',
    risk: 'LOW',
    rollback: 'Available (revert MAX_CACHE_ENTRIES)',
    expectedEffect: 'Bound cache to 10,000 entries with LRU eviction, stabilizing heap usage at 140MB.',
    traceSteps: [
      { id: '1', title: 'Incident received: Auth worker heap 95% full with 503 drops', tool: 'telemetry_listener', durationMs: 40, status: 'COMPLETED' },
      { id: '2', title: 'Planner created autonomous investigation plan', tool: 'orchestrator', durationMs: 110, status: 'COMPLETED' },
      { id: '3', title: 'Inspecting runtime: 1800ms garbage collection pauses recorded', tool: 'inspect_runtime', durationMs: 310, status: 'COMPLETED' },
      { id: '4', title: 'Inspecting configuration: Found MAX_CACHE_ENTRIES=unlimited', tool: 'inspect_configuration', durationMs: 170, status: 'COMPLETED' },
      { id: '5', title: 'Retrieving operational knowledge: Memory leak runbooks matched', tool: 'rag_engine', durationMs: 230, status: 'COMPLETED' },
      { id: '6', title: 'Comparing hypotheses: Formulated 4 competing candidates', tool: 'hypothesis_engine', durationMs: 380, status: 'COMPLETED' },
      { id: '7', title: 'External research: Node/Python LRU cache bounding patterns', tool: 'tavily', durationMs: 520, status: 'COMPLETED' },
      { id: '8', title: 'Root cause identified: Unbounded Token Map Memory Leak (89%)', tool: 'nemotron_ai', durationMs: 330, status: 'COMPLETED' },
      { id: '9', title: 'Remediation simulated: Enforced MAX_CACHE_ENTRIES=10000 with LRU', tool: 'sandbox_engine', durationMs: 270, status: 'COMPLETED' },
      { id: '10', title: 'Baseline test: Heap grew unbounded until OOM termination (FAILED)', tool: 'verifier', durationMs: 440, status: 'COMPLETED' },
      { id: '11', title: 'Post-fix test: Memory leveled off at 140MB under sustained load (PASSED)', tool: 'verifier', durationMs: 470, status: 'COMPLETED' },
      { id: '12', title: 'Health verification: GC pauses dropped under 12ms (PASSED)', tool: 'verifier', durationMs: 260, status: 'COMPLETED' },
      { id: '13', title: 'Control test: Reverted to unlimited; heap immediately spiked (FAILED)', tool: 'verifier', durationMs: 500, status: 'COMPLETED' },
      { id: '14', title: 'VERIFIED: Causal recovery proven by independent control execution', tool: 'verifier', durationMs: 50, status: 'COMPLETED' },
    ],
    ragDocuments: [
      {
        title: 'Worker Heap Memory Leak Analysis',
        similarity: 92,
        source: 'docs/runbooks/heap-leak.md',
        summary: 'In-memory token maps without explicit eviction thresholds grow monotonically until heap exhaustion triggers OOM kills.',
        category: 'Runtime / Memory',
        whyRetrieved: 'Matched incident symptoms: unbounded heap growth + GC pauses + 503 service unavailable',
      },
    ],
    causalGraph: {
      nodes: [
        { id: 'n1', label: 'MAX_CACHE_ENTRIES=unlimited', sublabel: 'No Eviction Bound', type: 'root' },
        { id: 'n2', label: 'Token Map Growth', sublabel: 'Monotonic Leak', type: 'event' },
        { id: 'n3', label: 'Heap Saturation (95%)', sublabel: 'Memory Limit Hit', type: 'event' },
        { id: 'n4', label: 'GC Thrashing (1800ms)', sublabel: 'Event Loop Freeze', type: 'symptom' },
        { id: 'n5', label: 'HTTP 503 Drops', sublabel: '19.8% Failure Rate', type: 'impact' },
      ],
      edges: [
        { from: 'n1', to: 'n2' },
        { from: 'n2', to: 'n3' },
        { from: 'n3', to: 'n4' },
        { from: 'n4', to: 'n5' },
      ],
    },
    hypotheses: [
      {
        id: 'H1',
        title: 'Unbounded Token Cache Memory Leak',
        confidence: 89,
        isLeading: true,
        supportingEvidence: ['MAX_CACHE_ENTRIES=unlimited in config', 'Heap growth linear with token generation rate'],
      },
      {
        id: 'H2',
        title: 'Socket Descriptor Leak',
        confidence: 28,
        isLeading: false,
        supportingEvidence: [],
        rejectedReason: 'Open socket descriptors constant at 48; no descriptor exhaustion.',
      },
    ],
    rootCause: {
      title: 'Unbounded Token Cache Memory Leak',
      confidence: 89,
      supportingCount: 7,
      contradictingCount: 0,
      whySummary: 'MAX_CACHE_ENTRIES=unlimited + linear heap growth + 1800ms GC pauses + LRU bounding runbook',
    },
    verification: {
      baseline: { status: 'FAILED', label: 'FAILED (Expected failure)', code: 1 },
      postfix: { status: 'PASSED', label: 'PASSED (Fix resolved problem)', code: 0 },
      health: { status: 'PASSED', label: 'PASSED (200 OK)', code: 0 },
      control: { status: 'FAILED', label: 'FAILED (Proves causality)', code: 1 },
      receiptId: 'VR-4D8E2A9C',
      timestamp: '2026-10-30T15:55:00Z',
    },
  },
  {
    id: 'database_saturation',
    name: 'Database Saturation',
    service: 'order-service',
    severity: 'CRITICAL',
    symptoms: 'Write pool connection saturation and transaction lock backlog stalling 1,400 checkout orders.',
    errorRate: '2.4% → 42.1%',
    blastRadius: ['Order Placement', 'Inventory Reservation', 'Warehouse Queue'],
    databaseStatus: 'Connection Exhaustion (Write Master 10/10 active)',
    expectedRootCause: 'Write Master MAX_CONNECTIONS=10 undersized during checkout surge',
    verificationState: 'VERIFIED',
    configBefore: 'MAX_CONNECTIONS=10\nSTATEMENT_TIMEOUT=60s\nDB_HOST=order-db-master',
    configAfter: 'MAX_CONNECTIONS=50\nSTATEMENT_TIMEOUT=15s\nDB_HOST=order-db-master',
    configKey: 'MAX_CONNECTIONS: 10 -> 50',
    risk: 'LOW',
    rollback: 'Available (revert MAX_CONNECTIONS to 10)',
    expectedEffect: 'Expand write connection concurrency to 50, clearing transaction backlog within 12 seconds.',
    traceSteps: [
      { id: '1', title: 'Incident received: 1,400 orders backlogged on order-service', tool: 'telemetry_listener', durationMs: 40, status: 'COMPLETED' },
      { id: '2', title: 'Planner created autonomous investigation plan', tool: 'orchestrator', durationMs: 110, status: 'COMPLETED' },
      { id: '3', title: 'Inspecting logs: Lock wait timeouts exceeded on orders table', tool: 'inspect_logs', durationMs: 300, status: 'COMPLETED' },
      { id: '4', title: 'Inspecting configuration: Found MAX_CONNECTIONS=10 on write pool', tool: 'inspect_configuration', durationMs: 160, status: 'COMPLETED' },
      { id: '5', title: 'Retrieving operational knowledge: Database lock contention runbooks', tool: 'rag_engine', durationMs: 230, status: 'COMPLETED' },
      { id: '6', title: 'Comparing hypotheses: Formulated 4 competing candidates', tool: 'hypothesis_engine', durationMs: 380, status: 'COMPLETED' },
      { id: '7', title: 'External research: PostgreSQL transaction concurrency scaling', tool: 'tavily', durationMs: 510, status: 'COMPLETED' },
      { id: '8', title: 'Root cause identified: Write Master Concurrency Starvation (93%)', tool: 'nemotron_ai', durationMs: 340, status: 'COMPLETED' },
      { id: '9', title: 'Remediation simulated: Scaled MAX_CONNECTIONS to 50 with 15s timeout', tool: 'sandbox_engine', durationMs: 280, status: 'COMPLETED' },
      { id: '10', title: 'Baseline test: 10 connections locked under simulated surge (FAILED)', tool: 'verifier', durationMs: 450, status: 'COMPLETED' },
      { id: '11', title: 'Post-fix test: 50 connections handled 80 concurrent orders cleanly (PASSED)', tool: 'verifier', durationMs: 470, status: 'COMPLETED' },
      { id: '12', title: 'Health verification: Order latency returned to 34ms (PASSED)', tool: 'verifier', durationMs: 250, status: 'COMPLETED' },
      { id: '13', title: 'Control test: Reverted to 10 connections; transaction stall returned (FAILED)', tool: 'verifier', durationMs: 510, status: 'COMPLETED' },
      { id: '14', title: 'VERIFIED: Causal recovery proven by independent control execution', tool: 'verifier', durationMs: 55, status: 'COMPLETED' },
    ],
    ragDocuments: [
      {
        title: 'PostgreSQL Write Contention & Lock Runbook',
        similarity: 95,
        source: 'docs/runbooks/db-write-locks.md',
        summary: 'During checkout traffic spikes, undersized write pools cause transaction cascading locks and checkout drop-off.',
        category: 'Database / High Availability',
        whyRetrieved: 'Matched incident symptoms: write lock saturation + statement timeout + connection backlog',
      },
    ],
    causalGraph: {
      nodes: [
        { id: 'n1', label: 'MAX_CONNECTIONS=10', sublabel: 'Undersized Master', type: 'root' },
        { id: 'n2', label: 'Write Pool Starvation', sublabel: '10/10 Slots Occupied', type: 'event' },
        { id: 'n3', label: 'Row Lock Queuing', sublabel: '1,400 Orders Waiting', type: 'event' },
        { id: 'n4', label: 'Checkout Stalls', sublabel: 'Timeout on Submit', type: 'symptom' },
        { id: 'n5', label: '42.1% Order Failures', sublabel: 'Revenue Impact', type: 'impact' },
      ],
      edges: [
        { from: 'n1', to: 'n2' },
        { from: 'n2', to: 'n3' },
        { from: 'n3', to: 'n4' },
        { from: 'n4', to: 'n5' },
      ],
    },
    hypotheses: [
      {
        id: 'H1',
        title: 'Write Pool Concurrency Starvation & Lock Queue',
        confidence: 93,
        isLeading: true,
        supportingEvidence: ['MAX_CONNECTIONS=10 on write master', 'All 10 slots saturated with 60s statement timeout'],
      },
      {
        id: 'H2',
        title: 'Deadlock in Inventory Table',
        confidence: 64,
        isLeading: false,
        supportingEvidence: [],
        rejectedReason: 'Lock graph shows FIFO queuing rather than cyclical deadlock.',
      },
    ],
    rootCause: {
      title: 'Write Master Concurrency Starvation',
      confidence: 93,
      supportingCount: 8,
      contradictingCount: 0,
      whySummary: 'MAX_CONNECTIONS=10 + order traffic spike + write pool exhaustion + transaction lock runbook',
    },
    verification: {
      baseline: { status: 'FAILED', label: 'FAILED (Expected failure)', code: 1 },
      postfix: { status: 'PASSED', label: 'PASSED (Fix resolved problem)', code: 0 },
      health: { status: 'PASSED', label: 'PASSED (200 OK)', code: 0 },
      control: { status: 'FAILED', label: 'FAILED (Proves causality)', code: 1 },
      receiptId: 'VR-5E9A3B7D',
      timestamp: '2026-10-30T15:56:10Z',
    },
  },
]
