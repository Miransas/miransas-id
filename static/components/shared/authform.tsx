"use client";

import { useState } from "react";

export default function AuthForm() {
  const [activeTab, setActiveTab] = useState<"login" | "register">("login");
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="w-full max-w-[480px] bg-[#0a0a0a] border border-stone-900 rounded-2xl p-8 md:p-12 shadow-2xl flex flex-col justify-center">
      {/* Üst Logo ve Başlık */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-extrabold tracking-widest text-white uppercase font-sans mb-3">
          ACTIVISION
        </h1>
        <p className="text-stone-300 font-medium text-lg">
          {activeTab === "login" ? "Hesabınızla oturum açın" : "Yeni bir hesap oluşturun"}
        </p>
      </div>

      {/* Login / Register Sekmeleri (Tabs) */}
      <div className="flex border-b border-stone-900 mb-6">
        <button
          onClick={() => setActiveTab("login")}
          className={`flex-1 pb-3 text-sm font-semibold tracking-wide transition-colors ${
            activeTab === "login"
              ? "text-white border-b-2 border-white"
              : "text-stone-500 hover:text-stone-300"
          }`}
        >
          Oturum Aç
        </button>
        <button
          onClick={() => setActiveTab("register")}
          className={`flex-1 pb-3 text-sm font-semibold tracking-wide transition-colors ${
            activeTab === "register"
              ? "text-white border-b-2 border-white"
              : "text-stone-500 hover:text-stone-300"
          }`}
        >
          Kaydol
        </button>
      </div>

      {/* Form Alanı */}
      <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-2">
            E-posta Adresi
          </label>
          <input
            type="email"
            placeholder="örnek@alanadi.com"
            className="w-full bg-[#121212] border border-stone-800 rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-stone-600 transition-colors placeholder-stone-600"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-stone-400 mb-2">
            Parola
          </label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              placeholder="Parola Gir"
              className="w-full bg-[#121212] border border-stone-800 rounded-lg px-4 py-3 text-white text-sm focus:outline-none focus:border-stone-600 transition-colors placeholder-stone-600 pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-stone-500 hover:text-stone-300 transition-colors"
            >
              {showPassword ? "👁️" : "👁️‍🗨️"}
            </button>
          </div>
        </div>

        {activeTab === "login" && (
          <div className="text-right">
            <a href="#" className="text-xs text-stone-400 hover:text-white underline tracking-wide transition-colors">
              Oturum Açarken Sorun mu Yaşıyorsunuz?
            </a>
          </div>
        )}

        <button
          type="submit"
          className="w-full bg-[#1c1c1c] hover:bg-white hover:text-black border border-stone-800 text-stone-400 font-bold py-3 px-4 rounded-lg tracking-wider uppercase text-sm transition-all duration-200 mt-2"
        >
          {activeTab === "login" ? "Oturum Aç" : "Kayıt Ol"}
        </button>
      </form>

      {/* Sosyal Medya ile Giriş (Görseldeki İkon Alanı) */}
      <div className="mt-8 pt-6 border-t border-stone-900 text-center">
        <p className="text-xs font-semibold text-stone-500 uppercase tracking-widest mb-4">
          Veya, şunları kullanarak oturum aç:
        </p>
        <div className="flex justify-center items-center gap-4">
          {/* İkonları temsili olarak butonlaştırdık */}
          {["PlayStation", "Xbox", "Steam", "Battle.net", "Nintendo"].map((platform) => (
            <button
              key={platform}
              title={platform}
              className="w-10 h-10 rounded-lg bg-[#121212] border border-stone-800 flex items-center justify-center text-stone-400 hover:text-white hover:border-stone-600 transition-colors text-xs font-bold"
            >
              {platform[0]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
