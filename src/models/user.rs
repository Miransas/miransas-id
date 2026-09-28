use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, FromRow, Clone)]
pub struct User {
    pub id: Uuid,
    pub email: String,
    #[serde(skip_serializing)] // Şifre hash'ini JSON yanıtlarında dışarı sızdırmıyoruz
    pub password_hash: String,
    pub is_verified: bool,
    pub created_at: DateTime<Utc>,
}
