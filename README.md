
# OBS Call Mapper

OBS Call Mapper allows you to map cameras from programs like Discord and Zoom to OBS much easier. You simply set whos camera is who and press Map Cameras and they will get mapped to your OBS.


## How To Use

#### Warnings

Before running the application, make sure you have your call open and running. If you are using discord, make sure the call is poped out into it's own window.

#### Instalation
Download and install the appropriate version for your system. Ubuntu uses .AppImage, Windows will use the .msi file, and Mac uses the .dmg file.

On windows when you run the .msi file, windows defender may state that the file is unrecognized and say "Don't run". Click the more option and click "Run anyway" instead.

For the OBSScript.zip, unzip it to a known location and open OBS. Click Tools -> Scripts and then click the plus icon. Locate the OBSCallMap.lua script and add it to obs. You won't need to change anything once added. Make sure if you extract to the OBS scripts folder, you move all 3 files into the folder as they are all required.

#### First Run

After installing, run the OBSCallMapper application and you will be greeted with the main interface. A new preset window will pop up as well. The top bar is the name of the preset.

#### Setting Cameras
Once you are ready to set your cameras to people, use the drop down at the top of the right pane and find the name of the window of your call. If discord, it will be the name of the voice channel. After you have the proper window selected, click 'Select Window' and make sure none of the extra buttons are showing when the screen becomes active. If you do not get a camera image showing, try making sure the call window is not the last active window as well as the call buttons (Circle buttons along bottom on discord for example) are not visable and try 'Select Window' again. When the window pops up, make sure your mouse is not hovering over the call window to avoid any buttons from showing. You have a second to move your mouse out of the way before a screenshot is taken.

Once you have cameras showing up, use the drop down at the bottom of the window to select the persons name who the camera belongs to and click bind. Use the next and previous buttons to cycle through the cameras and bind all of the cameras that are needed. 

#### Mac OS or 'Select Screenshot'
For Mac users, there is a major limitation for getting window names and location information that makes it not possible to select a window like on Windows or Ubuntu. You will have to use the 'Select Screenshot' option. 

In order to use 'Select Screenshot' you will first need to take a screenshot of just the call window and save it as a .jpg, .jpeg, or .png file as well as create a window capture source with the name 'OBSMapper-PresetName' the PresetName will be the name of your preset in the application. After you create the source you will need to export your scene collection as a .json file.

Once you have the screenshot file and the exported json file, select 'Select Screenshot' and then press 'Select Window' and a file selection box or two will open open. First one will be to provide the screenshot file and the second one will be for the json file if you have not already provided one. If you have provided one in the past but need to update it, Select the file command option along the top and then 'Select OBS Source Export' and it will let you select the new json file. 

After that, you should see the camera images and you can use the program like normal. 

#### Sending Cameras to OBS

Make sure the scene that will have the cameras is the active scene. Go back to OBSCallMapper and click Map Cameras. This will send all the needed information to OBS and map the cameras in OBS and you can then move and adjust the size of the cameras as needed. Each time Map Cameras is pressed it will update any present cameras but not move or adjust the size.
