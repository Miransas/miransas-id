use askama::Template;
use axum::{
    extract::Query,
    http::{StatusCode, header},
    response::{Html, IntoResponse, Response},
};
use serde::Deserialize;

#[derive(Deserialize)]
pub struct LoginQueryParams {
    pub client_id: Option<String>,
    pub redirect_uri: Option<String>,
    pub theme: Option<String>,
    pub locale: Option<String>,
    pub login_token: Option<String>,
}

#[derive(Template)]
#[template(path = "login.html")]
pub struct LoginTemplate {
    pub client_name: String,
    pub client_id: String,
    pub redirect_uri: String,
    pub theme: String,
    pub locale: String,
    pub login_token: String,
}

impl IntoResponse for LoginTemplate {
    fn into_response(self) -> Response {
        match self.render() {
            Ok(html) => Html(html).into_response(),
            Err(err) => {
                tracing::error!("Template render hatası: {:?}", err);
                (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "Sayfa yüklenirken bir hata oluştu.",
                )
                    .into_response()
            }
        }
    }
}

pub async fn show_login_page(Query(params): Query<LoginQueryParams>) -> impl IntoResponse {
    let theme = params.theme.unwrap_or_else(|| "default".to_string());
    let locale = params.locale.unwrap_or_else(|| "tr".to_string());
    let redirect_uri = params.redirect_uri.unwrap_or_default();
    let client_id = params.client_id.unwrap_or_default();
    let login_token = params
        .login_token
        .unwrap_or_else(|| uuid::Uuid::new_v4().to_string());

    let client_name = match theme.as_str() {
        "cod" => "Activision".to_string(),
        _ => "Merkezi Auth".to_string(),
    };

    LoginTemplate {
        client_name,
        client_id,
        redirect_uri,
        theme,
        locale,
        login_token,
    }
}
