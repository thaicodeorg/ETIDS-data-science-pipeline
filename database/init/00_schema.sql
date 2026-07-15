CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS clean;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS lab;

CREATE TABLE IF NOT EXISTS lab.pipeline_run_log (
    run_id BIGSERIAL PRIMARY KEY,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL,
    detail JSONB,
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS lab.lecture_map (
    lecture_no INT PRIMARY KEY,
    lecture_title TEXT NOT NULL,
    pipeline_focus TEXT NOT NULL,
    main_outputs TEXT NOT NULL
);

INSERT INTO lab.lecture_map (lecture_no, lecture_title, pipeline_focus, main_outputs)
VALUES
(3, 'Data Wrangling & Feature Engineering', 'Raw data, quality check, cleaning, preprocessing, EDA, feature engineering, and audit-style data-quality evidence', 'raw schema, clean schema, dq issue log, feature tables'),
(4, 'Data Visualization & Decision Dashboard', 'Cleaned data to visualization, insight, decision, action, metric layer, chart layer, dashboard layer, and RLS', 'mart schema, Superset dataset views, metric registry, chart registry, dashboard registry, RLS registry')
ON CONFLICT (lecture_no) DO UPDATE
SET lecture_title = EXCLUDED.lecture_title,
    pipeline_focus = EXCLUDED.pipeline_focus,
    main_outputs = EXCLUDED.main_outputs;
