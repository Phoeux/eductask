function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

function add_book(form){
    let title = form.title.value;
    let text = form.text.value;
    let arr_genre = JSON.stringify($(form.genre).val());
    console.log(title, text, arr_genre);
    $($(form).children()[6]).trigger('click');
    $.ajax({
        url: '/shop/add_new_book_ajax/',
        method: 'post',
        data: {
                'csrfmiddlewaretoken': csrftoken,
                'title': title,
                'text': text,
                'genre': arr_genre
        },
        success: function (data) {
            $('div.book_container').append(`<h1>${title}</h1> <h5>${text}</h5>`)
        }
    })
}

function add_comment(form, slug, id)  {
    let text = form.text.value;

    console.log(text, slug);
    $.ajax({
        url: '/shop/add_new_comment_ajax/',
        method: 'post',
        data: {
            'csrfmiddlewaretoken': csrftoken,
            'text': text,
            'book_id': id,
        },
        success: function (data) {
            $('#'+slug).append(`${text}`)
        }
    })
}


$('document').ready(function () {
    $('span.comment_like').on('click', function() {
        let cl_id = $(this).attr('id');
        let object_comment = this;
        $.ajax({
            url:'/shop/add_like_ajax/',
            data: {'cl_id': cl_id, 'csrfmiddlewaretoken': csrftoken},
            method: 'post',
            success: function (data) {
                $(object_comment).html(` Like: ${data['count_like']}`);
                let th = $(object_comment).parent();
                if (data['flag']) {
                    $(object_comment).attr('class', 'comment_like fa  fa-star checked ');
                    $(th).append(`<span class='col'>${data['user']}</span>`)
                } else {
                    $(object_comment).attr('class', 'comment_like fa');
                    for (var i = 0; i < $(th).children().length; i++) {
                        let item = $(th).children()[i];
                        if ($(item).html() == data['user']) {
                            $(th).children()[i].remove();
                            break
                        }
                    }
                }
            }
        });
    });

    $('span.book_rate').on('click', function () {
    let arr = $(this).attr('id').split('-');
        let book_id = arr[1];
        let book_rate = arr[2];
        let obj = this;
        $.ajax ({
            url: '/shop/add_book_rate_ajax/',
            method: 'post',
            data: {'book_id': book_id, 'rate': book_rate, 'csrfmiddlewaretoken': csrftoken},
            success:function(data) {
                let rate = $(obj).parent();
                let children = $(rate).children();
                let text = children[0];
                $(text).html(`Rate: ${data['cached_rate']}`);
                for (let i = 1; i <= 10; i++){
                    if (data['rate']  >= i - 1) {
                       $(children[i]).attr('class', 'book_rate fa fa-star checked')
                    } else {
                       $(children[i]).attr('class', 'book_rate fa fa-star')
                        }
                }
                   if (data['flag']){
                        $(rate).append(`<span>${data['user']}</span>`)
                        }

            }

        })
    })

    $('button.delete-comment').on('click', function (){
        let id = $(this).attr('id').split('-')[1];
        let obj = this;
        $.ajax({
            url: `/shop/delete_comment_ajax/${id}`,
            method: 'delete',
            headers: {'X-CSRFToken': csrftoken},
            success: function (data) {
                $(obj).parent().remove();
            }
        })
    });

//    $('a.add_new_book').on('click', function() {
//        let arr = $(this).parent().children();
//        let title = $(arr[0]).val();
//        let text = $(arr[1]).val();
//        let genre = JSON.stringify($(arr[4]).val());
//        $('modal').modal('toggle');
//        let close = $(this).parent().parent().children()[1];
////        $(close).trigger('click')
//        $.ajax({
//            url: '/shop/add_new_book_ajax/',
//            method: 'post',
//            data: {
//                'csrfmiddlewaretoken': csrftoken,
//                'title': title,
//                'text': text,
//                'genre': genre},
//            success: function(data) {
//                console.log(data)
//            }
//        }) //append как выше
//    })

});


//$('document').ready(function () {
//    $('span.book_rate').on('click', function () {
//        let br_id = $(this).attr('id');
//        $.ajax({
//            url: '/shop/add_rate_ajax/',
//            data: {'br_id': br_id, 'csrfmiddlewaretoken': csrftoken},
//            method: 'post',
//            success: function (data) {
//                console.log(data)
//            }
//        });
//    });
//});

