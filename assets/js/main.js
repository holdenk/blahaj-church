$(document).ready(function() {
  // Mobile nav toggle
  $('.nav-toggle').on('click', function() {
    $('.nav-menu').toggleClass('active');
  });

  // Close menu when clicking a link
  $('.nav-menu a').on('click', function() {
    $('.nav-menu').removeClass('active');
  });
});
