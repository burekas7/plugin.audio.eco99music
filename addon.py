# coding=utf-8

import sys
import os
import urllib.request, urllib.parse, urllib.error
import xbmcaddon
import xbmcgui
import xbmcplugin
import requests
import re
import xmltodict


def build_url(query):
    """Build route url

    :param query: Dictionary to create URL for.
    :type query: dict
    :return: Complete route URL.
    :rtype: str
    """
    base_url = sys.argv[0]
    return base_url + '?' + urllib.parse.urlencode(query)


def get_rss(url):
    """Download the source XML for given RSS URL using requests
    and parse the page using xmltodict.

    :param url: URL of RSS page.
    :type url: str
    :return: Dictionary of parsed XML RSS page.
    :rtype: dict
    """
    return xmltodict.parse(requests.get(url).text)


def get_channels():
    """Extract channels from rss.

    :return: Return dictionary of received channels.
    :rtype: dict
    """
    rss = get_rss('http://eco99fm.maariv.co.il/RSS_MusicChannels_Index/')
    channels = {}
    index = 1

    for item in rss["rss"]["channel"]["item"]:
        channels.update({
            index: {
                'album_cover': re.search("src='([^']+)'", item['description']).group(1),
                'title'      : item['title'],
                'description': item['itunes:summary'],
                'url'        : build_url({
                                    'mode': 'playlist',
                                    'url': item['link']
                               })
            }
        })
        index += 1
    return channels


def get_playlists(url):
    """Get playlists of a channel.

    :param url: Channel rss url.
    :type url: str
    :return: Dictionary containing playlist items.
    :rtype: dict
    """
    rss = get_rss(url)

    playlists = {}
    index = 1

    for item in rss["rss"]["channel"]["item"]:
        playlists.update({
            index: {
                'album_cover': re.search("src='([^']+)'", item['description']).group(1),
                'title'      : item['title'],
                'description': item['itunes:summary'],
                'url'        : build_url({
                                'mode': 'stream',
                                'url': item['enclosure']['@url'] #item['guid']
                               })
            }
        })
        index += 1
    return playlists


def build_menu(items, is_folder):
    """Build menu control

    :param items: List of items, can be channels or playlist.
    :type items: list
    :param is_folder: If True the item is channel else a playlist.
    :type is_folder: bool
    """

    items_list = []

    for item in items:
        album_cover = clean_album_cover(items[item])

        # create a list item using the song filename for the label
        li = xbmcgui.ListItem(label = items[item]['title'])

        # set the fanart to the album cover
        # li.setProperty(
        #     'fanart_image',
        #     os.path.join(ADDON_FOLDER, 'resources/media/fanart.jpg'))

        li.setProperty('IsPlayable', 'false' if is_folder else 'true')

        # li.setProperty('PlotOutline', items[item]['description'])

        li.setInfo(
            type = 'video', infoLabels = {
                'title': items[item]['title'],
                'genre': 'Podcast',
                'plot': items[item]['description'],
                'plotoutline': items[item]['description'],
                'mediatype' : 'musicvideo'
            })

        li.setArt({
            'thumb' : album_cover,
            'poster': album_cover,
            'fanart': os.path.join(ADDON_FOLDER, 'resources/media/fanart.jpg')
        })

        url = items[item]['url']
        items_list.append((url, li, is_folder))
    xbmcplugin.addDirectoryItems(ADDON_HANDLE, items_list, len(items_list))
    xbmcplugin.setContent(ADDON_HANDLE, 'musicvideos')
    # xbmcplugin.endOfDirectory(ADDON_HANDLE)

def clean_album_cover(item):
    substring_to_remove = "https://eco99fm.maariv.co.il/download/Sets/pictures/"

    album_cover = item['album_cover']
    isSubstringExist = album_cover.count(substring_to_remove)

    if isSubstringExist > 1:
        album_cover = album_cover.replace(substring_to_remove, "", 1)
    elif isSubstringExist == 1 and 'SetsCategories' in album_cover:
        album_cover = album_cover.replace(substring_to_remove, "")

    return album_cover

def play(url):
    """Play playlist by URL.

    :param url: URL of playlist.
    :type url: str
    """
    play_item = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem=play_item)


def main():
    """Main method."""
    args = urllib.parse.parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)
    if mode is None:
        items = get_channels()
        build_menu(items, True)
    elif mode[0] == 'playlist':
        items = get_playlists(args['url'][0])
        build_menu(items, False)
    elif mode[0] == 'stream':
        play(args['url'][0])
        # play(args['url'][0].replace('/playlist.m3u8', ''))
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


if __name__ == '__main__':
    ADDON_FOLDER = xbmcaddon.Addon().getAddonInfo('path')
    ADDON_HANDLE = int(sys.argv[1])
    main()
