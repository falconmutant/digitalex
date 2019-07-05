$(function() {
    $('#contact').validate({
        rules: {
            name: {
                required: true,
                minlength: 2
            },
            email: {
                required: true,
                email: true
            },
            message: {
                required: true,
                minlength: 5
            }
        },
        messages: {
            name: {
                required: "Name is required",
                minlength: "At least 2 characters"
            },
            email: {
                required: "Email is required"
            },
            message: {
                required: "Message is required",
                minlength: "At least 5 characters"
            }
        },
        submitHandler: function(form) {
            $(form).ajaxSubmit({
                type:"POST",
                data: $(form).serialize(),
                url:"contact_form.php",
                success: function() {
                    $('.contact-form .alert-success').fadeIn();
                },
                error: function() {
                    $('.contact-form .alert-danger').fadeIn(); 
                }
            });
        }
    });
});