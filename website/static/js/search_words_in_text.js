$(document).ready(function(){
  // Search functionality
  $('.search-box input[type="text"]').on('keyup', function() {
    var searchText = $(this).val().toLowerCase();
    var searchWords = searchText.split(' ');
    $('.list-group label').each(function() {
      var currentItemText = $(this).text().toLowerCase();
      var matchCount = 0;
      for(var i = 0; i < searchWords.length; i++) {
        if(currentItemText.indexOf(searchWords[i]) > -1) {
          matchCount++;
        }
      }
      if(matchCount == searchWords.length) {
        $(this).show();
      } else {
        $(this).hide();
      }
    });
  });
});
