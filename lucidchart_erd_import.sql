-- Lucidchart ERD Import Script for VRID-AlumniUC Knowledge Graph
-- Instren: En Lucidchart go to: File -> Import Data -> Entity Relationship (ERD) -> Select "Generic SQL" or "PostgreSQL" and paste this script.

CREATE TABLE WORK (
  work_id VARCHAR PRIMARY KEY,
  title VARCHAR,
  type_id VARCHAR,
  publisher_id VARCHAR,
  source_id VARCHAR,
  funder_id VARCHAR,
  issued_year VARCHAR,
  doi VARCHAR,
  language_iso VARCHAR,
  rights VARCHAR,
  abstract TEXT
);

CREATE TABLE AUTHOR (
  person_id VARCHAR PRIMARY KEY,
  name VARCHAR,
  codpers VARCHAR,
  is_uc BOOLEAN,
  orcid VARCHAR
);

CREATE TABLE INSTITUTION (
  dept_id VARCHAR PRIMARY KEY,
  name VARCHAR,
  cod_ua VARCHAR
);

CREATE TABLE DEWEY (
  dewey_code VARCHAR PRIMARY KEY,
  name_es VARCHAR
);

CREATE TABLE ODS (
  ods_code VARCHAR PRIMARY KEY,
  name_en VARCHAR,
  name_es VARCHAR
);

CREATE TABLE KEYWORD (
  keyword_id VARCHAR PRIMARY KEY,
  name VARCHAR
);

CREATE TABLE DOCTYPE (
  type_id VARCHAR PRIMARY KEY,
  name VARCHAR
);

CREATE TABLE PUBLISHER (
  publisher_id VARCHAR PRIMARY KEY,
  name VARCHAR
);

CREATE TABLE FUNDER (
  funder_id VARCHAR PRIMARY KEY,
  name VARCHAR
);

CREATE TABLE SOURCE (
  source_id VARCHAR PRIMARY KEY,
  name VARCHAR,
  issn VARCHAR,
  index VARCHAR
);

-- Relationship Tables / Foreign Keys
CREATE TABLE WORK_AUTHOR (
  work_id VARCHAR,
  person_id VARCHAR,
  role VARCHAR,
  PRIMARY KEY (work_id, person_id),
  FOREIGN KEY (work_id) REFERENCES WORK(work_id),
  FOREIGN KEY (person_id) REFERENCES AUTHOR(person_id)
);

CREATE TABLE AUTHOR_AFFILIATION (
  person_id VARCHAR,
  dept_id VARCHAR,
  PRIMARY KEY (person_id, dept_id),
  FOREIGN KEY (person_id) REFERENCES AUTHOR(person_id),
  FOREIGN KEY (dept_id) REFERENCES INSTITUTION(dept_id)
);

CREATE TABLE WORK_DEWEY (
  work_id VARCHAR,
  dewey_code VARCHAR,
  PRIMARY KEY (work_id, dewey_code),
  FOREIGN KEY (work_id) REFERENCES WORK(work_id),
  FOREIGN KEY (dewey_code) REFERENCES DEWEY(dewey_code)
);

CREATE TABLE WORK_ODS (
  work_id VARCHAR,
  ods_code VARCHAR,
  PRIMARY KEY (work_id, ods_code),
  FOREIGN KEY (work_id) REFERENCES WORK(work_id),
  FOREIGN KEY (ods_code) REFERENCES ODS(ods_code)
);

CREATE TABLE WORK_KEYWORD (
  work_id VARCHAR,
  keyword_id VARCHAR,
  PRIMARY KEY (work_id, keyword_id),
  FOREIGN KEY (work_id) REFERENCES WORK(work_id),
  FOREIGN KEY (keyword_id) REFERENCES KEYWORD(keyword_id)
);

-- Foreign Keys for Work
ALTER TABLE WORK ADD FOREIGN KEY (type_id) REFERENCES DOCTYPE(type_id);
ALTER TABLE WORK ADD FOREIGN KEY (publisher_id) REFERENCES PUBLISHER(publisher_id);
ALTER TABLE WORK ADD FOREIGN KEY (funder_id) REFERENCES FUNDER(funder_id);
ALTER TABLE WORK ADD FOREIGN KEY (source_id) REFERENCES SOURCE(source_id);
