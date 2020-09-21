"use strict";
const request = require('./request');
const server = '{{server}}';

const ERROR_CODE = {
  {% for error_code in error_codes %}{{error_code.tag}}: {{error_code.code}}{% if not forloop.last %},{% endif %} // {{error_code.desc}}{% if not forloop.last %}
  {% endif %}{% endfor %}
}
{% for api in apis %}

// {{api.name}}
const {{ api.ul_name }} = function({% if api.self_params %}{
  {% for field_name, field in api.info.request_info.items %}{% if field_name not in base_params %}{{ field_name }}{% if not forloop.last %},{% endif %} // {{ field.label }}{% if not forloop.last %}
  {% endif %}{% endif %}{% endfor %}
} = {}{% endif %}) {
  return request({
    server: server,
    path: '{{ api.url }}',
    method: '{{ api.suggest_method }}',
    data: {{% if api.self_params %}
      {% for field_name, field in api.info.request_info.items %}{% if field_name not in base_params %}{{ field_name }}: {{ field_name}}{% if not forloop.last %},
      {% endif %}{% endif %}{% endfor %}
    {% endif %}},
    header: { 'Content-Type': '{{api.content_type}}' }
  })
}
{% endfor %}

module.exports = {
  ERROR_CODE: ERROR_CODE,
  {% for api in apis %}{{ api.ul_name }}: {{ api.ul_name }}{% if not forloop.last %},
  {% endif %}{% endfor %}
}
