from crispy_tailwind.tailwind import CSSContainer

# DaisyUI native classes — theme-aware, no dark: hacks needed
base_input = "input input-bordered w-full"
base_textarea = "textarea textarea-bordered w-full"

custom_styles = {
    "text": base_input,
    "number": base_input,
    "radioselect": "",
    "email": base_input,
    "url": base_input,
    "password": base_input,
    "hidden": "",
    "multiplehidden": "",
    "file": "",
    "clearablefile": "",
    "textarea": base_textarea,
    "date": base_input,
    "datetime": base_input,
    "time": base_input,
    "checkbox": "",
    "select": "",
    "nullbooleanselect": "",
    "selectmultiple": "",
    "checkboxselectmultiple": "",
    "multi": "",
    "splitdatetime": base_input,
    "splithiddendatetime": "",
    "selectdate": "",
    "error_border": "border-error",
}

CUSTOM_CSS_CONTAINER = CSSContainer(custom_styles)
