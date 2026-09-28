// Sayfa yüklendiğinde çalışacak animasyonlar
document.addEventListener("DOMContentLoaded", () => {
    console.log("Login JS Yüklendi! Animasyonlar başlıyor...");

    const formSection = document.getElementById("form-section");
    
    // Sağdan sola yumuşak bir giriş animasyonu (Vanilla JS)
    formSection.style.opacity = "0";
    formSection.style.transform = "translateX(50px)";
    formSection.style.transition = "all 0.8s cubic-bezier(0.25, 1, 0.5, 1)";

    // Küçük bir gecikme ile animasyonu tetikle
    setTimeout(() => {
        formSection.style.opacity = "1";
        formSection.style.transform = "translateX(0)";
    }, 100);

    // Buraya daha sonra Shader mantığı (WebGL) veya parçacık efektleri eklenebilir!
    const canvas = document.getElementById("shader-canvas");
    if(canvas) {
        // İleride 3D veya shader kodlarını buraya yazacağız.
    }
});


document.addEventListener("DOMContentLoaded", () => {
    const themeToggleBtn = document.getElementById("theme-toggle");
    
    // 1. Tarayıcı hafızasından (localStorage) önceki seçimi oku
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
    }

    // 2. Butona tıklandığında temayı değiştir ve hafızaya yaz
    themeToggleBtn.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
        
        if (document.body.classList.contains("dark-mode")) {
            localStorage.setItem("theme", "dark");
        } else {
            localStorage.setItem("theme", "light");
        }
    });
});