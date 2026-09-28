import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Güvenlik amacıyla sadece izin verdiğimiz dış kaynaklardan resim/logo çekilmesini sağlarız
    remotePatterns: [
      {
        protocol: "https",
        hostname: "res.cloudinary.com",
        pathname: "/**", // Cloudinary
      },
      {
        protocol: "https",
        hostname: "://githubusercontent.com",
        pathname: "/**", 
      },
      {
        protocol: "https",
        hostname: "github.com",
        pathname: "/**", 
      },
      {
        protocol: "https",
        hostname: "://githubusercontent.com",
        pathname: "/**", 
      }
    ],
  },
  
  // Eğer projenizde video veya büyük ses dosyaları ağır yükleniyorsa, 
  // kaynak yönetimini ve performans optimizasyonunu artırmak için bu opsiyonları ekleyebilirsiniz:
  experimental: {
    // Büyük medya (video/ses) asset optimizasyon desteği için açık bırakılabilir
  }
};

export default nextConfig;
