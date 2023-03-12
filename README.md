
# OBS Call Mapper

OBS Call Mapper allows you to map cameras from programs like Discord and Zoom to OBS much easier. You simply set whos camera is who and press Map Cameras and they will get mapped to your OBS.


## How To Use

#### Warnings

Before running the application, make sure you have your call open and running. If you are using discord, make sure the call is poped out into it's own window.

#### Instalation
Download and install the appropriate version for your system. Ubuntu uses .AppImage and windows will use the .msi file.

On windows when you run the .msi file, windows defender may state that the file is unrecognized and say "Don't run". Click the more option and click "Run anyway" instead.

For the OBSScript.zip, unzip it to a known location and open OBS. Click Tools -> Scripts and then click the plus icon. Locate the OBSCallMap.lua script and add it to obs. You won't need to change anything once added. 

#### First Run

After installing, run the OBSCallMapper application and you will be greeted with the main interface. First click New Preset and create your first preset. Presets are how your information will be stored for easily setting cameras to people.

#### Setting Cameras
Once you are ready to set your cameras to people, use the drop down at the top of the right pane and find the name of the window of your call. If discord, it will be the name of the voice channel. After you have the proper window selected, click 'Select Window' and make sure none of the extra buttons are showing when the screen becomes active. If you do not get a camera image showing, try making sure the call window is not the last active window and try 'Select Window' again. 

Once you have cameras showing up, use the drop down at the bottom of the window to select the persons name who the camera belongs to and click bind. Use the next and previous buttons to cycle through the cameras and bind all of the cameras that are needed. 

#### Sending Cameras to OBS

Make sure the scene that will have the cameras is the active scene. Go back to OBSCallMapper and click Map Cameras. This will send all the needed information to OBS and map the cameras in OBS and you can then move and adjust the size of the cameras as needed. Each time Map Cameras is pressed it will update any present cameras but not move or adjust the size.
