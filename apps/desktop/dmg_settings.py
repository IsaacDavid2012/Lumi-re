import os

volume_name = 'Lumière'
format = 'UDBZ' # bzip2 compressed DMG
size = None

files = [('dist/mac/Lumière.app', 'Lumière.app')]
symlinks = {'Applications': '/Applications'}

icon_locations = {
    'Lumière.app': (140, 180),
    'Applications': (440, 180)
}

window_rect = ((200, 200), (580, 380))
default_view = 'icon-view'
show_status_bar = False
show_tab_view = False
show_pathbar = False
show_sidebar = False
icon_size = 96
text_size = 13
