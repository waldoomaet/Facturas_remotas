import json

fileStruct = {
    "token": "0",
    "Allowed_Users": [],
    "Document_Folder_Path": "",
    "Image_Folder_Path": "",
    "Processed_Image_Folder_Path": "",
    "Generated_PDF_Path": "",
    "File_Types": {
        "Type_1": "",
        "Type_2": "",
        "Type_n": ""
    },
    "Printer_name": ""
}

jsonData = json.dumps(fileStruct, indent=4)
with open("configFile.json", 'w') as file:
    file.write(jsonData)