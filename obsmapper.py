"""
Creates an interface for users to interact with and streamline the cam mapping process.
"""
import json  # Used to read in the source export from OBS to try and find a source matching the name of the preset
import os  # Used to create proper paths for files and folders
import platform  # Used to find out the users system to create proper scenes in OBS
import webbrowser  # Used to open folders
from typing import Dict, List, Union  # Used for type hinting

import toga  # Used to create the user interface
from toga import MainWindow
from toga.style.pack import COLUMN, Pack, ROW, CENTER  # Used for styling widgets
from toga.command import Group  # Used to add items to default command groups

from mappingUtils import image_processing, preset_handler, obs_plugin_server


# noinspection PyAttributeOutsideInit
# pylint: disable=attribute-defined-outside-init
# noinspection PyTypeChecker
class ObsMapper(toga.App):
    """
    A class of toga.App to create the main user interface for the application
    Attributes
    ----------
    main_window
        Main window for toga application
    data_path
        File path for data to be stored in
    cam_images
        List of camera images to be displayed in application
    cams
        Dictionary of all camera images.
        Key == path to camera screenshot
        Value == list containing rect of camera location in window, name belonging to person who owns camera
    image_proc
        Image processing class. See module image_processing for more information
    preset_handler
        Preset handler class. See module preset_handler for more information
    obs_server
        Obs plugin server class. See module obs_plugin_server for more information
    new_preset
        Boolean to check if a preset is new or being edited
    obs_scenes
        OBS scenes from OBS export json file
    """
    main_window: MainWindow
    data_path: str
    cam_images: List[str]
    cams: Dict[str, List[Union[list, str]]]
    new_preset: False
    image_proc: image_processing.ImageProcessing
    preset_handler: preset_handler.PresetHandler
    obs_server: obs_plugin_server.Server
    obs_scenes: dict

    # pylint: disable=too-many-instance-attributes
    def startup(self):
        """
        Creates user interface and initializes all needed variables
        """
        self.main_window = toga.MainWindow(title="OBS Call Mapper", size=(640, 381), resizeable=False)
        self.data_path = os.path.join(str(self.paths.data), 'OBS Call Mapper')
        self.cam_images = []
        self.cams = {}
        self.new_preset = False
        self.image_proc = image_processing.ImageProcessing(self.data_path, False)
        self.preset_handler = preset_handler.PresetHandler()
        self.obs_server = obs_plugin_server.Server()
        self.obs_server.start_server()
        self.obs_scenes = self.get_obs_scene_export()
        # Tries to load presets.json and creates a new preset if it does not already exist
        try:
            self.preset_handler.load_json(os.path.join(self.data_path, "presets.json"))
        except FileNotFoundError:
            self.preset_handler.create_presets(os.path.join(self.data_path, "presets.json"))

        # Creates main window for user interface
        left_content = toga.Box(id='button_pane', style=Pack(direction=COLUMN, alignment=CENTER))
        new_preset_button = toga.Button(id='new_preset', text='New Preset', style=Pack(width=200, height=34),
                                        on_press=self.edit_preset_window)
        left_content.add(
            toga.Selection(id='preset_selection', items=self.preset_handler.get_preset_names(),
                           style=Pack(width=200, height=34)),
            toga.Button(id='load_preset', text='Load Preset', style=Pack(width=200, height=34),
                        on_press=self.load_preset),
            toga.Button(id='edit_preset', text='Edit Preset', style=Pack(width=200, height=34),
                        on_press=self.edit_preset_window),
            toga.Button(id='delete_preset', text='Delete Preset', style=Pack(width=200, height=34),
                        on_press=self.delete_preset),
            new_preset_button,
            toga.Box(id='flex_box_1', style=Pack(direction=COLUMN, flex=1)),
            toga.Button(id='reload_windows', text='Reload Windows', style=Pack(width=200, height=34),
                        on_press=self.reload_windows),
            toga.Button(id='map_cameras', text='Map Cameras', style=Pack(width=200, height=34),
                        on_press=self.map_cameras),
        )
        window_selection = toga.Selection(id='window_selection', items=list(self.image_proc.get_windows().keys()),
                                          style=Pack(width=280, height=34))
        window_selection.items = window_selection.items + ["Select Screenshot"]
        right_content = toga.Box(id='option_pane', style=Pack(direction=COLUMN, alignment=CENTER))
        right_content.add(
            toga.Box(id='window_selection_box', style=Pack(direction=ROW, width=420, alignment=CENTER), children=[
                window_selection,
                toga.Button(id='select_window', text='Select Window', style=Pack(height=34), on_press=self.get_cameras)
            ]),
            toga.Box(id='camera_control_buttons', style=Pack(direction=ROW, width=420), children=[
                toga.Button(id='previous', text='Previous', style=Pack(width=100, height=34), on_press=self.prev_image),
                toga.Label(id='person_label', text='',
                           style=Pack(width=200, height=34, padding_top=10, text_align=CENTER)),
                toga.Button(id='next', text='Next', style=Pack(width=100, height=34), on_press=self.next_image)
            ]),
            toga.Box(id='image_wrapper', style=Pack(direction=ROW, width=420, height=232), children=[
                toga.ImageView(id='image_viewer'),
            ]),
            toga.Box(id='flex_box_2', style=Pack(direction=COLUMN, flex=1)),
            toga.Box(id='cam_selection_wrapper', style=Pack(direction=ROW, width=420, height=100), children=[
                toga.Selection('cam_selection', items=[], style=Pack(width=320, height=34)),
                toga.Button(id='bind_camera', text='Bind', style=Pack(width=100, height=34), on_press=self.bind_camera)
            ])
        )
        # Creates a command to allow user to change the provided OBS exported json
        obs_sources_command = toga.Command(
            action=lambda _: self.main_window.open_file_dialog('Select OBS Sources exported json',
                                                               on_result=self.get_obs_scene_export,
                                                               file_types=['json']),
            text='Select OBS Source Export',
            group=Group.APP
        )
        debug_enable = toga.Command(
            action=self.toggle_debugging,
            text='Toggle debugging',
            group=Group.HELP
        )
        open_data_folder = toga.Command(
            action=self.open_data_folder,
            text='Open data folder',
            group=Group.APP
        )
        self.commands.add(obs_sources_command, debug_enable, open_data_folder)
        # Checks if the platform is a Windows machine and if so sets the split container to the content,
        # if it is not it will create scroll containers and then set it into the split container
        if platform.system() == 'Windows':
            split = toga.SplitContainer()
            split.content = [(left_content, 0.1), (right_content, 0.2)]
        else:
            left_container = toga.ScrollContainer(horizontal=False)
            left_container.content = left_content
            right_container = toga.ScrollContainer(horizontal=False)
            right_container.content = right_content
            split = toga.SplitContainer()
            split.content = [(left_container, 0.1), (right_container, 0.2)]

        # Sets main window to the split container and then shows it
        self.main_window.content = split
        self.main_window.show()
        # Checks to see if a preset already exists and if none exist it will open a window to create a new preset
        if len(self.preset_handler.get_preset_names()) == 0:
            self.edit_preset_window(new_preset_button)

    def toggle_debugging(self, widget):
        """
        Toggles debugging
        """
        self.image_proc.toggle_debugging()

    def open_data_folder(self, widget):
        """
        Opens data folder for application
        """
        webbrowser.open(os.path.realpath(self.data_path))

    def get_obs_scene_export(self, _=None, file_path: str =""):
        """
        Allows user to select scene export json file from OBS
        :param file_path: Selected path to the obs exported json file.
        :return: Json dict or None
        """
        # Sets scene_file to the locally stored json scenes file.
        scene_file = os.path.join(self.data_path, 'obs_scenes.json')
        try:
            # Try to open and read the scene_file
            scene_file = open(scene_file, 'r', encoding='UTF-8')
            return json.load(scene_file)
        except FileNotFoundError:
            # If file does not exist and a file is provided, create the scene file and read in the provided file
            if len(file_path) > 0:
                scene_file_create = open(scene_file, 'w', encoding='UTF-8')
                scene_file_create.write(open(file_path[1], 'r', encoding='UTF-8').read())
                scene_file_create.close()
                scene_file = open(scene_file, 'r', encoding='UTF-8')
                return json.load(scene_file)
            return

    def prev_image(self, widget):
        """
        Sets previous image from cam_images list as the image for the image viewer.
        If already on first image it will wrap around to the last image.
        """
        image_viewer = widget.window.widgets.get('image_viewer')
        person_label = widget.window.widgets.get('person_label')
        # Gets the index of the current image
        cur_image = self.cam_images.index(str(image_viewer.image.path))
        # If the current image is the first image in the list, wrap around to the last image. Else get previous image
        if cur_image - 1 < 0:
            image_viewer.image = toga.Image(self.cam_images[-1])
            person_label.text = self.cams[str(image_viewer.image.path)][1]
        else:
            image_viewer.image = toga.Image(self.cam_images[cur_image - 1])
            person_label.text = self.cams[str(image_viewer.image.path)][1]

    def next_image(self, widget):
        """
        Sets next image from cam_images list as the image for the image viewer.
        If already on the last image it will wrap to the first image.
        """
        image_viewer = widget.window.widgets.get('image_viewer')
        person_label = widget.window.widgets.get('person_label')
        # Gets the index of the current image
        cur_image = self.cam_images.index(str(image_viewer.image.path))
        # If the current image is the last image in the list, wrap around to the first image. Else get next image
        if cur_image + 1 == len(self.cam_images):
            image_viewer.image = toga.Image(self.cam_images[0])
            person_label.text = self.cams[str(image_viewer.image.path)][1]
        else:
            image_viewer.image = toga.Image(self.cam_images[cur_image + 1])
            person_label.text = self.cams[str(image_viewer.image.path)][1]

    def get_cameras(self, widget):
        # pylint: disable=attribute-defined-outside-init
        """
        Gets cameras from the selected window or provided screenshot
        """

        def get_from_screenshot(_, screenshot):
            """
            Gets cameras from a provided screenshot
            :param _: Throw away parameter
            :param screenshot: Path to the selected screenshot
            """
            # Gets camera information from image_processing and sets the image_viewer to the first camera
            self.cams = self.image_proc.get_camera_pos(None, screenshot=screenshot)
            self.cam_images = list(self.cams.keys())
            image_viewer = widget.window.widgets.get('image_viewer')
            image_viewer.image = toga.Image(self.cam_images[0])
            # Checks to see if obs_scenes is set and if not makes the user select a file to set it
            if self.obs_scenes is None:
                self.main_window.open_file_dialog('Select OBS Sources exported json',
                                                  on_result=self.get_obs_scene_export, file_types=['json'])

        window_selection = widget.window.widgets.get('window_selection')
        selected_window = window_selection.value
        # If Select Screenshot is selected then make user select a screenshot
        if selected_window == 'Select Screenshot':
            self.main_window.open_file_dialog('Select call screenshot', on_result=get_from_screenshot,
                                              file_types=['jpg', 'jpeg', 'png'])
        else:
            # If a window is selected then get the window title and set cams and image_viewer
            window_dict = self.image_proc.get_windows()
            for k in window_dict.keys():
                if k.startswith(selected_window):
                    self.cams = self.image_proc.get_camera_pos(k)
                    self.cam_images = list(self.cams.keys())
                    image_viewer = widget.window.widgets.get('image_viewer')
                    image_viewer.image = toga.Image(self.cam_images[0])
                    return

    def bind_camera(self, widget):
        """
        Sets camera to the selected person
        """
        image_viewer = widget.window.widgets.get('image_viewer')
        cam_selection = widget.window.widgets.get('cam_selection')
        person_label = widget.window.widgets.get('person_label')
        # If no person is selected or no preset is loaded, return
        if cam_selection.value is None:
            return
        # Sets the name of the current camera to the person and sets the label so the user knows who it belongs to
        self.cams[str(image_viewer.image.path)][1] = cam_selection.value
        person_label.text = cam_selection.value

    def load_preset(self, widget):
        """
        Loads selected preset
        """
        cam_selection = widget.window.widgets.get('cam_selection')
        preset_selection = widget.window.widgets.get('preset_selection')
        person_label = widget.window.widgets.get('person_label')
        # Loads selected preset and resets cam names to blank
        cam_selection.items = self.preset_handler.get_people(preset_selection.value)
        for cam in self.cams.values():
            cam[1] = ''
        person_label.text = ''

    def delete_preset(self, widget):
        """
        Deletes selected preset
        """
        preset_selection = widget.window.widgets.get('preset_selection')
        cam_selection = widget.window.widgets.get('cam_selection')
        # Removes the current preset and deletes it from the preset handler and saves it.
        self.preset_handler.remove_preset(preset_selection.value)
        self.preset_handler.save_presets()
        preset_selection.items = self.preset_handler.get_preset_names()
        cam_selection.items = []

    def reload_windows(self, widget):
        """
        Reloads windows for window selection
        """
        window_selection = widget.window.widgets.get('window_selection')
        window_selection.items = list(self.image_proc.get_windows().keys()) + ['Select Screenshot']

    def edit_preset_window(self, widget):
        # pylint: disable=attribute-defined-outside-init, too-many-branches
        """
        Window for editing presets
        """

        def hide_window(widget):
            """
            Hides window
            """
            preset_selection = widget.app.main_window.widgets.get('preset_selection')
            save_edit = None
            edit_box = None
            for item in widget.content.children:
                if item.id == 'save_edit':
                    save_edit = item
                if item.id == 'edit_box':
                    edit_box = item
            preset_selection.enabled = True
            children = edit_box.children
            for i in reversed(range(len(children))):
                edit_box.remove(children[i])
            if save_edit is None:
                widget.content.add(
                    toga.Button(id='save_edit', text='Save edit', style=Pack(width=420), on_press=self.save_edit))
            widget.hide()

        if widget.id == 'new_preset':
            self.new_preset = True
        else:
            self.new_preset = False
        for windows in widget.app.windows.elements:
            if windows.title == 'Edit Profiles Window':
                if not windows.visible:
                    preset_selection = widget.window.widgets.get('preset_selection')
                    preset_name = windows.widgets.get('preset_name')
                    people_table = windows.widgets.get('people_table')
                    preset_selection.enabled = False
                    if not self.new_preset:
                        if preset_selection.value is None or preset_selection.value == "":
                            return
                        preset_name.value = preset_selection.value
                        people_table.data.clear()
                        for person in self.preset_handler.get_people(preset_selection.value):
                            people_table.data.append(person)
                    else:
                        preset_name.value = ''
                        people_table.data.clear()

                    windows.show()
                return
        people_table = toga.Table(id='people_table', headings=['People'], style=Pack(height=400, width=420))
        preset_selection = widget.window.widgets.get('preset_selection')
        preset_selection.enabled = False
        # noinspection PyTypeChecker
        window = toga.Window(title='Edit Profiles Window', on_close=hide_window, size=(420, 464))
        widget.app.windows.add(window)
        preset_name = toga.TextInput(id='preset_name', value=preset_selection.value, placeholder='Preset name',
                                     on_change=self.text_handler(20))
        box = toga.Box(id="edit_window", style=Pack(width=420, direction=COLUMN), children=[
            preset_name,
            people_table,
            toga.Box(id='tableButtons', style=Pack(direction=ROW), children=[
                toga.Button(id='new_person', text='New Person', style=Pack(width=140), on_press=self.new_person),
                toga.Button(id='edit_person', text='Edit Person', style=Pack(width=140), on_press=self.edit_person),
                toga.Button(id='remove_person', text='Remove Person', style=Pack(width=140),
                            on_press=self.remove_person)
            ]),
            toga.Box(id='edit_box', style=Pack(direction=ROW, flex=1)),
            toga.Button(id='save_edit', text='Save edit', style=Pack(width=420), on_press=self.save_edit)
        ])
        if not self.new_preset:
            if preset_name.value == "":
                return
            for person in self.preset_handler.get_people(preset_selection.value):
                people_table.data.append(person)
        else:
            preset_name.value = ""
        window.content = box
        window.show()

    def save_edit(self, widget):
        """
        Saves preset edits
        """
        preset_name = widget.window.widgets.get('preset_name')
        # Makes sure that the preset has a name
        if len(preset_name.value) == 0:
            preset_name.focus()
        else:
            preset_selection = widget.app.main_window.widgets.get('preset_selection')
            # Loops through table and sets an array to the contents of the table
            people = []
            for person in widget.window.widgets.get('people_table').data:
                people.append(person.people)
            # If this is not a new preset then save the edits to the current preset
            if not self.new_preset:
                self.preset_handler.edit_preset(preset_selection.value,
                                                {"preset_name": preset_name.value, "people": people})
            # If this is a new preset then create a new preset
            else:
                self.preset_handler.new_preset({"preset_name": preset_name.value, "people": people})
            # Saves preset changes and closes the window. Also sets cam_selection and enables preset_selection
            self.preset_handler.save_presets()
            widget.window.hide()
            cam_selection = widget.app.main_window.widgets.get('cam_selection')
            cam_selection.items = people
            preset_selection.enabled = True
            preset_selection.items = self.preset_handler.get_preset_names()
            preset_selection.value = preset_name.value

    def remove_person(self, widget):
        """
        Removes person from preset
        """
        people_table = widget.window.widgets.get('people_table')
        people_table.data.remove(people_table.selection)

    def new_person(self, widget):
        """
        Adds new person to the preset
        """
        people_table = widget.window.widgets.get('people_table')
        save_edit = widget.window.widgets.get('save_edit')
        edit_window = widget.window.widgets.get('edit_window')
        edit_window.remove(save_edit)
        new_person = toga.TextInput(placeholder='Enter name here or leave blank', on_change=self.text_handler(20),
                                    style=Pack(width=320))
        edit_box = widget.window.widgets.get('edit_box')

        def save_change(_widget):
            """
            Saves change to table and removes edit_box widget
            """
            # Checks if the new_person text is grater than 0 and if so adds the person to the table.
            if len(new_person.value) > 0:
                people_table.data.append(new_person.value)
            # Removes edit fields and adds save_edit button
            children = edit_box.children
            for i in reversed(range(len(children))):
                edit_box.remove(children[i])
            edit_window.add(save_edit)

        # Checks if edit fields exist and if not creates then
        if len(edit_box.children) == 0:
            edit_box.add(
                new_person,
                toga.Button(id='save_change', text='Save Change', style=Pack(width=100), on_press=save_change)
            )

    def edit_person(self, widget):
        """
        Edits the selected person
        """
        people_table = widget.window.widgets.get('people_table')
        save_edit = widget.window.widgets.get('save_edit')
        edit_window = widget.window.widgets.get('edit_window')
        # Makes sure that people_table has contents

        if people_table.selection is not None:
            edit_window.remove(save_edit)
            name_changed = toga.TextInput(placeholder='Leave blank to not edit', on_change=self.text_handler(20),
                                          style=Pack(width=320))
            edit_box = widget.window.widgets.get('edit_box')

            def save_change(_widget):
                """
                Saves changes to table and removes edit_box widget
                """
                # Checks if the new_person text is grater than 0 and if so adds the person to the table.
                if len(name_changed.value) > 0:
                    # pylint: disable=protected-access
                    # noinspection PyProtectedMember
                    # Loops through all data in the table and modifies edited people. This is due to windows table not updating properly
                    people = people_table.data._data
                    people_edited = []
                    for i, person in enumerate(people):
                        if person.people == people_table.selection.people:
                            people_edited.append(name_changed.value)
                        else:
                            people_edited.append(person.people)
                    people_table.data.clear()
                    for person in people_edited:
                        people_table.data.append(person)
                    people_table.refresh()
                # Removes edit fields and adds save_edit button
                children = edit_box.children
                for i in reversed(range(len(children))):
                    edit_box.remove(children[i])
                edit_window.add(save_edit)

            # Checks if edit fields exist and if not creates then
            if len(edit_box.children) == 0:
                edit_box.add(
                    name_changed,
                    toga.Button(id='save_change', text='Save Change', style=Pack(width=100), on_press=save_change)
                )

    def text_handler(self, value):
        """
        Makes sure text stays with in limits as to not affect selection box width
        """

        def text_len_validation(widget):
            # If text length goes past the allowed limit, splice the string to set length
            if len(widget.value) > value:
                widget.value = widget.value[0:value]

        return text_len_validation

    def map_cameras(self, widget):
        """
        Maps cameras to obs
        """
        window_selection = widget.window.widgets.get('window_selection')
        # If a screenshot is selected, uses scene info to get needed exe information
        if window_selection.value == 'Select Screenshot':
            cameras = []
            # Loops through all cameras and makes needed cam json information to create a new source or edit an existing one
            for cam in self.cams.values():
                if platform.system() == 'Linux':
                    cameras.append(
                        {'camName': cam[1], "x": cam[0][0], "x1": cam[0][2], "y": int(cam[0][1]) + 40, "y1": cam[0][3]})
                else:
                    cameras.append(
                        {'camName': cam[1], "x": cam[0][0], "x1": cam[0][2], "y": int(cam[0][1]), "y1": cam[0][3]})
            # Gets scene information and sends command to OBS plugin to create a new or edit an existing scene
            scene = self.get_source_info_from_json(widget)
            settings = list(dict(scene['settings']).items())
            obs_cams_send = str({
                "arg": "crop camera",
                "os": settings[0][0],
                "exe": settings[0][1],
                "cameras": cameras,
                "id": scene['id']  #
            })
            self.obs_server.send_command(obs_cams_send)
        else:
            cameras = []
            # Loops through all cameras and makes needed cam json information to create a new source or edit an existing one
            for cam in self.cams.values():
                if platform.system() == 'Windows':
                    cameras.append(
                        {'camName': cam[1], "x": cam[0][0], "x1": cam[0][2], "y": int(cam[0][1]), "y1": cam[0][3]})
                if platform.system() == 'Linux':
                    cameras.append(
                        {'camName': cam[1], "x": cam[0][0], "x1": cam[0][2], "y": int(cam[0][1]) + 40, "y1": cam[0][3]})
            # Sends information to OBS plugin to create or edit an existing scene
            obs_cams_send = str({
                "arg": "crop camera",
                "os": platform.system(),
                "exe": self.image_proc.get_exe_name(window_selection.value),
                "cameras": cameras,
                "id": ''
            })
            self.obs_server.send_command(obs_cams_send)

    def get_source_info_from_json(self, widget):
        """
        Gets the source info needed to create a caputre source in OBS
        """
        preset_selection = widget.window.widgets.get('preset_selection')
        # Looks through all provided sources for a scene that has the same name as the preset name
        for source in self.obs_scenes['sources']:
            preset_name = str('OBSMapper-' + str(preset_selection.value))
            if source['name'] == preset_name:
                return source
        # OBSMapper-{PresetName} is format that is looked for


if __name__ == "__main__":
    app = ObsMapper("OBS Call Mapper", "org.lunarsoftware.obscallmapper", author='Luna', version=1)
    app.main_loop()
