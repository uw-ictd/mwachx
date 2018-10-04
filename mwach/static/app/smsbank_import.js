(function($) {
	function getCookie(name) {
	    var cookieValue = null;
	    if (document.cookie && document.cookie !== '') {
	        var cookies = document.cookie.split(';');
	        for (var i = 0; i < cookies.length; i++) {
	            var cookie = $.trim(cookies[i]);
	            if (cookie.substring(0, name.length + 1) === (name + '=')) {
	                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
	                break;
	            }
	        }
	    }
	    return cookieValue;
	}

	function upload(e) {
		if($(this).attr('id') == 'check_form'){
			e.preventDefault();
		  	var form_data = new FormData($("#check_form").get(0));
			$.ajax({
				url: $(this).attr('action'),
				// type: $(this).attr('method'),
				method: $(this).attr('method'),
				data: form_data,
				contentType: false,
				cache: false,
				processData: false,
				success: function(response) {
					if (response["success"]) {
						console.log('success');
						$('#submit-id-submit').val('Import File');
						$('#check_form').attr('id', 'import_form');
						$('#import_form').attr('action', response['url']);
						$("[name='csrfmiddlewaretoken']").val(getCookie('csrftoken'));
						$('#total_rows').html(response['total']);
						$('#duplicate_count').html(response['duplicates'].length);
						for ( var i =0; i < response['duplicates'].length; i++) {
							$('#duplicate_rows').append('<li>' + response['duplicates'][i] + "</li>");
						}
						$('#invalid_count').html(response['errors'].length);
						for ( var i =0; i < response['errors'].length; i++) {
							$('#invalid_rows').append('<li>' + response['errors'][i] + "</li>");
						}
						$('#checked_file').removeClass('hidden');
					}
				}
			});
			return false;
		}
	}
	$(document).ready(function() {
		$('#check_form').submit(upload);
	});
})(django.jQuery);