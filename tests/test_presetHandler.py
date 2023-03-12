import jsonschema
import pytest
from mappingUtils import preset_handler


def test_loadJson_is_file_false():
    ph = preset_handler.PresetHandler()
    with pytest.raises(FileNotFoundError):
        ph.load_json('tests/newPresets.json')


def test_loadJson_is_file_true():
    ph = preset_handler.PresetHandler()
    assert ph.load_json('tests/presets.json') == None
    # assert p_h.load_json('newPresets.json') == "File provided does not exist. Please create new presets.json with create_presets or check file given is correct"


def test_loadJson_contains_good_json():
    ph = preset_handler.PresetHandler()
    assert ph.load_json('tests/presets.json') == None


def test_loadJson_contains_bad_json():
    ph = preset_handler.PresetHandler()
    with pytest.raises(Exception):
        ph.load_json('tests/bad.json')


def test_loadJson_presets_are_presets():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')


def test_loadJson_presets_are_not_presets():
    ph = preset_handler.PresetHandler()
    with pytest.raises(jsonschema.exceptions.ValidationError):
        ph.load_json('tests/badFormedPresets.json')


def test_getpreset_names_contains_presets():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    assert ph.get_preset_names() == ['TestingPreset', 'TestingPreset2']


def test_getpreset_names_contains_None():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/empty_presets.json')
    assert ph.get_preset_names() == []


def test_getPeople_contains_people():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    assert ph.get_people('TestingPreset') == ["Luna", "James"]


def test_getPeople_contains_None():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/empty_people_presets.json')
    assert ph.get_people('TestingPreset') == []


def test_getPeople_does_not_contain_preset():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/empty_presets.json')
    assert ph.get_people('TestingPreset') is None


def test_editPreset_does_contain_original_preset():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    assert ph.edit_preset('TestingPreset', {"preset_name": "edited_preset", "people": ["Luna", "Jack"]}) == {
        'preset_name': 'edited_preset', 'people': ['Luna', 'Jack']}


def test_editPreset_does_not_contain_original_preset():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    with pytest.raises(Exception):
        ph.edit_preset('notPreset', {"preset_name": "edited_preset", "people": ["Luna", "Jack"]})


def test_editPreset_new_preset_is_preset():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    assert ph.edit_preset('TestingPreset', {"preset_name": "edited_preset", "people": ["Luna", "Jack"]}) == {
        'preset_name': 'edited_preset', 'people': ['Luna', 'Jack']}


def test_editPreset_new_preset_is_not_preset():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    with pytest.raises(jsonschema.exceptions.ValidationError):
        assert ph.edit_preset('TestingPreset', {"preset_name": "TestingPreset", "people": 'COWS'})


def test_removePreset_preset_removed():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    assert ph.remove_preset('TestingPreset') == True

def test_removePreset_preset_does_not_exist():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    with pytest.raises(Exception):
        ph.remove_preset('notPreset')

def test_newPreset_preset_added():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    assert ph.new_preset({"preset_name": "TestingPreset", "people":["Luna", "James"]}) is None

def test_newPreset_invalid_preset():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    with pytest.raises(jsonschema.exceptions.ValidationError):
        ph.new_preset({"preset_name": "TestingPreset", "people": 'COWS'})

def test_savePresets():
    ph = preset_handler.PresetHandler()
    ph.load_json('tests/presets.json')
    assert ph.save_presets() is None

def test_createPresets_file_exists():
    ph = preset_handler.PresetHandler()
    assert ph.create_presets('tests/presets.json') == "File already exists"

def test_createPresets_file_does_not_exist():
    ph = preset_handler.PresetHandler()
    assert ph.create_presets('tests/newpresets.json') is None