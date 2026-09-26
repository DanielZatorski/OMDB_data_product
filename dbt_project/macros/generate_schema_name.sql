{#
  dbt's default behavior concatenates the target schema with the custom
  schema (e.g. "main_staging"). We want the schema to be exactly "staging"
  or "marts", matching the README's Architecture table, so override it.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
