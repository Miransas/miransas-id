mod config;
mod db;
mod models;
mod routes;

use config::AppConfig;
use routes::ui::show_login_page;

use axum::{routing::get, Router};
use std::net::SocketAddr;
use tower_http::services::ServeDir;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let config = AppConfig::init();
    
    // VERİTABANI GEÇİCİ OLARAK DEVRE DIŞI
    // let db = init_db(&config.database_url).await;
    // sqlx::migrate!("./migrations").run(&db).await.unwrap();

    let app = Router::new()
        .route("/login", get(show_login_page))
        .nest_service("/static", ServeDir::new("static"));

    let addr = SocketAddr::from(([127, 0, 0, 1], config.server_port));
    println!("🚀 Sunucu başlatıldı: http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}