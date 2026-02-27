// Mobile nav toggle
(function() {
  var toggle = document.querySelector('.nav-toggle');
  var menu = document.querySelector('.nav-menu');

  if (toggle && menu) {
    toggle.addEventListener('click', function() {
      var expanded = menu.classList.toggle('active');
      toggle.setAttribute('aria-expanded', expanded);
    });

    // Close menu when clicking a link
    var links = menu.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) {
      links[i].addEventListener('click', function() {
        menu.classList.remove('active');
        toggle.setAttribute('aria-expanded', 'false');
      });
    }
  }
})();

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
  anchor.addEventListener('click', function(e) {
    var target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});
