import os
import platform

from datetime import datetime

from xbmcswift2 import Plugin, xbmc, xbmcgui, xbmcplugin

plugin = Plugin()

sys.path.append(
    xbmc.translatePath(
        os.path.join(plugin.addon.getAddonInfo('path'), 'resources', 'lib')
    )
)

from deluge_client import DelugeRPCClient

def get_client():
    c = DelugeRPCClient(plugin.get_setting('ip', unicode),
                        plugin.get_setting('port', int),
                        plugin.get_setting('username', unicode),
                        plugin.get_setting('password', unicode))
    c.connect()
    return c

@plugin.route('/<infohash>/<path>')
def play_file(infohash, path):
    client = get_client()
    
    files = client.call('core.get_torrent_status', infohash, ['name', 'num_files', 'files', 'save_path', 'file_progress'])
    for progress, f in zip(files['file_progress'], files['files']):
        if f['path'] != path:
            continue
        
        if progress != 1.0:
            continue
        
        full_path = os.path.join(files['save_path'], f['path'])
        if os.path.isfile(full_path):
            name = path.split('/')[-1]
            item = {
                'label': name,
                'path': full_path,
            }
    
    if 'streaming.stream_torrent' not in client.call('daemon.get_method_list'):
        dialog = xbmcgui.Dialog()
        dialog.ok(plugin.get_string(31000), plugin.get_string(31001))
        return
    
    result = client.call('streaming.stream_torrent', infohash=infohash, filepath_or_index=path, includes_name=True, wait_for_end_pieces=True)
    name = path.split('/')[-1]
    item = {
        'label': name,
        'path': result['url'],
    }
    return plugin.play_video(item)

@plugin.route('/<infohash>')
def list_torrent(infohash):
    client = get_client()
    torrent = client.call('core.get_torrent_status', infohash, ['name', 'num_files', 'files'])
    
    items = []
    for f in torrent['files']:
        name = f['path'].split('/')[-1]
        items.append({
            'label': name,
            'path': plugin.url_for('play_file', infohash=infohash, path=f['path']),
            'is_playable': True,
        })
    
    plugin.add_sort_method(xbmcplugin.SORT_METHOD_LABEL)
    
    return items

@plugin.route('/')
def index():
    client = get_client()
    
    torrents = client.call('core.get_torrents_status', {}, ['name', 'num_files', 'time_added'])
    items = []
    for infohash, torrent in torrents.iteritems():
        items.append({
            'label': torrent['name'],
            'path': plugin.url_for('list_torrent', infohash=infohash),
            'info_type': {
                'date': datetime.fromtimestamp(torrent['time_added']).strftime('%d.%m.%Y'),
            },
        })
    
    plugin.add_sort_method(xbmcplugin.SORT_METHOD_DATEADDED)
    plugin.add_sort_method(xbmcplugin.SORT_METHOD_LABEL)
    
    return items

def do_first_run():
    if platform.system() in ('Windows', 'Microsoft'):
        auth_path = os.path.join(os.environ['APPDATA'], 'deluge')
    else:
        try:
            from xdg.BaseDirectory import save_config_path
        except ImportError:
            return
        
        auth_path = save_config_path('deluge')
    
    auth_path = os.path.join(auth_path, 'auth')
    if not os.path.isfile(auth_path):
        return
    
    with open(auth_path, 'rb') as f:
        filedata = f.read().split('\n')[0].split(':')
        if len(filedata) < 2:
            return
        
        username, password = filedata[:2]
    
    plugin.set_setting('ip', '127.0.0.1')
    plugin.set_setting('port', '58846')
    plugin.set_setting('username', username)
    plugin.set_setting('password', password)

def check_config():
    try:
        client = get_client()
        client.call('core.get_free_space')
    except:
        return False
    else:
        return True

if __name__ == '__main__':
    if not plugin.get_setting('first_run_done', str):
        plugin.set_setting('first_run_done', 'run')
        do_first_run()
    
    if not check_config():
        plugin.notify('Unable to connect to Deluge')
        plugin.open_settings()
    else:
        plugin.run()
