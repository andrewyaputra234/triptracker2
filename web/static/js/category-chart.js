document.addEventListener('DOMContentLoaded', function () {
  const dataElement = document.getElementById('categoryData');
  if (!dataElement) return;

  const data = JSON.parse(dataElement.textContent);

  const ctx = document.getElementById('categoryChart').getContext('2d');
  new Chart(ctx, {
    type: 'bar', // Change to 'pie' if preferred
    data: {
      labels: Object.keys(data),
      datasets: [{
        label: 'Amount Spent ($)',
        data: Object.values(data),
        backgroundColor: [
          '#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f',
          '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
});
