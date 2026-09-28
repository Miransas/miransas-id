-- 1. Clients Tablosu (Sisteme kayıtlı istemciler: SaaS, COD Mobile, Oyunlar vb.)
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(64) NOT NULL UNIQUE,
    client_secret_hash VARCHAR(255), -- Mobil/oyun istemcileri için NULL olabilir (PKCE kullanılır)
    name VARCHAR(100) NOT NULL,
    allowed_redirect_uris TEXT[] NOT NULL,
    default_theme VARCHAR(50) NOT NULL DEFAULT 'default',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users Tablosu (Ortak kullanıcı hesabı)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Auth Codes Tablosu (OAuth 2.0 Authorization Code Flow için geçici kodlar)
CREATE TABLE IF NOT EXISTS auth_codes (
    code VARCHAR(128) PRIMARY KEY,
    client_id VARCHAR(64) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    redirect_uri TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Refresh Tokens Tablosu (Uzun ömürlü oturumları yönetmek ve iptal edebilmek için)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_id VARCHAR(64) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);