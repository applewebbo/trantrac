from crispy_tailwind.tailwind import CSSContainer

# Custom CSS classes with dark mode support using DaisyUI
base_input = (
    "bg-base-200 dark:bg-base-300 focus:outline-none border border-base-300 rounded-lg py-2 px-4 "
    "block w-full appearance-none leading-normal text-base-content"
)

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
    "textarea": base_input,
    "date": base_input,
    "datetime": base_input,
    "time": base_input,
    "checkbox": "",
    "select": "",
    "nullbooleanselect": "",
    "selectmultiple": "",
    "checkboxselectmultiple": "",
    "multi": "",
    "splitdatetime": (
        "text-base-content bg-base-200 dark:bg-base-300 focus:outline border border-base-300 "
        "leading-normal px-4 appearance-none rounded-lg py-2 focus:outline-none mr-2"
    ),
    "splithiddendatetime": "",
    "selectdate": "",
    "error_border": "border-red-500",
}

CUSTOM_CSS_CONTAINER = CSSContainer(custom_styles)
