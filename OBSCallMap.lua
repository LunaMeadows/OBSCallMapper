--https://obsproject.com/forum/threads/using-udp-ports-in-obs-lua.157274/post-576170
--Code inspired by John Hartman UDP-test.lua
obs = obslua
local socket = require("ljsocket")
local json = require("dkjson")
local our_server = nil

-- Set true to get debug printing
local debug_print_enabled = true

function debug_print(a_string)
    if debug_print_enabled then
        print(a_string)
    end
end

function script_load(settings)
    our_server = assert(socket.create("inet", "dgram", "udp"))

    -- Must set "reuseaddr" or bind will fail when you reload the script
    assert(our_server:set_option("reuseaddr", 1))
    -- Must set non-blocking to prevent the locking the OBS UI thread
    assert(our_server:set_blocking(false))
    -- Bind our_port on all local interfaces
    assert(our_server:bind('*', obs.obs_data_get_int(settings, "port")))

    -- Check for input once per second.
    obs.timer_add(client, 5000)
    print('Listening on UDP port ' .. obs.obs_data_get_int(settings, "port"))
end

function script_unload()
    debug_print("in script_unload")

    if our_server ~= nil then
        -- By the time we get here our callback has been removed.
        -- Attempting to remove it crashes OBS

        print('Shutting down our server')
        assert(our_server:close())
        our_server = nil
    end
end

function get_source(self, scene, win_title, cam_info)
    source = obs.obs_get_source_by_name(cam_info['camName'])
    if source == nil then
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "window", win_title)
        source = obs.obs_source_create("window_capture", cam_info['camName'], settings, None)
        obs.obs_scene_add(scene, source)
        obs.obs_scene_release(scene)
        obs.obs_data_release(settings)
        return source
    else
        return source
    end
end

function get_crop(self, source)
    crop = obs.obs_source_get_filter_by_name(source, "CamCrop")
    if crop == nil then
        _obs_data = obs.obs_data_create()
        obs.obs_data_set_bool(_obs_data, "relative", False)
        filter = obs.obs_source_create_private("crop_filter", "CamCrop", _obs_data)
        obs.obs_source_filter_add(source, filter)
        obs.obs_source_release(filter)
        obs.obs_data_release(_obs_data)
        time.sleep(1)
        return obs.obs_source_get_filter_by_name(source, "CamCrop")
    else
        return crop
    end
end

function crop_cam(win_title, cam_info)
    for  k,v in pairs(cam_info) do
        current_scene = obs.obs_frontend_get_current_scene()
        scene = obs.obs_scene_from_source(current_scene)
        source = self.get_source(scene, win_title, v)
        crop = self.get_crop(source)

        settings = obs.obs_source_get_settings(crop)
        i = obs.obs_data_set_int
        --left, top, cx, cy = ast.literal_eval(str(cam[1]))
        i(settings, "left", v['x'])
        i(settings, "top", v['y'])
        i(settings, "cx", v['x1'])
        i(settings, "cy", v['y1'])
        obs.obs_source_update(crop, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
        obs.obs_source_release(crop)
    end
end

local tick = 0
function client()
    tick = tick + 1
    debug_print("in client " .. tick)

    -- Get data until there is no more, or an error occurs
    repeat
        local data, status = our_server:receive_from()
        if data then
            local args = json.decode(data)
            debug_print('Data received after ' .. tick .. ' polls: "' .. data .. '"')
            if args['arg'] == ("crop camera") then
                print("Crop cameras")
                crop_cam(args['exe'], args['cameras'])
            end
        elseif status ~= "timeout" then
            error(status)
        end
    until data == nil
end

function script_description()
    return "Connects to the OBSCallMapper for mapping the camera positions in a call to individual sources automatticly in OBS to save time when setting up streams and fixing cameras mid stream" ..
    "\n\n By Luna"
end

function script_defaults(settings)
    obs.obs_data_set_default_int(settings, "port", 48387)
end

function script_properties()
    props = obs.obs_properties_create()
    obs.obs_properties_add_int(props, "port", "Port used to communicate with server. Leave default unless changed in server settings.", 0, 65535, 1)
    obs.obs_properties_add_button(props, "button", "Connect", connect)
    return props
end