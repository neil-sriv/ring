CREATE TABLE public.alembic_version (
	version_num VARCHAR(32) NOT NULL,
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num ASC)
);
CREATE SEQUENCE public.user_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public."user" (
	id INT8 NOT NULL DEFAULT nextval('public.user_id_seq'::REGCLASS),
	name VARCHAR NULL,
	email VARCHAR NOT NULL,
	hashed_password VARCHAR NOT NULL,
	api_identifier VARCHAR NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	admin BOOL NOT NULL DEFAULT false,
	CONSTRAINT user_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX ix_user_api_identifier (api_identifier ASC),
	INDEX ix_user_created_at (created_at ASC),
	UNIQUE INDEX ix_user_email (email ASC),
	INDEX ix_user_id (id ASC)
);
CREATE SEQUENCE public.group_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public."group" (
	id INT8 NOT NULL DEFAULT nextval('public.group_id_seq'::REGCLASS),
	name VARCHAR NOT NULL,
	api_identifier VARCHAR NOT NULL,
	admin_id INT8 NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	cycle_length INT8 NOT NULL DEFAULT 30:::INT8,
	CONSTRAINT group_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX ix_group_api_identifier (api_identifier ASC),
	INDEX ix_group_created_at (created_at ASC),
	INDEX ix_group_id (id ASC),
	UNIQUE INDEX ix_group_name (name ASC)
);
CREATE SEQUENCE public.default_question_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.default_question (
	id INT8 NOT NULL DEFAULT nextval('public.default_question_id_seq'::REGCLASS),
	api_identifier VARCHAR NOT NULL,
	question_text STRING NOT NULL,
	group_id INT8 NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	CONSTRAINT default_question_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX ix_default_question_api_identifier (api_identifier ASC),
	INDEX ix_default_question_created_at (created_at ASC),
	INDEX ix_default_question_id (id ASC)
);
CREATE SEQUENCE public.group_key_value_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.group_key_value (
	id INT8 NOT NULL DEFAULT nextval('public.group_key_value_id_seq'::REGCLASS),
	group_id INT8 NOT NULL,
	key_values JSONB NOT NULL DEFAULT '{}':::JSONB,
	CONSTRAINT group_key_value_pkey PRIMARY KEY (id ASC),
	INDEX ix_group_key_value_group_id (group_id ASC)
);
CREATE SEQUENCE public.s3_file_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.s3_file (
	id INT8 NOT NULL DEFAULT nextval('public.s3_file_id_seq'::REGCLASS),
	type VARCHAR NOT NULL,
	s3_url VARCHAR NOT NULL,
	CONSTRAINT s3_file_pkey PRIMARY KEY (id ASC),
	INDEX ix_s3_file_id (id ASC)
);
CREATE TABLE public.image (
	id INT8 NOT NULL,
	media_type VARCHAR NOT NULL DEFAULT 'image':::STRING::VARCHAR,
	CONSTRAINT image_pkey PRIMARY KEY (id ASC),
	INDEX ix_image_id (id ASC)
);
CREATE SEQUENCE public.letter_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.letter (
	id INT8 NOT NULL DEFAULT nextval('public.letter_id_seq'::REGCLASS),
	number INT8 NULL,
	api_identifier VARCHAR NOT NULL,
	group_id INT8 NULL,
	status VARCHAR NOT NULL,
	send_at TIMESTAMPTZ NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	letter_type VARCHAR NOT NULL DEFAULT 'CYCLIC':::STRING,
	title VARCHAR NULL,
	CONSTRAINT letter_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX unique_group_letter_number (group_id ASC, number ASC),
	UNIQUE INDEX ix_letter_api_identifier (api_identifier ASC),
	INDEX ix_letter_created_at (created_at ASC),
	INDEX ix_letter_id (id ASC)
);
CREATE SEQUENCE public.question_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.question (
	id INT8 NOT NULL DEFAULT nextval('public.question_id_seq'::REGCLASS),
	api_identifier VARCHAR NOT NULL,
	question_text STRING NOT NULL,
	letter_id INT8 NOT NULL,
	author_id INT8 NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	CONSTRAINT question_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX ix_question_api_identifier (api_identifier ASC),
	INDEX ix_question_created_at (created_at ASC),
	INDEX ix_question_id (id ASC)
);
CREATE SEQUENCE public.response_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.response (
	id INT8 NOT NULL DEFAULT nextval('public.response_id_seq'::REGCLASS),
	api_identifier VARCHAR NOT NULL,
	participant_id INT8 NOT NULL,
	question_id INT8 NOT NULL,
	response_text STRING NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	CONSTRAINT response_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX participant_question_unique (participant_id ASC, question_id ASC),
	UNIQUE INDEX ix_response_api_identifier (api_identifier ASC),
	INDEX ix_response_created_at (created_at ASC),
	INDEX ix_response_id (id ASC)
);
CREATE TABLE public.image_response_assocation (
	image_id INT8 NOT NULL,
	response_id INT8 NOT NULL,
	CONSTRAINT image_response_assocation_pkey PRIMARY KEY (image_id ASC, response_id ASC)
);
CREATE SEQUENCE public.one_time_token_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.one_time_token (
	id INT8 NOT NULL DEFAULT nextval('public.one_time_token_id_seq'::REGCLASS),
	token VARCHAR NOT NULL,
	ttl FLOAT8 NOT NULL,
	used BOOL NOT NULL DEFAULT false,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	type VARCHAR NOT NULL,
	email VARCHAR NULL,
	CONSTRAINT one_time_token_pkey PRIMARY KEY (id ASC),
	INDEX ix_one_time_token_created_at (created_at ASC),
	INDEX ix_one_time_token_email (email ASC),
	INDEX ix_one_time_token_id (id ASC)
);
CREATE SEQUENCE public.invite_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.invite (
	id INT8 NOT NULL DEFAULT nextval('public.invite_id_seq'::REGCLASS),
	email VARCHAR NOT NULL,
	api_identifier VARCHAR NOT NULL,
	inviter_id INT8 NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	group_id INT8 NOT NULL,
	one_time_token_id INT8 NOT NULL,
	CONSTRAINT invite_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX ix_invite_api_identifier (api_identifier ASC),
	INDEX ix_invite_created_at (created_at ASC),
	INDEX ix_invite_email (email ASC),
	INDEX ix_invite_id (id ASC),
	UNIQUE INDEX ix_invite_one_time_token_id (one_time_token_id ASC)
);
CREATE TABLE public.letter_to_user_assocation (
	letter_id INT8 NULL,
	user_id INT8 NULL,
	rowid INT8 NOT VISIBLE NOT NULL DEFAULT unique_rowid(),
	CONSTRAINT letter_to_user_assocation_pkey PRIMARY KEY (rowid ASC)
);
CREATE SEQUENCE public.schedule_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.schedule (
	id INT8 NOT NULL DEFAULT nextval('public.schedule_id_seq'::REGCLASS),
	group_id INT8 NOT NULL,
	CONSTRAINT schedule_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX unique_group_schedule (group_id ASC),
	INDEX ix_schedule_id (id ASC)
);
CREATE SEQUENCE public.subscription_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.subscription (
	id INT8 NOT NULL DEFAULT nextval('public.subscription_id_seq'::REGCLASS),
	endpoint VARCHAR NOT NULL,
	keys JSONB NOT NULL,
	user_id INT8 NOT NULL,
	api_identifier VARCHAR NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	CONSTRAINT subscription_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX ix_subscription_api_identifier (api_identifier ASC),
	INDEX ix_subscription_created_at (created_at ASC),
	UNIQUE INDEX ix_subscription_endpoint (endpoint ASC),
	INDEX ix_subscription_id (id ASC),
	INDEX ix_subscription_user_id (user_id ASC)
);
CREATE SEQUENCE public.task_id_seq AS INT8 MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.task (
	id INT8 NOT NULL DEFAULT nextval('public.task_id_seq'::REGCLASS),
	schedule_id INT8 NOT NULL,
	type VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	execute_at TIMESTAMPTZ NOT NULL,
	arguments JSONB NOT NULL,
	message VARCHAR NULL,
	CONSTRAINT task_pkey PRIMARY KEY (id ASC),
	INDEX ix_task_execute_at (execute_at ASC),
	INDEX ix_task_id (id ASC),
	INDEX ix_task_schedule_id (schedule_id ASC),
	INDEX ix_task_status (status ASC),
	INDEX ix_task_type (type ASC)
);
CREATE TABLE public.user_group_assocation (
	user_id INT8 NULL,
	group_id INT8 NULL,
	rowid INT8 NOT VISIBLE NOT NULL DEFAULT unique_rowid(),
	CONSTRAINT user_group_assocation_pkey PRIMARY KEY (rowid ASC)
);
CREATE TABLE public.apscheduler_jobs (
	id VARCHAR(191) NOT NULL,
	next_run_time FLOAT8 NULL,
	job_state BYTES NOT NULL,
	CONSTRAINT apscheduler_jobs_pkey PRIMARY KEY (id ASC),
	INDEX ix_public_apscheduler_jobs_next_run_time (next_run_time ASC)
);
CREATE TABLE public.hybrid_search_document (
	id INT8 NOT NULL DEFAULT unique_rowid(),
	raw_text VARCHAR NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	text_tsv TSVECTOR NULL AS (to_tsvector('english':::STRING, raw_text)) STORED,
	text_embedding_768 VECTOR(768) NULL,
	CONSTRAINT hybrid_search_document_pkey PRIMARY KEY (id ASC),
	INDEX ix_hybrid_search_document_created_at (created_at ASC),
	INVERTED INDEX content_search_inverted_idx (text_tsv),
	VECTOR INDEX embedding_vector_idx (text_embedding_768 vector_l2_ops)
);
CREATE TABLE public.hybrid_search_document_association (
	id INT8 NOT NULL DEFAULT unique_rowid(),
	hybrid_search_document_id INT8 NOT NULL,
	model_api_identifier VARCHAR NOT NULL,
	model_type VARCHAR NOT NULL,
	CONSTRAINT hybrid_search_document_association_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX uq_model_api_identifier_model_type (model_api_identifier ASC, model_type ASC)
);
CREATE TABLE public.documents (
	id INT8 NOT NULL DEFAULT unique_rowid(),
	name VARCHAR NOT NULL,
	content BYTES NOT NULL,
	latest_snapshot_version INT8 NOT NULL,
	api_identifier VARCHAR NOT NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	group_id INT8 NOT NULL,
	CONSTRAINT documents_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX ix_documents_api_identifier (api_identifier ASC),
	INDEX ix_documents_created_at (created_at ASC)
);
CREATE SEQUENCE public.document_edit_version_seq MINVALUE 1 MAXVALUE 9223372036854775807 INCREMENT 1 START 1;
CREATE TABLE public.document_edits (
	id INT8 NOT NULL DEFAULT unique_rowid(),
	delta BYTES NOT NULL,
	version INT8 NOT NULL DEFAULT nextval('public.document_edit_version_seq'::REGCLASS),
	document_id INT8 NOT NULL,
	author_id INT8 NULL,
	created_at TIMESTAMPTZ NOT NULL DEFAULT now():::TIMESTAMPTZ,
	CONSTRAINT document_edits_pkey PRIMARY KEY (id ASC),
	UNIQUE INDEX unique_document_edit_version (document_id ASC, version ASC),
	INDEX ix_document_edits_created_at (created_at ASC)
);
ALTER TABLE public."group" ADD CONSTRAINT group_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES public."user"(id);
ALTER TABLE public.default_question ADD CONSTRAINT default_question_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
ALTER TABLE public.group_key_value ADD CONSTRAINT group_key_value_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
ALTER TABLE public.image ADD CONSTRAINT image_id_fkey FOREIGN KEY (id) REFERENCES public.s3_file(id);
ALTER TABLE public.letter ADD CONSTRAINT letter_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
ALTER TABLE public.question ADD CONSTRAINT question_author_id_fkey FOREIGN KEY (author_id) REFERENCES public."user"(id);
ALTER TABLE public.question ADD CONSTRAINT question_letter_id_fkey FOREIGN KEY (letter_id) REFERENCES public.letter(id);
ALTER TABLE public.response ADD CONSTRAINT response_participant_id_fkey FOREIGN KEY (participant_id) REFERENCES public."user"(id);
ALTER TABLE public.response ADD CONSTRAINT response_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.question(id);
ALTER TABLE public.image_response_assocation ADD CONSTRAINT image_response_assocation_image_id_fkey FOREIGN KEY (image_id) REFERENCES public.image(id);
ALTER TABLE public.image_response_assocation ADD CONSTRAINT image_response_assocation_response_id_fkey FOREIGN KEY (response_id) REFERENCES public.response(id);
ALTER TABLE public.invite ADD CONSTRAINT invite_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id) ON DELETE CASCADE;
ALTER TABLE public.invite ADD CONSTRAINT invite_inviter_id_fkey FOREIGN KEY (inviter_id) REFERENCES public."user"(id) ON DELETE CASCADE;
ALTER TABLE public.invite ADD CONSTRAINT invite_one_time_token_id_fkey FOREIGN KEY (one_time_token_id) REFERENCES public.one_time_token(id) ON DELETE CASCADE;
ALTER TABLE public.letter_to_user_assocation ADD CONSTRAINT letter_to_user_assocation_letter_id_fkey FOREIGN KEY (letter_id) REFERENCES public.letter(id);
ALTER TABLE public.letter_to_user_assocation ADD CONSTRAINT letter_to_user_assocation_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);
ALTER TABLE public.schedule ADD CONSTRAINT schedule_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
ALTER TABLE public.subscription ADD CONSTRAINT subscription_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;
ALTER TABLE public.task ADD CONSTRAINT task_schedule_id_fkey FOREIGN KEY (schedule_id) REFERENCES public.schedule(id);
ALTER TABLE public.user_group_assocation ADD CONSTRAINT user_group_assocation_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
ALTER TABLE public.user_group_assocation ADD CONSTRAINT user_group_assocation_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);
ALTER TABLE public.hybrid_search_document_association ADD CONSTRAINT association_hybrid_search_document_id_fkey FOREIGN KEY (hybrid_search_document_id) REFERENCES public.hybrid_search_document(id) ON DELETE CASCADE;
ALTER TABLE public.documents ADD CONSTRAINT documents_group_id_fkey FOREIGN KEY (group_id) REFERENCES public."group"(id);
ALTER TABLE public.document_edits ADD CONSTRAINT document_edits_author_id_fkey FOREIGN KEY (author_id) REFERENCES public."user"(id);
ALTER TABLE public.document_edits ADD CONSTRAINT document_edits_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id);
-- Validate foreign key constraints. These can fail if there was unvalidated data during the SHOW CREATE ALL TABLES
ALTER TABLE public."group" VALIDATE CONSTRAINT group_admin_id_fkey;
ALTER TABLE public.default_question VALIDATE CONSTRAINT default_question_group_id_fkey;
ALTER TABLE public.group_key_value VALIDATE CONSTRAINT group_key_value_group_id_fkey;
ALTER TABLE public.image VALIDATE CONSTRAINT image_id_fkey;
ALTER TABLE public.letter VALIDATE CONSTRAINT letter_group_id_fkey;
ALTER TABLE public.question VALIDATE CONSTRAINT question_author_id_fkey;
ALTER TABLE public.question VALIDATE CONSTRAINT question_letter_id_fkey;
ALTER TABLE public.response VALIDATE CONSTRAINT response_participant_id_fkey;
ALTER TABLE public.response VALIDATE CONSTRAINT response_question_id_fkey;
ALTER TABLE public.image_response_assocation VALIDATE CONSTRAINT image_response_assocation_image_id_fkey;
ALTER TABLE public.image_response_assocation VALIDATE CONSTRAINT image_response_assocation_response_id_fkey;
ALTER TABLE public.invite VALIDATE CONSTRAINT invite_group_id_fkey;
ALTER TABLE public.invite VALIDATE CONSTRAINT invite_inviter_id_fkey;
ALTER TABLE public.invite VALIDATE CONSTRAINT invite_one_time_token_id_fkey;
ALTER TABLE public.letter_to_user_assocation VALIDATE CONSTRAINT letter_to_user_assocation_letter_id_fkey;
ALTER TABLE public.letter_to_user_assocation VALIDATE CONSTRAINT letter_to_user_assocation_user_id_fkey;
ALTER TABLE public.schedule VALIDATE CONSTRAINT schedule_group_id_fkey;
ALTER TABLE public.subscription VALIDATE CONSTRAINT subscription_user_id_fkey;
ALTER TABLE public.task VALIDATE CONSTRAINT task_schedule_id_fkey;
ALTER TABLE public.user_group_assocation VALIDATE CONSTRAINT user_group_assocation_group_id_fkey;
ALTER TABLE public.user_group_assocation VALIDATE CONSTRAINT user_group_assocation_user_id_fkey;
ALTER TABLE public.hybrid_search_document_association VALIDATE CONSTRAINT association_hybrid_search_document_id_fkey;
ALTER TABLE public.documents VALIDATE CONSTRAINT documents_group_id_fkey;
ALTER TABLE public.document_edits VALIDATE CONSTRAINT document_edits_author_id_fkey;
ALTER TABLE public.document_edits VALIDATE CONSTRAINT document_edits_document_id_fkey;
