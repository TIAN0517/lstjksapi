--
-- PostgreSQL database dump
--

-- Dumped from database version 15.14 (Debian 15.14-1.pgdg12+1)
-- Dumped by pg_dump version 17.5 (Debian 17.5-1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: jytian
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO jytian;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: data_quality_reports; Type: TABLE; Schema: public; Owner: jytian
--

CREATE TABLE public.data_quality_reports (
    id bigint NOT NULL,
    upload_id text NOT NULL,
    dataset_name text,
    success boolean,
    total_expectations integer,
    successful_expectations integer,
    failed_expectations integer,
    success_rate numeric(5,2),
    report_path text,
    report_data jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.data_quality_reports OWNER TO jytian;

--
-- Name: data_quality_reports_id_seq; Type: SEQUENCE; Schema: public; Owner: jytian
--

CREATE SEQUENCE public.data_quality_reports_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.data_quality_reports_id_seq OWNER TO jytian;

--
-- Name: data_quality_reports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: jytian
--

ALTER SEQUENCE public.data_quality_reports_id_seq OWNED BY public.data_quality_reports.id;


--
-- Name: dedup_clusters; Type: TABLE; Schema: public; Owner: jytian
--

CREATE TABLE public.dedup_clusters (
    cluster_id text NOT NULL,
    record_count integer DEFAULT 1,
    primary_record_id bigint,
    match_threshold numeric(3,2),
    avg_match_score numeric(3,2),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dedup_clusters OWNER TO jytian;

--
-- Name: enhanced_records; Type: TABLE; Schema: public; Owner: jytian
--

CREATE TABLE public.enhanced_records (
    id bigint NOT NULL,
    original_name text,
    original_phone text,
    original_email text,
    original_address text,
    phone_e164 text,
    phone_region text,
    phone_carrier text,
    phone_line_type text,
    phone_reachable boolean,
    phone_validation_score numeric(3,2),
    name_zh_prob numeric(3,2),
    name_signals jsonb,
    name_surname text,
    name_normalized text,
    addr_libpostal jsonb,
    addr_cn jsonb,
    addr_normalized text,
    addr_quality_score numeric(3,2),
    lang_code text,
    lang_score numeric(3,2),
    lang_top_k jsonb,
    entity_cluster_id text,
    entity_match_score numeric(3,2),
    entity_duplicate_of integer,
    upload_id text,
    processed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.enhanced_records OWNER TO jytian;

--
-- Name: enhanced_records_id_seq; Type: SEQUENCE; Schema: public; Owner: jytian
--

CREATE SEQUENCE public.enhanced_records_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.enhanced_records_id_seq OWNER TO jytian;

--
-- Name: enhanced_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: jytian
--

ALTER SEQUENCE public.enhanced_records_id_seq OWNED BY public.enhanced_records.id;


--
-- Name: data_quality_reports id; Type: DEFAULT; Schema: public; Owner: jytian
--

ALTER TABLE ONLY public.data_quality_reports ALTER COLUMN id SET DEFAULT nextval('public.data_quality_reports_id_seq'::regclass);


--
-- Name: enhanced_records id; Type: DEFAULT; Schema: public; Owner: jytian
--

ALTER TABLE ONLY public.enhanced_records ALTER COLUMN id SET DEFAULT nextval('public.enhanced_records_id_seq'::regclass);


--
-- Name: data_quality_reports data_quality_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: jytian
--

ALTER TABLE ONLY public.data_quality_reports
    ADD CONSTRAINT data_quality_reports_pkey PRIMARY KEY (id);


--
-- Name: dedup_clusters dedup_clusters_pkey; Type: CONSTRAINT; Schema: public; Owner: jytian
--

ALTER TABLE ONLY public.dedup_clusters
    ADD CONSTRAINT dedup_clusters_pkey PRIMARY KEY (cluster_id);


--
-- Name: enhanced_records enhanced_records_pkey; Type: CONSTRAINT; Schema: public; Owner: jytian
--

ALTER TABLE ONLY public.enhanced_records
    ADD CONSTRAINT enhanced_records_pkey PRIMARY KEY (id);


--
-- Name: idx_enhanced_records_cluster_id; Type: INDEX; Schema: public; Owner: jytian
--

CREATE INDEX idx_enhanced_records_cluster_id ON public.enhanced_records USING btree (entity_cluster_id);


--
-- Name: idx_enhanced_records_phone_e164; Type: INDEX; Schema: public; Owner: jytian
--

CREATE INDEX idx_enhanced_records_phone_e164 ON public.enhanced_records USING btree (phone_e164);


--
-- Name: idx_enhanced_records_upload_id; Type: INDEX; Schema: public; Owner: jytian
--

CREATE INDEX idx_enhanced_records_upload_id ON public.enhanced_records USING btree (upload_id);


--
-- Name: idx_enhanced_records_zh_prob; Type: INDEX; Schema: public; Owner: jytian
--

CREATE INDEX idx_enhanced_records_zh_prob ON public.enhanced_records USING btree (name_zh_prob);


--
-- Name: idx_quality_reports_upload_id; Type: INDEX; Schema: public; Owner: jytian
--

CREATE INDEX idx_quality_reports_upload_id ON public.data_quality_reports USING btree (upload_id);


--
-- Name: enhanced_records update_enhanced_records_updated_at; Type: TRIGGER; Schema: public; Owner: jytian
--

CREATE TRIGGER update_enhanced_records_updated_at BEFORE UPDATE ON public.enhanced_records FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO jytian;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT,INSERT,REFERENCES,DELETE,TRIGGER,TRUNCATE,UPDATE ON TABLES TO jytian;


--
-- PostgreSQL database dump complete
--

