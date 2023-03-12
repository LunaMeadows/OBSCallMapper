"""
Preset Handler handles presets for the OBS Call Mapper program.
"""
import json
from os import path
from typing import List, Any

import jsonschema


class PresetHandler():
    """
    The class to handle presets.

    Methods
    --------
    load_json(json_file)
        Loads provided json file

    get_preset_names()
        Returns preset names

    get_people(preset_name)
        Gets people from provided preset name

    edit_preset(original_preset_name, edited_preset)
        Edits provided preset to edited preset

    remove_preset(preset_name)
        Removed preset

    new_preset(preset)
        Adds preset

    save_presets()
        Saves presets to preeset file

    create_presets(new_presets_file)
        Creates new presets file
    """

    def __init__(self):
        self.schema = {'$schema': 'http://json-schema.org/draft-04/schema#', 'type': 'object',
                       'properties': {'preset_name': {'type': 'string'},
                                      'people': {'type': 'array', 'items': {'type': 'string'}}},
                       'required': ['preset_name', 'people']}
        self.json_file = None
        self.presets = None

    def load_json(self, json_file):
        """
        Will load a provided json file and grab the presets. Will also validate the presets to make sure they are correctly formatted.
        :param json_file: File contains presets in json format
        :return: None
        """
        try:
            self.json_file = open(json_file, 'r', encoding='UTF-8')
            try:
                self.presets = json.loads(self.json_file.read())["Presets"]
                for preset in self.presets:
                    jsonschema.validate(instance=preset, schema=self.schema)
            except json.decoder.JSONDecodeError as exception:
                raise exception
            except jsonschema.exceptions.ValidationError as exception:
                raise exception
        except FileNotFoundError as exception:
            raise exception

    def get_preset_names(self):
        """
        Gets preset names from preset file
        :return: preset_list as list
        """
        preset_list: List[Any] = []
        for preset in self.presets:
            preset_list.append(preset["preset_name"])
        return preset_list

    def get_people(self, preset_name):
        """
        Gets people from a provided preset
        :param preset_name: Name of preset to get people from
        :return: people_list as list
        """
        for preset in self.presets:
            if preset["preset_name"] == preset_name:
                return preset["people"]

    def edit_preset(self, original_preset_name, edited_preset):
        """
        Edits a preset. Finds the original preset to edit and sets it to the edited preset
        :type original_preset_name:
        :param original_preset_name: Name of the original preset
        :param edited_preset: Edited preset following the json schema
        :return: Returns updated preset
        """
        try:
            jsonschema.validate(instance=edited_preset, schema=self.schema)
            for i, preset in enumerate(self.presets):
                if preset['preset_name'] == original_preset_name:
                    self.presets[i] = edited_preset
                    return self.presets[i]
            raise Exception("Provided preset does not exist in file")
        except jsonschema.exceptions.ValidationError as exception:
            raise exception

    def remove_preset(self, preset_name):
        """
        Removed provided preset
        :param preset_name: Name of preset to remove
        :return: Returns True if preset was removed
        """
        for i, preset in enumerate(self.presets):
            if preset['preset_name'] == preset_name:
                print(preset['preset_name'])
                del self.presets[i]
                return True
        raise Exception("Provided preset does not exist in file")

    def new_preset(self, preset):
        """
        Addes new preset to presets
        :param preset: Preset that matches json schema
        :return:
        """
        try:
            jsonschema.validate(instance=preset, schema=self.schema)
            self.presets.append(preset)
        except jsonschema.exceptions.ValidationError as exception:
            raise exception

    def save_presets(self):
        """
        Saves presets to presets.json and then reloads the file
        :return:
        """
        self.json_file.close()
        json_file = open(self.json_file.name, 'w', encoding='UTF-8')
        json_file.write(str('{"Presets":' + str(self.presets) + '}').replace("'", '"'))
        json_file.close()
        self.json_file = open(self.json_file.name, 'r', encoding='UTF-8')

    def create_presets(self, new_presets_file):
        """
        Creates an empty presets file
        :param new_presets_file: Name of new presets file
        :return:
        """
        if path.isfile(new_presets_file):
            return "File already exists"
        json_file = open(new_presets_file, 'w', encoding='UTF-8')
        json_file.write(str('{"Presets":[]}'))
        json_file.close()
        self.presets = []
        self.json_file = open(new_presets_file, 'r', encoding='UTF-8')
