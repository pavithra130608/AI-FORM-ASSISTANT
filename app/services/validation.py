def validate(field, value):
    if field.get("required") and not value:
        return False, "This field is required"

    if field["type"] == "number":
        if not value.isdigit():
            return False, "Please enter a valid number"

    return True, ""
