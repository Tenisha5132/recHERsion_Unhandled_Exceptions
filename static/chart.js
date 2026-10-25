const canvas = document.getElementById('cycleChart');
if (canvas) {
  const ctx = canvas.getContext('2d');
  // simple example - would use real data
  ctx.fillStyle = '#6b46c1';
  ctx.fillRect(10, 100, 20, -40);
  ctx.fillRect(40, 100, 20, -52);
  ctx.fillRect(70, 100, 20, -45);
  ctx.strokeStyle = '#2f9e44';
  ctx.beginPath();
  ctx.moveTo(0, 79);
  ctx.lineTo(300, 79); // 21 days line approx
  ctx.stroke();
  ctx.strokeStyle = '#e03131';
  ctx.beginPath();
  ctx.moveTo(0, 65);
  ctx.lineTo(300, 65); // 35 days line approx
  ctx.stroke();
  ctx.fillStyle = '#000';
  ctx.fillText('21/35 day band', 5, 75);
}
