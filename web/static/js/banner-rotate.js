const images = [
  "/static/css/images/NJ0002.jpg",
  "/static/css/images/NJ0003.jpg",
  "/static/css/images/NJ0004.jpg"
];

let index = 0;
const banner = document.getElementById("banner");

function rotateBackground() {
  if (!banner) return;

  // Fade out
  banner.style.opacity = 0;

  setTimeout(() => {
    // Change background image after fade out
    banner.style.backgroundImage = `url('${images[index]}')`;
    index = (index + 1) % images.length;

    // Fade back in
    banner.style.opacity = 1;
  }, 1000);  // This matches the CSS opacity transition time
}

// Initial setup
banner.style.backgroundImage = `url('${images[index]}')`;
banner.style.opacity = 1;
index++;

// Change every 5 seconds (or whatever you prefer)
setInterval(rotateBackground, 5000);
