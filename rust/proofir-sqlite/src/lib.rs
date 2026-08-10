//! Versioned SQL contract for the normalized ProofIR projection.
//!
//! Execution is intentionally kept behind Ladon's existing SQLite builder until
//! Rust has differential row/plan vectors; this crate prevents the schema from
//! being re-invented by downstream adapters.

pub const SCHEMA_VERSION: &str = "proofir-sqlite-v3-1";
pub const SCHEMA_SQL: &str = r#"
CREATE TABLE proofir_v3_artifacts(
  artifact_id TEXT PRIMARY KEY,
  artifact_kind TEXT NOT NULL,
  proofir_version TEXT NOT NULL,
  environment_ref TEXT NOT NULL,
  content_json TEXT NOT NULL,
  UNIQUE(artifact_id, artifact_kind)
);
CREATE TABLE proofir_v3_environments(
  environment_ref TEXT PRIMARY KEY,
  environment_json TEXT NOT NULL
);
CREATE TABLE proofir_v3_subjects(
  environment_ref TEXT NOT NULL,
  subject_kind TEXT NOT NULL,
  local_id TEXT NOT NULL,
  fingerprint TEXT,
  display TEXT,
  PRIMARY KEY(environment_ref, subject_kind, local_id),
  FOREIGN KEY(environment_ref) REFERENCES proofir_v3_environments(environment_ref) ON DELETE CASCADE
);
CREATE TABLE proofir_v3_observations(
  observation_id TEXT PRIMARY KEY,
  artifact_id TEXT NOT NULL REFERENCES proofir_v3_artifacts(artifact_id) ON DELETE CASCADE,
  environment_ref TEXT NOT NULL,
  subject_kind TEXT NOT NULL,
  subject_local_id TEXT NOT NULL,
  observation_kind TEXT NOT NULL,
  result TEXT NOT NULL,
  authority_basis TEXT NOT NULL,
  guarantee_scope TEXT NOT NULL,
  details_json TEXT NOT NULL,
  FOREIGN KEY(environment_ref, subject_kind, subject_local_id)
    REFERENCES proofir_v3_subjects(environment_ref, subject_kind, local_id) ON DELETE CASCADE
);
CREATE TABLE proofir_v3_coverage(
  artifact_id TEXT PRIMARY KEY REFERENCES proofir_v3_artifacts(artifact_id) ON DELETE CASCADE,
  population_kind TEXT NOT NULL,
  selector_json TEXT NOT NULL,
  expected INTEGER,
  query_matched INTEGER NOT NULL CHECK(query_matched >= 0),
  omitted_json TEXT NOT NULL
);
CREATE TABLE proofir_v3_omissions(
  artifact_id TEXT NOT NULL REFERENCES proofir_v3_artifacts(artifact_id) ON DELETE CASCADE,
  pointer TEXT NOT NULL,
  stage TEXT NOT NULL,
  reason_code TEXT NOT NULL,
  details_json TEXT NOT NULL,
  PRIMARY KEY(artifact_id, pointer, reason_code)
);
CREATE TABLE proofir_v3_extensions(
  artifact_id TEXT NOT NULL REFERENCES proofir_v3_artifacts(artifact_id) ON DELETE CASCADE,
  namespace TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  PRIMARY KEY(artifact_id, namespace)
);
CREATE INDEX idx_v3_artifacts_kind ON proofir_v3_artifacts(artifact_kind, proofir_version, artifact_id);
CREATE INDEX idx_v3_subject_fingerprint ON proofir_v3_subjects(environment_ref, subject_kind, fingerprint, local_id);
CREATE INDEX idx_v3_subject_local_id ON proofir_v3_subjects(local_id, environment_ref, subject_kind);
CREATE INDEX idx_v3_subject_display ON proofir_v3_subjects(display, environment_ref, subject_kind) WHERE display IS NOT NULL;
CREATE INDEX idx_v3_observation_subject ON proofir_v3_observations(environment_ref, subject_kind, subject_local_id, result);
CREATE INDEX idx_v3_observation_artifact ON proofir_v3_observations(artifact_id, observation_kind, result);
CREATE INDEX idx_v3_omission_stage ON proofir_v3_omissions(stage, reason_code, artifact_id);
CREATE INDEX idx_v3_extension_namespace ON proofir_v3_extensions(namespace, artifact_id);
"#;

pub fn schema_contract() -> (&'static str, &'static str) {
    (SCHEMA_VERSION, SCHEMA_SQL)
}

/// Minimal owned SQLite adapter used for parity tests. Production publication
/// remains Ladon's transactional Python projection until all row/query vectors
/// are differential.
pub struct Connection(*mut libsqlite3_sys::sqlite3);

impl Connection {
    pub fn open_memory() -> Result<Self, String> {
        let mut handle = std::ptr::null_mut();
        let name = std::ffi::CString::new(":memory:").unwrap();
        let status = unsafe { libsqlite3_sys::sqlite3_open(name.as_ptr(), &mut handle) };
        if status != libsqlite3_sys::SQLITE_OK {
            return Err(format!("sqlite open failed: {status}"));
        }
        let connection = Self(handle);
        connection.execute("PRAGMA foreign_keys = ON")?;
        connection.execute(SCHEMA_SQL)?;
        Ok(connection)
    }

    pub fn execute(&self, sql: &str) -> Result<(), String> {
        let mut error = std::ptr::null_mut();
        let bytes = std::ffi::CString::new(sql).map_err(|_| "SQL contains NUL".to_string())?;
        let status = unsafe {
            libsqlite3_sys::sqlite3_exec(
                self.0,
                bytes.as_ptr(),
                None,
                std::ptr::null_mut(),
                &mut error,
            )
        };
        if status == libsqlite3_sys::SQLITE_OK {
            return Ok(());
        }
        let message = if error.is_null() {
            format!("sqlite error: {status}")
        } else {
            unsafe {
                std::ffi::CStr::from_ptr(error)
                    .to_string_lossy()
                    .into_owned()
            }
        };
        if !error.is_null() {
            unsafe {
                libsqlite3_sys::sqlite3_free(error.cast());
            }
        }
        Err(message)
    }

    pub fn project_artifact(
        &self,
        artifact_id: &str,
        kind: &str,
        environment: &str,
        payload_json: &str,
    ) -> Result<(), String> {
        self.execute(&format!("INSERT INTO proofir_v3_artifacts(artifact_id,artifact_kind,proofir_version,environment_ref,content_json) VALUES ('{}','{}','3.0','{}','{}')", sql_escape(artifact_id), sql_escape(kind), sql_escape(environment), sql_escape(payload_json)))
    }

    pub fn artifact_count(&self) -> Result<i64, String> {
        let mut statement = std::ptr::null_mut();
        let sql = std::ffi::CString::new("SELECT COUNT(*) FROM proofir_v3_artifacts").unwrap();
        let status = unsafe {
            libsqlite3_sys::sqlite3_prepare_v2(
                self.0,
                sql.as_ptr(),
                -1,
                &mut statement,
                std::ptr::null_mut(),
            )
        };
        if status != libsqlite3_sys::SQLITE_OK {
            return Err(format!("sqlite prepare failed: {status}"));
        }
        let step = unsafe { libsqlite3_sys::sqlite3_step(statement) };
        let count = if step == libsqlite3_sys::SQLITE_ROW {
            unsafe { libsqlite3_sys::sqlite3_column_int64(statement, 0) }
        } else {
            -1
        };
        unsafe {
            libsqlite3_sys::sqlite3_finalize(statement);
        }
        if count < 0 {
            Err("sqlite count failed".into())
        } else {
            Ok(count)
        }
    }

    pub fn integrity_check(&self) -> Result<(), String> {
        if self.query_text("PRAGMA integrity_check")? != "ok" {
            return Err("sqlite integrity check failed".into());
        }
        if !self.query_text("PRAGMA foreign_key_check")?.is_empty() {
            return Err("sqlite foreign-key check failed".into());
        }
        Ok(())
    }

    pub fn database_bytes(&self) -> Result<i64, String> {
        Ok(self.query_i64("PRAGMA page_size")? * self.query_i64("PRAGMA page_count")?)
    }

    pub fn uses_artifact_index(&self) -> Result<bool, String> {
        let plan = self.query_text_at("EXPLAIN QUERY PLAN SELECT artifact_id FROM proofir_v3_artifacts WHERE artifact_kind='proofir.test' ORDER BY artifact_id LIMIT 1", 3)?;
        Ok(plan.contains("idx_v3_artifacts_kind"))
    }

    fn query_i64(&self, sql_text: &str) -> Result<i64, String> {
        let statement = self.prepare(sql_text)?;
        let step = unsafe { libsqlite3_sys::sqlite3_step(statement) };
        let value = if step == libsqlite3_sys::SQLITE_ROW {
            unsafe { libsqlite3_sys::sqlite3_column_int64(statement, 0) }
        } else {
            unsafe { libsqlite3_sys::sqlite3_finalize(statement) };
            return Err(format!("sqlite query failed: {step}"));
        };
        unsafe { libsqlite3_sys::sqlite3_finalize(statement) };
        Ok(value)
    }

    fn query_text(&self, sql_text: &str) -> Result<String, String> {
        self.query_text_at(sql_text, 0)
    }

    fn query_text_at(&self, sql_text: &str, column: i32) -> Result<String, String> {
        let statement = self.prepare(sql_text)?;
        let step = unsafe { libsqlite3_sys::sqlite3_step(statement) };
        let value = if step == libsqlite3_sys::SQLITE_ROW {
            let pointer = unsafe { libsqlite3_sys::sqlite3_column_text(statement, column) };
            if pointer.is_null() {
                String::new()
            } else {
                unsafe {
                    std::ffi::CStr::from_ptr(pointer.cast())
                        .to_string_lossy()
                        .into_owned()
                }
            }
        } else if step == libsqlite3_sys::SQLITE_DONE {
            String::new()
        } else {
            unsafe { libsqlite3_sys::sqlite3_finalize(statement) };
            return Err(format!("sqlite query failed: {step}"));
        };
        unsafe { libsqlite3_sys::sqlite3_finalize(statement) };
        Ok(value)
    }

    fn prepare(&self, sql_text: &str) -> Result<*mut libsqlite3_sys::sqlite3_stmt, String> {
        let mut statement = std::ptr::null_mut();
        let sql = std::ffi::CString::new(sql_text).map_err(|_| "SQL contains NUL".to_string())?;
        let status = unsafe {
            libsqlite3_sys::sqlite3_prepare_v2(
                self.0,
                sql.as_ptr(),
                -1,
                &mut statement,
                std::ptr::null_mut(),
            )
        };
        if status == libsqlite3_sys::SQLITE_OK {
            Ok(statement)
        } else {
            Err(format!("sqlite prepare failed: {status}"))
        }
    }
}

impl Drop for Connection {
    fn drop(&mut self) {
        if !self.0.is_null() {
            unsafe {
                libsqlite3_sys::sqlite3_close(self.0);
            }
        }
    }
}

fn sql_escape(value: &str) -> String {
    value.replace('\'', "''")
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn contract_has_constraints_and_access_path() {
        assert!(SCHEMA_SQL.contains("PRIMARY KEY"));
        assert!(SCHEMA_SQL.contains("FOREIGN KEY") || SCHEMA_SQL.contains("REFERENCES"));
        assert!(SCHEMA_SQL.contains("CREATE INDEX"));
    }

    #[test]
    fn owned_projection_executes_constraints_and_counts_rows() {
        let connection = Connection::open_memory().unwrap();
        connection
            .project_artifact("sha256:test", "proofir.test", "env", "{}")
            .unwrap();
        assert_eq!(connection.artifact_count().unwrap(), 1);
        connection.integrity_check().unwrap();
        assert!(connection.database_bytes().unwrap() > 0);
        assert!(connection.uses_artifact_index().unwrap());
        assert!(connection
            .project_artifact("sha256:test", "proofir.test", "env", "{}")
            .is_err());
    }
}
