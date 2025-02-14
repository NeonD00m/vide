import requests

# Formatting settings
enable_formatting = True
new_line = ";"
next_entry = ";"
new_line_not_required = ""
indent = ""
space = ""

if enable_formatting:
    new_line = "\n"
    new_line_not_required = "\n"
    space = " "
    next_entry = ",\n"
    indent = "\t"

# Set to False if you want to output only the desired classes
compile_for_all_classes = False
desired_classes = [
    "CanvasGroup",
    "Frame",
    "ImageButton",
    "TextButton",
    "ImageLabel",
    "TextLabel",
    "ScrollingFrame",
    "TextBox",
    "VideoFrame",
    "ViewportFrame",
    "BillboardGui",
    "ScreenGui",
    "AdGui",
    "SurfaceGui",
    "SelectionBox",
    "BoxHandleAdornment",
    "ConeHandleAdornment",
    "CylinderHandleAdornment",
    "ImageHandleAdornment",
    "LineHandleAdornment",
    "SphereHandleAdornment",
    "WireframeHandleAdornment",
    "ParabolaAdornment",
    "SelectionSphere",
    "ArcHandles",
    "Handles",
    "SurfaceSelection",
    "Path2D",
    "UIAspectRatioConstraint",
    "UISizeConstraint",
    "UITextSizeConstraint",
    "UICorner",
    "UIDragDetector",
    "UIFlexItem",
    "UIGradient",
    "UIListLayout",
    "UIGridLayout",
    "UIPageLayout",
    "UITableLayout",
    "UIPadding",
    "UIScale",
    "UIStroke",

    "WorldModel",
    "Camera",
    "Part",
    "Model",
    "MeshPart",
    "Highlight",
    "Folder",
]

# Prepend some type definitions
lines_before = [
    "type p<T> =" + space + "T?|()->T",
    "type e<T=()->()> =" + space + "T?",
    "type a={priority:" + space + "number," + space + "callback:" + space + "(Instance)" + space + "->" + space + "()}",
    "type recursive<T> =T|{read recursive<T>}|()->recursive<T>",
    "type c<T> =a|T|recursive<Instance>",
    "type Dictionary = {read [string]: any}",
    "type Array = {read any}"
]

lines_after = [
    "return{}"
]

lines = []

# API dump links
API_DUMP_LINK = "https://raw.githubusercontent.com/MaximumADHD/Roblox-Client-Tracker/roblox/API-Dump.json"
CORRECTIONS_LINK = "https://raw.githubusercontent.com/NightrainsRbx/RobloxLsp/master/server/api/Corrections.json"

api_dump_request = requests.get(API_DUMP_LINK)
corrections_dump_request = requests.get(CORRECTIONS_LINK)

api_dump = api_dump_request.json()
corrections_dump = corrections_dump_request.json()

# Mapping for type aliases (no snake_case conversion here)
aliases = {
    "int64": "number",
    "int": "number",
    "float": "number",
    "double": "number",
    "bool": "boolean",
    "ContentId": "string",
    "string": "string" + space + "|" + space + "number",
    "OptionalCoordinateFrame": "CFrame?",
    "BinaryString": "string",
}

map_corrections = {}
map_roblox_classes = {}

for roblox_class in api_dump["Classes"]:
    map_roblox_classes[roblox_class["Name"]] = roblox_class

for correction_class in corrections_dump["Classes"]:
    map_corrections[correction_class["Name"]] = correction_class

def get_prop_type(value_type):
    """
    Returns the property type string exactly as provided,
    without any snake_case conversion.
    """
    prop = ""
    category = value_type["Category"]
    if category == "Enum":
        prop = "Enum." + value_type["Name"]
    elif category == "Class":
        prop = value_type["Name"] + "?"
    elif category == "Primitive":
        value_name = value_type["Name"]
        prop = aliases.get(value_name) or value_name
    elif category == "DataType":
        value_name = value_type["Name"]
        prop = aliases.get(value_name) or value_name
    elif category == "Group":
        prop = value_type["Name"]
    return prop

def append_class(roblox_class):
    # Get corrections (if any) for the class
    correction_class = map_corrections.get(roblox_class["Name"]) or {"Members": []}
    correction_members_map = {member["Name"]: member for member in correction_class["Members"]}
    
    for member in roblox_class["Members"]:
        # Skip members that are read-only, deprecated, or not scriptable
        if member.get("Tags") and ("ReadOnly" in member["Tags"] or "Deprecated" in member["Tags"] or "NotScriptable" in member["Tags"]):
            continue
        
        # Process Properties
        if member["MemberType"] == "Property":
            if member["Security"]["Write"] != "None":
                continue
            if "Deprecated" in member:
                continue
            # Use the original member name without converting case.
            lines.append(indent + member["Name"] + ":" + space + "p<" + get_prop_type(member["ValueType"]) + ">" + next_entry)
        
        # Process Events
        elif member["MemberType"] == "Event":
            if member["Security"] != "None":
                continue

            correction_member = correction_members_map.get(member["Name"]) or {"Parameters": []}
            correction_parameters_map = {parameter["Name"]: parameter for parameter in correction_member["Parameters"]}
            line = indent + member["Name"] + ":" + space + "e<("
            is_first = True
            for parameter in member["Parameters"]:
                if not is_first:
                    line += ","
                is_first = False

                correction_parameter = correction_parameters_map.get(parameter["Name"])
                if correction_parameter is None:
                    value = get_prop_type(parameter["Type"])
                    # If the type is "Tuple", use a variadic any type
                    if value == "Tuple":
                        line += "...any"
                    else:
                        line += parameter["Name"] + ":" + value
                else:
                    line += parameter["Name"] + ":"
                    name = correction_parameter["Type"].get("Name")
                    generic = correction_parameter["Type"].get("Generic")
                    if name is not None:
                        line += name
                    elif generic is not None:
                        line += "{" + generic + "}"
            line += ")" + space + "->" + space + "()>"+next_entry
            lines.append(line)
    
    # If the class has a superclass, append its members as well
    if roblox_class["Superclass"] != "<<<ROOT>>>":
        append_class(map_roblox_classes[roblox_class["Superclass"]])

# Determine which classes to process
if compile_for_all_classes:
    desired_classes = map_roblox_classes

# Process each desired class
for class_name in desired_classes:
    roblox_class = map_roblox_classes[class_name]
    if 'Tags' in roblox_class and "NotCreatable" in roblox_class['Tags']:
        continue
    name = roblox_class['Name']
    lines.append("export type v" + name + space + "=" + space + "{" + new_line_not_required)
    append_class(roblox_class)
    lines.append(indent + "[number]:" + space + "c<v" + name + ">" + new_line)
    lines.append(new_line_not_required + "}" + new_line)

# Write the types file
with open("../src/roblox_types.luau", "wt") as file:
    single_line = new_line.join(lines_before) + new_line + ''.join(lines) + new_line.join(lines_after)
    file.write(single_line)

# Modify create.luau
with open("../src/create.luau", "r") as reader:
    lines_create = reader.readlines()

line_create_at = 0
for i, line in enumerate(lines_create):
    if "return (create" in line:
        line_create_at = i + 1
        break

with open("../src/create.luau", "w") as writer:
    # Write lines up to the insertion point
    writer.writelines(lines_create[:line_create_at])
    iterate_through = desired_classes if not compile_for_all_classes else map_roblox_classes
    first = True
    for name in iterate_through:
        roblox_class = map_roblox_classes[name]
        if "Tags" in roblox_class and "NotCreatable" in roblox_class["Tags"]:
            continue
        if not first:
            writer.write("&")
        else:
            first = False
        writer.write(f'\t( (class: "{name}") -> (r.v{name}) -> {name} )\n')

# Modify init.luau
with open("../src/init.luau", "r") as reader:
    init_lines = reader.readlines()

line_create_at = 0
for i, line in enumerate(init_lines):
    if "-- TYPES HERE" in line:
        line_create_at = i + 1
        break

with open("../src/init.luau", "w") as writer:
    writer.writelines(init_lines[:line_create_at])
    lines_after = init_lines[line_create_at+1:]
    iterate_through = desired_classes if not compile_for_all_classes else map_roblox_classes
    first = True
    for name in iterate_through:
        roblox_class = map_roblox_classes[name]
        if "Tags" in roblox_class and "NotCreatable" in roblox_class["Tags"]:
            continue
        writer.write(f'export type v{name} = roblox_types.v{name}\n')
    writer.writelines(lines_after)
