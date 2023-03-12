"""ObsMapper
This is the main module for the OBSCamMapper application.

It will create and run the users side of the application and comunicate with the obs plugin
"""
import os
import platform

import toga
from toga.style.pack import COLUMN, Pack, ROW, CENTER, HIDDEN
from mappingUtils import image_processing, preset_handler, obs_plugin_server


# noinspection PyAttributeOutsideInit
class ObsMapper(toga.App):
    """
        OBSMapper User Interface
    """

    def startup(self):
        # pylint: disable=attribute-defined-outside-init
        """
        Main window
        """
        self.main_window = toga.MainWindow("OBS Call Mapper")
        self.data_path = os.path.join(str(app.paths.data), 'OBSCallMapper')
        self.cam_images = []
        self.cams = {}
        self.image_proc = image_processing.ImageProcessing(self.data_path, False)
        self.p_h = preset_handler.PresetHandler()
        self.obs_server = obs_plugin_server.Server()
        self.obs_server.start_server()
        self.main_window.size = (640, 381)
        self.main_window.resizeable = False
        self.new_preset = False
        if platform.system() == 'Windows':
            self.buttonHeight = 26
        if platform.system() == 'Linux':
            self.buttonHeight = 36
        try:
            self.p_h.load_json(os.path.join(self.data_path, "presets.json"))
        except FileNotFoundError:
            self.p_h.create_presets(os.path.join(self.data_path, "presets.json"))

        left_content = toga.Box(id='button_pane', style=Pack(direction=COLUMN, alignment=CENTER))
        left_content.add(
            toga.Selection(id='preset_selection', items=self.p_h.get_preset_names(), style=Pack(width=200)),
            toga.Button(id='load_preset', text='Load Preset', style=Pack(width=200), on_press=self.load_preset),
            toga.Button(id='edit_preset', text='Edit Preset', style=Pack(width=200), on_press=self.edit_profile_window),
            toga.Button(id='delete_preset', text='Delete Preset', style=Pack(width=200), on_press=self.delete_preset),
            toga.Button(id='new_preset', text='New Preset', style=Pack(width=200), on_press=self.edit_profile_window),
            toga.Box(id='flex_box_1', style=Pack(direction=COLUMN, flex=1)),
            toga.Button(id='map_cameras', text='Map Cameras', style=Pack(width=200), on_press=self.map_cameras),
        )

        right_content = toga.Box(id='option_pane', style=Pack(direction=COLUMN, alignment=CENTER))
        right_content.add(
            toga.Box(id='window_selection_box', style=Pack(direction=ROW, width=420, alignment=CENTER), children=[
                toga.Selection(id='window_selection', items=list(self.image_proc.get_windows().keys()),
                               style=Pack(width=280)),
                toga.Button(id='select_window', text='Select Window', on_press=self.get_cameras)
            ]),
            toga.Box(id='camera_control_buttons', style=Pack(direction=ROW, width=420), children=[
                toga.Button(id='previous', text='Previous', style=Pack(width=100), on_press=self.prev_image),
                toga.Label(id='person_label', text='', style=Pack(width=200, padding_top=10, text_align=CENTER)),
                toga.Button(id='next', text='Next', style=Pack(width=100), on_press=self.next_image)
            ]),
            toga.Box(id='image_wrapper', style=Pack(direction=ROW, width=420, height=232), children=[
                toga.ImageView(id='image_viewer'),
            ]),
            toga.Box(id='flex_box_2', style=Pack(direction=COLUMN, flex=1)),
            toga.Box(id='cam_selection_wrapper', style=Pack(direction=ROW, width=420, height=100), children=[
                toga.Selection('cam_selection', items=[], style=Pack(width=320)),
                toga.Button(id='bind_camera', text='Bind', style=Pack(width=100), on_press=self.bind_camera)
            ])
        )
        if platform.system() == 'Windows':
            split = toga.SplitContainer()
            split.content = [(left_content, 0.1), (right_content, 0.2)]
        if platform.system() == 'Linux':
            left_container = toga.ScrollContainer(horizontal=False)
            left_container.content = left_content
            right_container = toga.ScrollContainer(horizontal=False)
            right_container.content = right_content
            split = toga.SplitContainer()
            split.content = [(left_container, 0.1), (right_container, 0.2)]

        self.main_window.content = split
        self.main_window.show()

    def prev_image(self, widget):
        """
        Sets previous image from cam_images list as the image for the image viewer.
        If already on first image it will wrap around to the last image.
        """
        image_viewer = widget.window.widgets.get('image_viewer')
        person_label = widget.window.widgets.get('person_label')
        cur_image = self.cam_images.index(str(image_viewer.image.path))
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
        cur_image = self.cam_images.index(str(image_viewer.image.path))
        if cur_image + 1 == len(self.cam_images):
            image_viewer.image = toga.Image(self.cam_images[0])
            person_label.text = self.cams[str(image_viewer.image.path)][1]
        else:
            image_viewer.image = toga.Image(self.cam_images[cur_image + 1])
            person_label.text = self.cams[str(image_viewer.image.path)][1]

    def get_cameras(self, widget):
        # pylint: disable=attribute-defined-outside-init
        """
        Gets cameras from the selected window
        """
        window_selection = widget.window.widgets.get('window_selection')
        selected_window = window_selection.value
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
        :param widget:
        :return:
        """
        image_viewer = widget.window.widgets.get('image_viewer')
        cam_selection = widget.window.widgets.get('cam_selection')
        person_label = widget.window.widgets.get('person_label')
        if cam_selection.value is None:
            return
        self.cams[str(image_viewer.image.path)][1] = cam_selection.value
        person_label.text = cam_selection.value

    def load_preset(self, widget):
        """
        Loads selected preset
        """
        cam_selection = widget.window.widgets.get('cam_selection')
        preset_selection = widget.window.widgets.get('preset_selection')
        person_label = widget.window.widgets.get('person_label')
        cam_selection.items = self.p_h.get_people(preset_selection.value)
        for cam in self.cams.values():
            cam[1] = ''
        person_label.text = ''

    def delete_preset(self, widget):
        """
        Deletes selected preset
        :param widget:
        :return:
        """
        preset_selection = widget.window.widgets.get('preset_selection')
        cam_selection = widget.window.widgets.get('cam_selection')
        self.p_h.remove_preset(preset_selection.value)
        self.p_h.save_presets()
        preset_selection.items = self.p_h.get_preset_names()
        cam_selection.items = []

    def edit_profile_window(self, widget):
        # pylint: disable=attribute-defined-outside-init
        """
        Window for editing profiles
        :param widget:
        :return:
        """

        def hide_window(widget):
            """
            Hides window
            """
            preset_selection = widget.app.main_window.widgets.get('preset_selection')
            save_edit = None
            for item in widget.content.children:
                if item.id == 'save_edit':
                    save_edit = item
                if item.id == 'edit_box':
                    edit_box = item
                if item.id == 'edit_window':
                    edit_window = item
            preset_selection.enabled = True
            children = edit_box.children
            for i in reversed(range(len(children))):
                edit_box.remove(children[i])
            if save_edit is None:
                widget.content.add(toga.Button(id='save_edit', text='Save edit', style=Pack(width=420), on_press=self.save_edit))
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
                        for person in self.p_h.get_people(preset_selection.value):
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
        preset_name = toga.TextInput(id='preset_name', value=preset_selection.value, on_change=self.text_handler(20))
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
            for person in self.p_h.get_people(preset_selection.value):
                people_table.data.append(person)
        else:
            preset_name.value = ""
        window.content = box
        window.show()

    def save_edit(self, widget):
        """
        Saves preset
        """
        preset_name = widget.window.widgets.get('preset_name')
        if len(preset_name.value) == 0:
            preset_name.focus()
        else:
            preset_selection = widget.app.main_window.widgets.get('preset_selection')
            new_people = []
            for person in widget.window.widgets.get('people_table').data:
                new_people.append(person.people)
            if not self.new_preset:
                self.p_h.edit_preset(preset_selection.value, {"preset_name": preset_name.value, "people": new_people})
            else:
                self.p_h.new_preset({"preset_name": preset_name.value, "people": new_people})
            self.p_h.save_presets()
            widget.window.hide()
            cam_selection = widget.app.main_window.widgets.get('cam_selection')
            cam_selection.items = new_people
            preset_selection.enabled = True
            preset_selection.items = self.p_h.get_preset_names()
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
        if len(edit_box.children) == 0:
            def save_change(_widget):
                """
                Saves change to table and removes edit_box widget
                """
                if len(new_person.value) > 0:
                    people_table.data.append(new_person.value)
                children = edit_box.children
                for i in reversed(range(len(children))):
                    edit_box.remove(children[i])
                edit_window.add(save_edit)


            edit_box.add(
                new_person,
                toga.Button(id = 'save_change', text='Save Change', style=Pack(width=100), on_press=save_change)
            )

    def edit_person(self, widget):
        """
        Edits the selected person
        """
        people_table = widget.window.widgets.get('people_table')
        save_edit = widget.window.widgets.get('save_edit')
        edit_window = widget.window.widgets.get('edit_window')
        if people_table.selection is not None:
            edit_window.remove(save_edit)
            name_changed = toga.TextInput(placeholder='Leave blank to not edit', on_change=self.text_handler(20),
                                          style=Pack(width=320))
            edit_box = widget.window.widgets.get('edit_box')

            if len(edit_box.children) == 0:
                def save_change(_widget):
                    """
                    Saves changes to table and removes edit_box widget
                    """
                    if len(name_changed.value) > 0:
                        people = people_table.data._data
                        peopleEdited = []
                        for i, person in enumerate(people):
                            if person.people == people_table.selection.people:
                                peopleEdited.append(name_changed.value)
                            else:
                                peopleEdited.append(person.people)
                        people_table.data.clear()
                        for person in peopleEdited:
                            people_table.data.append(person)
                    children = edit_box.children
                    for i in reversed(range(len(children))):
                        edit_box.remove(children[i])
                    edit_window.add(save_edit)

                edit_box.add(
                    name_changed,
                    toga.Button(id='save_change', text='Save Change', style=Pack(width=100), on_press=save_change)
                )

    def text_handler(self, value):
        """
        Makes sure text stays with in limits as to not affect selection box width
        """

        def text_len_validation(widget):
            if len(widget.value) > value:
                widget.value = widget.value[0:value]

        return text_len_validation

    def map_cameras(self, widget):
        """
        Maps cameras to obs
        :param widget:
        :return:
        """
        window_selection = widget.window.widgets.get('window_selection')
        # print(self.image_proc.get_exe_name(window_selection.value))
        cameras = []
        for cam in self.cams.values():
            if platform.system() == 'Windows':
                cameras.append(
                    {'camName': cam[1], "x": cam[0][0] , "x1": cam[0][2] , "y": int(cam[0][1]) , "y1": cam[0][3]})
            if platform.system() == 'Linux':
                cameras.append(
                    {'camName': cam[1], "x": cam[0][0] , "x1": cam[0][2] , "y": int(cam[0][1]) + 40 , "y1": cam[0][3]})
        obs_cams_send = str({
            "arg": "crop camera",
            "os": platform.system(),
            "exe": self.image_proc.get_exe_name(window_selection.value),
            "cameras": cameras
        })
        self.obs_server.send_command(obs_cams_send)


if __name__ == "__main__":
    app = ObsMapper("OBS Call Mapper", "org.lunarsoftware.obscallmapper", author='Luna', version=1)
    app.main_loop()
