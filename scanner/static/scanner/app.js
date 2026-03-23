document.addEventListener("DOMContentLoaded", () => {
  // 3D Tilt Effect
  const cards = document.querySelectorAll(".card");
  
  cards.forEach(card => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const rotateX = (centerY - y) / 15;
      const rotateY = (x - centerX) / 15;
      
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
      card.style.boxShadow = `${-rotateY * 2}px ${rotateX * 2}px 50px rgba(0,0,0,0.5)`;
    });
    
    card.addEventListener("mouseleave", () => {
      card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
      card.style.boxShadow = "";
    });
  });

  const result = document.querySelector(".result");
  if (!result) return;

  const band = result.dataset.riskBand;
  if (!band) return;

  if (band === "safe") {
    result.classList.add("safe");
  } else if (band === "medium") {
    result.classList.add("medium");
  } else if (band === "high") {
    result.classList.add("unsafe");
  }
});

