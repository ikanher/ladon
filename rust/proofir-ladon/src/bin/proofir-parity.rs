use proofir_core::canonical_bytes;
use proofir_ladon::normalized_rows;
use serde_json::{json, Value};
use std::{env, fs, process};

fn main() {
    let Some(path) = env::args().nth(1) else {
        eprintln!("usage: proofir-parity VECTOR.json");
        process::exit(2);
    };
    let raw = fs::read_to_string(path).expect("read vector");
    let vector: Value = serde_json::from_str(&raw).expect("decode vector");
    let artifact = vector["artifact"].clone();
    let rows = normalized_rows(artifact.clone()).expect("validate artifact");
    let canonical =
        String::from_utf8(canonical_bytes(&artifact).expect("canonicalize")).expect("utf8");
    println!("{}", serde_json::to_string(&json!({"artifactId": artifact["artifactId"], "canonical": canonical, "normalized": rows})).unwrap());
}
