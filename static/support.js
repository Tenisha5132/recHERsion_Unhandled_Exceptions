(() => {
  const button = document.getElementById('locateSupport');
  const status = document.getElementById('locationStatus');
  const links = Array.from(document.querySelectorAll('.map-link[data-map-query]'));
  if (!button || !status || !links.length) return;

  function mapsUrl(query, coords) {
    const target = query + (coords ? ' near ' + coords : ' near me');
    return 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(target);
  }

  button.addEventListener('click', () => {
    if (!navigator.geolocation) {
      status.textContent = 'Location is not available in this browser. Map links still search near you.';
      return;
    }
    status.textContent = 'Getting your location…';
    navigator.geolocation.getCurrentPosition((position) => {
      const coords = position.coords.latitude.toFixed(4) + ',' + position.coords.longitude.toFixed(4);
      links.forEach((link) => {
        link.href = mapsUrl(link.dataset.mapQuery, coords);
      });
      status.textContent = 'Location added in your browser only. It was not sent to recHERsion.';
    }, () => {
      status.textContent = 'Could not get your location. Map links will search near you.';
    }, { timeout: 8000, maximumAge: 300000 });
  });
})();
