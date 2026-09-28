use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, FromRow, Clone)]
pub struct Client {
    pub id: Uuid,
    pub client_id: String,
    pub client_secret_hash: Option<String>,
    pub name: String,
    pub allowed_redirect_uris: Vec<String>,
    pub default_theme: String,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
}
