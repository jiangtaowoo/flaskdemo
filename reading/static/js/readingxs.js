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
    var index = app_tab_content_main.cardnames.indexOf(word);
    if (index < 0) {
            axios.get("/vocabulary/" + word, {
                params: {
                    "format": "html"
                }
            })
            .then(function (response) {
                rsp_data = response.data;
                if (rsp_data) {
                    app_tab_content_main.cards.push(rsp_data);
                    app_tab_content_main.cardnames.push(word);
                }
            })
            .catch(function (error) {
                console.log(error);
            });
    };
};

app_tab_content_main = new Vue({
    el: "#app-tab-contentmain",
    data: {
        showType: 1,
        showTypeChanged: false,
        marker: null,
        cards: [],
        cardnames: [],
        schema: g_curschema,
        scrollPos: [[0,0],[0,0]]
    },
    mounted: function () {
        this.$nextTick(function () {
            if (this.marker==null) {
                var elem_for_mark = document.getElementById("app-left-whole-content");
                this.marker = new Mark(elem_for_mark);
            }
        });
    },
    updated: function () {
        if (this.showTypeChanged) {
            window.scroll(this.scrollPos[(this.showType-1)%2][0], this.scrollPos[(this.showType-1)%2][1]);
            this.showTypeChanged = false;
        }
    }
});


Vue.component('vocabulary-card', {
    props: {
        vcard: Object,
        viewopt: Object
    },
    template: '#template-vcard'
});

function searchSelectionWord() {
    var sel_word = getSelectionText().trim();
    if (sel_word.length > 2) {
        if (app_tab_content_main.marker != null) {
            var instance_Content = app_tab_content_main.marker;
            instance_Content.mark(sel_word);
            ansyncLoadWord(sel_word);
        }
    }
};


app_tab_controller = new Vue({
    el: "#app-tabs-controller",
    data: {
        curTab: 1
    },
    methods: {
        setViewContent: function(showType) {
            //console.log(window.pageYOffset);
            this.curTab = parseInt(showType);
            var idx = this.curTab==1? 1: 0;
            app_tab_content_main.showType = this.curTab;
            app_tab_content_main.scrollPos[idx][0] = window.pageXOffset;
            app_tab_content_main.scrollPos[idx][1] = window.pageYOffset;
            app_tab_content_main.showTypeChanged = true;
        },
        searchWord: function(e) {
            e.preventDefault();
            searchSelectionWord();
        }
    }
});

/*
按下回车键, 搜索选中的单词
*/
document.onkeyup = function (event) {
    if (event.key == "Enter") {
        searchSelectionWord();
    }
};