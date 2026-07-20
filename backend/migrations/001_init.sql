CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_id TEXT UNIQUE,
    email TEXT,
    plan TEXT DEFAULT 'free',
    api_key TEXT UNIQUE,
    reviews_this_month INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE connected_repos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    installation_id BIGINT,
    owner TEXT NOT NULL,
    repo TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(owner, repo)
);

CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    share_id TEXT UNIQUE,
    user_id UUID REFERENCES users(id),
    source TEXT CHECK (source IN ('web','api','github_app','ci')),
    repo_full_name TEXT,
    pr_number INTEGER,
    diff_text TEXT,
    diff_line_count INTEGER,
    overall_severity TEXT,
    finding_counts JSONB DEFAULT '{}',
    model_used TEXT,
    latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    review_id UUID REFERENCES reviews(id) ON DELETE CASCADE,
    category TEXT,
    severity TEXT,
    file_path TEXT,
    line_start INTEGER,
    line_end INTEGER,
    title TEXT NOT NULL,
    explanation TEXT,
    suggested_fix TEXT,
    why_it_matters TEXT,
    cwe_id TEXT,
    embedding vector(1536),
    user_feedback TEXT CHECK (user_feedback IN ('helpful','unhelpful'))
);

CREATE INDEX ON findings(review_id);
CREATE INDEX ON findings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX ON reviews(share_id) WHERE share_id IS NOT NULL;
CREATE INDEX ON reviews(created_at) WHERE expires_at IS NOT NULL;
CREATE INDEX ON reviews(user_id) WHERE user_id IS NOT NULL;
