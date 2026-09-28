use std::env;

#[derive(Clone, Debug)]
pub struct AppConfig {
    pub database_url: String,
    pub jwt_secret: String,
    pub server_port: u16,
}

impl AppConfig {
    pub fn init() -> Self {
        dotenvy::dotenv().ok();

        let database_url =
            env::var("DATABASE_URL").expect("DATABASE_URL .env dosyasında bulunamadı!");
        let jwt_secret = env::var("JWT_SECRET").expect("JWT_SECRET .env dosyasında bulunamadı!");
        let server_port = env::var("SERVER_PORT")
            .unwrap_or_else(|_| "3000".to_string())
            .parse::<u16>()
            .expect("SERVER_PORT geçerli bir sayı olmalıdır!");

        AppConfig {
            database_url,
            jwt_secret,
            server_port,
        }
    }
}
