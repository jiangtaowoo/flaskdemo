var g_curschema = {
    'front': false,
    'posp': false,
    'transform': false,
    'tag': false,
    'basic': true,
    'audio': true,
    'mean': true,
    'stat': false,
    'vocabulary': true,
    'oxford': true,
    'collins': false,
    'enmean': false
};

var content_pos = 0;

function scrollWordCardIntoView(word) {
    word = word.trim().toLowerCase();
    var index = app_card_container.cardnames.indexOf(word);
    if (index >= 0) {
        var voc_container = document.getElementById("app-voc-card");
        var need_height = 0;
        for (var i = 0; i < index; i++) {
            need_height += voc_container.childNodes[i].clientHeight;
        }
        voc_container.scrollTop = need_height;
    }
};

function restoreWordContentView() {
    var content_elem = document.getElementById("app-left-whole-content");
    content_elem.scrollTop = content_pos;
};

//调整文章视图, 将当前单词置于视图top位置
function scrollWordContentIntoView(word) {
    var mark_elems = document.getElementsByTagName("mark");
    var content_elem = document.getElementById("app-left-whole-content");
    var dest_pos = null;
    var cur_top = content_elem.scrollTop;
    var cur_bottom = cur_top + content_elem.clientHeight;
    for (var idx in mark_elems) {
        //console.log(mark_elems[idx].innerText);
        var index = mark_elems[idx].innerText.toLowerCase().indexOf(word);
        if (index>=0) {
            dest_pos = mark_elems[idx].offsetTop;
            break;
        }
    }
    if (dest_pos<cur_top || dest_pos>cur_bottom) {
        content_pos = cur_top;
        content_elem.scrollTop = dest_pos;
    }
};

/*输入部分单词时, 定位到对应的单词卡并显示*/
function scrollPartialWordIntoView(partial_input) {
    var match_word = null;
    partial_input = partial_input.trim().toLowerCase();
    for (var idx in app_card_container.cardnames) {
        var word = app_card_container.cardnames[idx];
        var index = word.indexOf(partial_input);
        if (index >= 0) {
            match_word = word;
            break;
        }
    }
    if (match_word) {
        scrollWordCardIntoView(match_word);
    }
};

function getSelectionText() {
    var text = "";
    var activeEl = document.activeElement;
    var activeElTagName = activeEl ? activeEl.tagName.toLowerCase() : null;
    if (
        (activeElTagName == "textarea") || (activeElTagName == "input" &&
            /^(?:text|search|password|tel|url)$/i.test(activeEl.type)) &&
        (typeof activeEl.selectionStart == "number")
    ) {
        text = activeEl.value.slice(activeEl.selectionStart, activeEl.selectionEnd);
    } else if (window.getSelection) {
        text = window.getSelection().toString();
    }
    return text;
};


//load word translation result
function ansyncLoadWord(word) {
    var index = app_card_container.cardnames.indexOf(word);
    if (index < 0) {
            axios.get("/vocabulary/" + word, {
                params: {
                    "format": "html"
                }
            })
            .then(function (response) {
                rsp_data = response.data;
                if (rsp_data) {
                    //console.log(rsp_data);
                    //app_card_container.cards.splice(0, 0, rsp_data);
                    //app_card_container.cardnames.splice(0, 0, word);
                    app_card_container.cards.push(rsp_data);
                    app_card_container.cardnames.push(word);
                }
            })
            .catch(function (error) {
                console.log(error);
            });
    } else {
        scrollWordCardIntoView(word);
    }
};

var instance_Content = new Mark(document.getElementById("app-left-whole-content"));

Vue.component('vocabulary-card', {
    props: {
        vcard: Object,
        viewopt: Object
    },
    template: '#template-vcard'
});

var app_card_container = new Vue({
    el: '#app-voc-card',
    data: {
        cards: [],
        cardnames: [],
        schema: g_curschema
    },
    updated: function () {
        if (this.cardnames.length > 0) {
            var new_word = this.cardnames[this.cardnames.length - 1];
            scrollWordCardIntoView(new_word);
        }
    }
});

var app_keyword_search = new Vue({
    el: "#app-keyword-search",
    data: {
        wordtosearch: ""
    },
    methods: {
        partialKeyWordMark: function (event) {
            event.preventDefault();
            //console.log(this.wordtosearch);
            if (event.key == "Escape") {
                this.wordtosearch = "";
                instance_Content.unmark();
                instance_Content.mark(app_card_container.cardnames);
                restoreWordContentView();
            } else {
                if (this.wordtosearch.length == 0) {
                    instance_Content.unmark();
                    instance_Content.mark(app_card_container.cardnames);
                    restoreWordContentView();
                }
                if (this.wordtosearch.length > 1) {
                    var markword = this.wordtosearch.toLowerCase()
                    instance_Content.unmark();
                    instance_Content.mark(app_card_container.cardnames);
                    instance_Content.mark(markword);
                    scrollPartialWordIntoView(markword);
                    scrollWordContentIntoView(markword);
                }
            }
        },
        loadAnkiCard: function (event) {
            event.preventDefault();
            //console.log(event);
            var sel_word = this.wordtosearch.trim().toLowerCase();
            if (sel_word.length < 3) {
                sel_word = getSelectionText().trim().toLowerCase();
            }
            if (sel_word.length > 2) {
                var content_elem = document.getElementById("app-left-whole-content");
                content_pos = content_elem.scrollTop;       //update current pos
                ansyncLoadWord(sel_word);
            }
        }
    }
});

/*
按下回车键, 搜索选中的单词
*/
document.onkeyup = function (event) {
    if (event.key == "Enter") {
        var sel_word = getSelectionText().trim().toLowerCase();
        if (sel_word.length > 2) {
            instance_Content.mark(sel_word);
            ansyncLoadWord(sel_word);
        }
    } else if (event.key == "Escape") {
        app_keyword_search.wordtosearch = "";
        instance_Content.unmark();
        instance_Content.mark(app_card_container.cardnames);
        restoreWordContentView();
    }
};

/*
双击选中文本时, 如果单词表中包含了这个单词, 则滚动到当前位置显示
*/
document.ondblclick = function (event) {
    var sel_word = getSelectionText().trim().toLowerCase();
    if (sel_word.length > 2) {
        scrollWordCardIntoView(sel_word);
    }
};