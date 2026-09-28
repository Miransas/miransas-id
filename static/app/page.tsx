import AuthBanner from "../components/shared/auth-banner";
import AuthForm from "../components/shared/authform";


export default function AuthPage() {
  return (
    <main className="flex flex-col min-h-screen bg-[#050505] justify-between">
      
      {/* Üst İki Sütunlu Ana İçerik */}
      <div className="flex flex-1 items-center justify-center h-full">
        {/* Sol Panel: Oyun Görsel Alanı */}
        <AuthBanner />

        {/* Sağ Panel: Giriş/Kayıt Formu */}
        <div className="flex-1 flex items-center justify-center p-4 md:p-8 z-10">
          <AuthForm />
        </div>
      </div>

      {/* Alt Footer Alanı (Görseldeki Linkler) */}
      <footer className="w-full py-6 bg-[#030303] border-t border-stone-900/60 text-center z-10">
        <div className="max-w-5xl mx-auto px-4 flex flex-wrap justify-center gap-x-6 gap-y-2 text-xs font-medium text-stone-500">
          <a href="#" className="hover:text-stone-300 transition-colors">Yasal Bilgiler</a>
          <a href="#" className="hover:text-stone-300 transition-colors">Kullanım Şartları</a>
          <a href="#" className="hover:text-stone-300 transition-colors">Gizlilik İlkesi</a>
          <a href="#" className="hover:text-stone-300 transition-colors">Çerez Politikası</a>
          <a href="#" className="hover:text-stone-300 transition-colors">Çerez Ayarları</a>
          <a href="#" className="hover:text-stone-300 transition-colors">Çevrimiçi Güvenlik Kılavuzu</a>
          <a href="#" className="hover:text-stone-300 transition-colors">Destek</a>
        </div>
        <p className="text-[10px] text-stone-600 mt-4 tracking-widest uppercase font-bold">
          © 2026 ACTIVISION PUBLISHING, INC.
        </p>
      </footer>
    </main>
  );
}
