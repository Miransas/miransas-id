export default function AuthBanner() {
  return (
    <div className="hidden lg:flex relative flex-1 h-full bg-[#080808] overflow-hidden items-center justify-center">
      {/* Arka plan görsel simülasyonu ve altın sarısı premium ışık süzmesi */}
      <div className="absolute inset-0 bg-gradient-to-tr from-amber-500/10 via-transparent to-transparent opacity-60 pointer-events-none" />
      <img src="https://res.cloudinary.com/dwdk20m6q/image/upload/v1790282774/Firefly_RemoveBackground_mre4pp.png" alt=""  className="absolute"/>
      {/* Oyun Görseli Alanı Konsepti */}
      <div className="relative z-10 text-center p-8 max-w-md">
        <div className="w-24 h-1 bg-amber-500 mx-auto mb-6 rounded-full" />
        <h2 className="text-4xl font-extrabold text-white tracking-tight leading-tight uppercase font-sans mb-4">
          Call of Duty
        </h2>
        <p className="text-stone-400 text-sm leading-relaxed">
          Hesabınıza giriş yaparak en güncel operasyonlara katılın, ilerlemenizi tüm platformlarda senkronize edin.
        </p>
      </div>

      {/* Sağ tarafa yumuşak geçiş gölgesi (Form alanına doğru) */}
      <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-[#050505] to-transparent pointer-events-none" />
    </div>
  );
}
