# -*- coding: utf-8 -*-
# Module: default
# Author: cache
# Created on: 30.4.2019
# License: AGPL v.3 https://www.gnu.org/licenses/agpl-3.0.html

import sys
from urllib import urlencode
from urlparse import parse_qsl, urlparse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import resolveurl
import urlresolver
import requests
import traceback
import re
from bs4 import BeautifulSoup

_url = sys.argv[0]
_handle = int(sys.argv[1])

_addon = xbmcaddon.Addon()
_session = requests.Session()
_profile = xbmc.translatePath( _addon.getAddonInfo('profile')).decode('utf-8')

BASE = 'http://dokumenty.tv/'
SORT = 'orderby='
HEADERS={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36', 'Referer': BASE}

CATEGORIES = [
    {'cat':'','msg':_addon.getLocalizedString(30201)},
    {'cat':'category/historie/','msg':_addon.getLocalizedString(30202)},
    {'cat':'category/katastroficke/','msg':_addon.getLocalizedString(30203)},
    {'cat':'category/konspirace/','msg':_addon.getLocalizedString(30204)},
    {'cat':'category/krimi/','msg':_addon.getLocalizedString(30205)},
    {'cat':'category/mysleni/','msg':_addon.getLocalizedString(30206)},
    {'cat':'category/prirodovedny-dokument/','msg':_addon.getLocalizedString(30207)},
    {'cat':'category/technika/','msg':_addon.getLocalizedString(30208)},
    {'cat':'category/vesmir/','msg':_addon.getLocalizedString(30209)},
    {'cat':'category/zahady/','msg':_addon.getLocalizedString(30210)},
    {'cat':'category/zivotni-styl/','msg':_addon.getLocalizedString(30211)}
]

ORDERS = [
    {'order':'date','msg':_addon.getLocalizedString(30301)},
    {'order':'title','msg':_addon.getLocalizedString(30302)},
    {'order':'views','msg':_addon.getLocalizedString(30303)},
    {'order':'likes','msg':_addon.getLocalizedString(30304)},
    {'order':'comments','msg':_addon.getLocalizedString(30305)},
    {'order':'rand','msg':_addon.getLocalizedString(30306)}
]

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs, 'utf-8'))

def list_categories():
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30200))
    for category in CATEGORIES:
        list_item = xbmcgui.ListItem(label=category['msg'])
        list_item.setInfo('video', {'title': category['msg'],
                                    'genre': category['msg']})
        list_item.setArt({'icon': 'DefaultGenre.png'})
        link = get_url(action='items', category=category['cat'])
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30001))
    list_item.setInfo('video', {'title': _addon.getLocalizedString(30001),
                                'genre': _addon.getLocalizedString(30001)})
    list_item.setArt({'icon': 'DefaultAddonsSearch.png'})
    link = get_url(action='search')
    is_folder = True
    xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def list_orders(**kwargs):
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30300))
    for order in ORDERS:
        list_item = xbmcgui.ListItem(label=order['msg'])
        list_item.setInfo('video', {'title': order['msg'],
                                    'genre': order['msg']})
        list_item.setArt({'icon': 'DefaultPlaylist.png'})
        link = get_url(order=order['order'], **kwargs)
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def list_posts(posts, less, more):
    if less is not None:
        list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30003))
        list_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        link = less
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    for post in posts:
        #TODO - catch non existing elements, or multiple elements?
        img = post.select('img')[0]['src']
        title_block = post.select('h2')[0]
        title_link = title_block.select('a')[0]
        href = title_link['href']
        name = title_link.string
        summary = post.find_all('p', {'class' : 'entry-summary'}, True)
        if len(summary) > 0:
            summary = summary[0].string.strip()
            summary = " ".join(summary.split()) #strip inner whitespaces
        else:
            summary = ''
        list_item = xbmcgui.ListItem(label=name)
        list_item.setInfo('video', {'title': name, 'plot': summary})
        list_item.setArt({'thumb': img})
        list_item.setProperty('IsPlayable', 'true')
        link = get_url(action='play', href=href)
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

    if more is not None:
        list_item = xbmcgui.ListItem(label=_addon.getLocalizedString(30004))
        list_item.setArt({'icon': 'DefaultVideoPlaylists.png'})
        link = more
        is_folder = True
        xbmcplugin.addDirectoryItem(_handle, link, list_item, is_folder)

def list_items(category, order, page = 1):
    if order is None:
        list_orders(action='items', category=category, page=page)
        return
    xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30002))
    data_url = BASE + category + ('page/' + str(page) + '/' if page > 1 else '') + '?' + SORT + order
    data_raw = _session.get(data_url, headers=HEADERS)
    data_text = data_raw.text.replace('</time></a>','</time>') #bullshit
    html = BeautifulSoup(data_text, 'html.parser')
    posts = html.find_all('div', {'id' : re.compile('post-[0-9]*')}, True)

    if page > 1:
        less = get_url(action='items', category=category, order=order, page=page-1)
    else:
        less = None

    nextpostslink = html.find_all('a', {'class' : 'nextpostslink', 'rel':'next'}, True)

    if len(nextpostslink) > 0:
        more = get_url(action='items', category=category, order=order, page=page+1)
    else:
        more = None

    list_posts(posts, less, more)

    xbmcplugin.endOfDirectory(_handle, updateListing=page > 1)

def list_search(query, order, page = 1):
    if query is None:
        kb = xbmc.Keyboard('', _addon.getLocalizedString(30001))
        kb.doModal()
        if kb.isConfirmed():
            query = kb.getText()
        else:
            query = ''

    if query:
        if order is None:
            list_orders(action='search', query=query, page=page)
            return
        xbmcplugin.setPluginCategory(_handle, _addon.getLocalizedString(30002))
        data_url = BASE + ('page/' + str(page) + '/' if page > 1 else '') + '?' + urlencode({'s':query}, 'utf-8') + '&' + SORT + order
        data_raw = _session.get(data_url, headers=HEADERS)
        data_text = data_raw.text.replace('</time></a>','</time>') #bullshit
        html = BeautifulSoup(data_text, 'html.parser')
        posts = html.find_all('div', {'id' : re.compile('post-[0-9]*')}, True)

        if len(posts) == 1 and posts[0]['id'] == 'post-0':
            xbmcplugin.endOfDirectory(_handle, updateListing=page > 1)
            return

        if page > 1:
            less = get_url(action='search', query=query, order=order, page=page-1)
        else:
            less = None

        nextpostslink = html.find_all('a', {'class' : 'nextpostslink', 'rel':'next'}, True)

        if len(nextpostslink) > 0:
            more = get_url(action='search', query=query, order=order, page=page+1)
        else:
            more = None

        list_posts(posts, less, more)

    xbmcplugin.endOfDirectory(_handle, updateListing=page > 1)

def manual_resolve(html):
    video = html.find_all('div', {'id' : 'video'}, True)
    if len(video) != 1:
        return ''
    video = video[0]
    
    objectf = video.select('object')
    if len(objectf) == 1:
        #probably old flash video
        objectf = objectf[0]
        embed = objectf.select('embed')
        if len(embed) == 1:
            embed = embed[0]
            url = embed['src']
            parsed = urlparse(url)
            if parsed.netloc == 'www.veoh.com':
                params = dict(parse_qsl(parsed.query))
                if 'permalinkId' in params:
                    return 'https://www.veoh.com/watch/' + params['permalinkId']
    
    script = video.select('script')
    if len(script) == 1:
        #probably embeded via script
        script = script[0]
        src = script['src']
        parsed = urlparse(src)
        if parsed.netloc == 'tune.pk':
            params = dict(parse_qsl(parsed.query))
            if 'vid' in params:
                return 'https://tune.pk/video/' + params['vid']
    return ''

def resolve(url):
    xbmc.log('Resolving: '+url,level=xbmc.LOGNOTICE)
    resolved = False
    try:
        resolved = resolveurl.resolve(url)
    except Exception as e:
        xbmc.log(str(e),level=xbmc.LOGNOTICE)
    
    if resolved == False:
        try:
            resolved = urlresolver.resolve(url)
        except Exception as e:
            xbmc.log(str(e),level=xbmc.LOGNOTICE)
    
    xbmc.log('Resolved: '+str(resolved),level=xbmc.LOGNOTICE)
    return resolved

def play(href):
    data_raw = _session.get(href, headers=HEADERS)
    html = BeautifulSoup(data_raw.text, 'html.parser')

    #let's manual resolve first
    manual_url = manual_resolve(html)

    #now iframes
    iframes = html.select('iframe')

    #now joint them
    if '' != manual_url:
        urls = [manual_url] + ['%s' % (iframe['src']) for iframe in iframes]
    else :
        urls = ['%s' % (iframe['src']) for iframe in iframes]

    count = len(urls)

    url = ''

    if count > 1:
        # choose dialog
        dialog = xbmcgui.Dialog()
        opts = ['%s' % (urlparse(iurl).netloc) for iurl in urls]
        index = dialog.select(_addon.getLocalizedString(30007), opts) #TODO
        if index != -1:
            url = urls[index]
        else:
            xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())
            return
    elif count == 1:
        #direct play
        url = urls[0]

    if url != '':
        url = resolve(url)
    else:
        xbmcgui.Dialog().ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(30005))
        xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())
        return

    if url == '' or url == False:
        xbmcgui.Dialog().ok(_addon.getAddonInfo('name'), _addon.getLocalizedString(30006))
        xbmcplugin.setResolvedUrl(_handle, False, xbmcgui.ListItem())
        return

    try:
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(_handle, True, listitem)
    except Exception as e:
        xbmc.log(str(e),level=xbmc.LOGNOTICE)
        traceback.print_exc()
        xbmcgui.Dialog().ok(_addon.getAddonInfo('name'), str(e))
    


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if 'order' in params:
            order = params['order']
        else:
            order = None
        if params['action'] == 'items':
            if 'category' in params:
                category = params['category']
            else: 
                category = ''
            try:
                page = int(params['page'])
            except:
                page = 1
            list_items(category, order, page)
        elif params['action'] == 'search':
            if 'query' in params:
                query = params['query']
            else:
                query = None
            try:
                page = int(params['page'])
            except:
                page = 1
            list_search(query, order, page)
        elif params['action'] == 'play':
            play(params['href'])
        else:
            list_categories()
    else:
        list_categories()
