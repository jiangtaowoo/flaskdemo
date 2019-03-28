var g_schemas = {
  'default': ['front', 'posp', 'audio', 'basic', 'stat', 'mean', 'vocabulary', 'oxford'],
  'simple': ['front', 'posp', 'audio', 'basic', 'stat',  'mean'],
  'vocabulary': ['front', 'posp', 'audio', 'basic', 'stat', 'mean', 'vocabulary'],
  'oxford': ['front', 'posp', 'audio', 'basic', 'stat', 'mean', 'oxford'],
  'full': ['front', 'posp', 'audio', 'transform', 'tag', 'basic', 'stat', 'mean', 'vocabulary', 'oxford', 'collins', 'enmeans']
};
var g_curschema = {
  'front': false,
  'posp': false,
  'audio': false,
  'transform': false,
  'tag': false,
  'basic': false,
  'stat': false,
  'mean': false,
  'vocabulary': false,
  'oxford': false,
  'collins': false,
  'enmeans': false
};

function setViewOptionBySchemaName(schemaname, schemaViewDict) {
  if (schemaname in g_schemas) {
    var cur_schema = g_schemas[schemaname];
    for (var name in schemaViewDict) {
      if (cur_schema.indexOf(name) >= 0) {
        schemaViewDict[name] = true;
      } else {
        schemaViewDict[name] = false;
      };
    };
  };
};

setViewOptionBySchemaName('default', g_curschema);

Vue.component('vocabulary-card', {
  props: {
    vcard: Object,
    viewopt: Object,
    vindex: Number
  },
  template: '#template-vcard'
});

var app_cards = new Vue({
  el: '#app-vocabulary-card',
  data: {
    cards: [],
    schema: g_curschema
  }
});

var app_schema = new Vue({
  el: '#app-sel-schema',
  data: {
    selected: 'default',
    schemas: g_schemas
  },
  computed: {
    options: function () {
      var op_list = [];
      for (var name in this.schemas) {
        op_list.push({
          text: name,
          value: name
        });
      }
      return op_list;
    }
  },
  methods: {
    refreshCardViewOption: function () {
      setViewOptionBySchemaName(this.selected, g_curschema);
      Vue.set(app_cards, "schema", g_curschema);
    }
  }
});

var app_themes = new Vue({
  el: '#app-sel-theme',
  data: {
    seltheme: "theme-default",
    schemas: {'theme-default': '/vocabulary/static/css/render-theme-light.css', 
              'theme-dark':'/vocabulary/static/css/render-theme-dark.css',
              'theme-solarized': '/vocabulary/static/css/render-theme-solarized.css'}
  },
  computed: {
    options: function () {
      var op_list = [];
      for (var name in this.schemas) {
        op_list.push({
          text: name,
          value: name
        });
      }
      return op_list;
    }
  },
  methods: {
    refreshCardTheme: function () {
      console.log(this.seltheme);
      document.getElementById("style-render-theme").setAttribute("href", this.schemas[this.seltheme]);
    }
  }
});

var app_query = new Vue({
  el: '#app-word-toquery',
  data: {
    word: ''
  },
  methods: {
    queryVocabulary: function (event) {
      event.preventDefault();
      if (this.word.length > 2 && (event.key == "Enter" || event.key == "*")) {
        axios.post("/vocabulary/", {
            word: this.word
          })
          .then(function (response) {
            app_cards.cards = response.data;
          })
          .catch(function (error) {
            console.log(error);
          });
      }
    }
  }
});