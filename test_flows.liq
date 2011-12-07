#!../liquidsoap/src/liquidsoap

%include "../liquidsoap/scripts/pervasives.liq"

# Test!
set("log.level",4)
set("log.file",false)
set("log.stdout",true)
set("server.telnet",true)

# Create a stream
source = playlist(id="src","~/music")
add_skip_command(source)

# Register a flow
source = register_flow(radio="My radio",website="http://my.web.site/",
                       description="The sound of my computer",genre="porn groove",
                       streams=[("mp3/128k","http://my.web.site/stream")],
                       source)

# Play it!
output.oss(fallible=true,source)
