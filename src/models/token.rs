use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct AuthCode {
    pub code: String,
    pub client_id: String,
    pub user_id: Uuid,
    pub redirect_uri: String,
    pub expires_at: DateTime<Utc>,
    pub used: bool,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct RefreshToken {
    pub id: Uuid,
    pub user_id: Uuid,
    pub client_id: String,
    pub token_hash: String,
    pub expires_at: DateTime<Utc>,
    pub is_revoked: bool,
    pub created_at: DateTime<Utc>,
}
