use sqlx::postgres::PgPoolOptions;
use sqlx::{Pool, Postgres};

pub type DbPool = Pool<Postgres>;

pub async fn init_db(database_url: &str) -> DbPool {
    PgPoolOptions::new()
        .max_connections(10)
        .connect(database_url)
        .await
        .expect("PostgreSQL veritabanına bağlanılamadı!")
}
