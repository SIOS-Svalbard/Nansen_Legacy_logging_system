$(document).ready(function() {
  $('.dropdown').hover(
    function() {
      if ($(window).width() > 991) {
        $(this).find('.dropdown-toggle').dropdown('toggle');
      }
    },
    function() {
      if ($(window).width() > 991) {
        $(this).find('.dropdown-toggle').dropdown('toggle');
      }
    }
  );
});
