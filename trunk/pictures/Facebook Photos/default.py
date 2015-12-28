import urllib,urllib2,re,xbmcplugin,xbmcgui,os,datetime
from fbapi import Facebook,FacebookError

#.nF0
__plugin__  = "Facebook Photos"
__author__  = "leo212"
__date__    = "6 10 2009"
__version__ = "1"

dialog = xbmcgui.Dialog()
settings = {}
fb = {}

# settings enum
API_KEY, SECRET_KEY, SESSION_KEY, UID, USERNAME, PASSWORD, SHOW_ALBUMS_DATE = range(7)
def get_settings():        
        settings[API_KEY] =  xbmcplugin.getSetting( "api_key" )
        settings[SECRET_KEY] =  xbmcplugin.getSetting( "secret_key" )
        settings[SESSION_KEY] =  xbmcplugin.getSetting( "session_key" )
        settings[UID] =  xbmcplugin.getSetting( "uid" )
        settings[USERNAME] =  xbmcplugin.getSetting( "username" )
        settings[PASSWORD] =  xbmcplugin.getSetting( "password" )
        settings[SHOW_ALBUMS_DATE] =  xbmcplugin.getSetting( "showdate" )

def save_settings():
        xbmcplugin.setSetting( "session_key", settings[SESSION_KEY] )
        xbmcplugin.setSetting( "uid", settings[UID] )

def facebook_login():
        try:                
                fb.auth.createToken()
                if (settings[USERNAME]==""):
                        dialog.ok(xbmc.getLocalizedString( 30000 ), xbmc.getLocalizedString( 30010 ), xbmc.getLocalizedString( 30011 ))
                else:
                        fb.login(settings[USERNAME], settings[PASSWORD])        
                        session = fb.auth.getSession()
                        settings[SESSION_KEY] = session["session_key"]
                        settings[UID] = session["uid"]
                        save_settings()
        except FacebookError, (err):                        
                dialog.ok(xbmc.getLocalizedString( 30000 ), (xbmc.getLocalizedString( 30012 ) % err.code), err.msg)                

def facebook_login_with_session():
        try:                
                fb.session_key = settings[SESSION_KEY]
                fb.uid =  settings[UID]
                # check if the connection was successfull
                fb.users.getInfo([fb.uid], ['name', 'birthday'])
                return True
        except FacebookError, (err):
                # if session was expired
                if (err.code == "102"):
                        return False
                else:
                        dialog.ok(xbmc.getLocalizedString( 30000 ), (xbmc.getLocalizedString( 30012 ) % err.code), err.msg)
                        
def load_albums(albums, showOwner=False):
        # build a list of cover pids
        pids = []
        for album in albums:
                pid = album["cover_pid"]
                if (pid != "0"):
                        pids.append(pid)
                
        # query src of the pics
        pics_hash = {}
        pics_hash["0"] = ""
        pics = fb.photos.get(pids=pids)

        # build the pics hashmap
        for pic in pics:
                        pics_hash[pic["pid"]] = pic["src_big"]

        if (showOwner):
                # build a list of owner uids
                uids = []
                for album in albums:
                        uid = album["owner"]
                        uids.append(uid)

                # query name of the owners
                users_hash = {}
                users = fb.users.getInfo(uids, ['uid', 'name'])

                # build the owners hashmap
                for user in users:
                        users_hash[user["uid"]] = user["name"]

        # build the list of the albums
        for album in albums:
                if (showOwner):
                        name = "%s - %s" % (users_hash[album["owner"]], album["name"])
                else:
                        name = "%s" % (album["name"])

                if (settings[SHOW_ALBUMS_DATE]):
                        creationDate = datetime.datetime.fromtimestamp(int(album["created"]))
                        creationDateStr = creationDate.strftime("%Y-%m-%d")
                        name = "%s: %s" % (creationDateStr, name)
                                
                listitem = xbmcgui.ListItem( name, iconImage="DefaultPicture.png", thumbnailImage=pics_hash[album["cover_pid"]])
                xbmcplugin.addDirectoryItem( handle=int( handle ), url="%s?showAlbum&aid=%s" % (path, album["aid"]), listitem=listitem, isFolder=True, totalItems=len(albums))                


def show_albums(uid):
        albums=fb.photos.getAlbums(uid=uid)
        load_albums(albums)
        
def show_album(aid):
        photos=fb.photos.get(aid=aid)
        for photo in photos:                
                listitem = xbmcgui.ListItem( os.path.basename(photo["src_big"]), iconImage="DefaultPicture.png", thumbnailImage=photo["src_big"])
                xbmcplugin.addDirectoryItem( handle=int( handle ), url=photo["src_big"], listitem=listitem, isFolder=False, totalItems=len(photos))                

def show_photos_by_subject(uid):
        photos=fb.photos.get(subj_id=uid)
        for photo in photos:
                if (photo["caption"]!= ""):
                        name = photo["caption"].split("\n")[0]
                else:
                        name = os.path.basename(photo["src_big"])
                listitem = xbmcgui.ListItem( name, iconImage="DefaultPicture.png", thumbnailImage=photo["src_big"])
                xbmcplugin.addDirectoryItem( handle=int( handle ), url=photo["src_big"], listitem=listitem, isFolder=False, totalItems=len(photos))                

def show_recent():
        albums=fb.fql.query("SELECT owner,aid,name,cover_pid,created FROM   album WHERE  owner IN (SELECT uid2 FROM friend WHERE uid1=%s) ORDER BY created DESC LIMIT 1,10" % fb.uid)
        load_albums(albums, True)

def show_friends(showBySubject=False):
        if (showBySubject):
                action = "showPhotosBySubject"
        else:
                action = "showAlbums"
        frds=fb.users.getInfo(fb.friends.get(),['name', 'pic'])
        for friend in frds:
                listitem = xbmcgui.ListItem( friend["name"], iconImage="DefaultPicture.png", thumbnailImage=friend["pic"])
                xbmcplugin.addDirectoryItem( handle=int( handle ), url="%s?%s&uid=%s" % (path, action, friend["uid"]), listitem=listitem, isFolder=True, totalItems=len(frds))

def show_main_menu():
        listitem = xbmcgui.ListItem(xbmc.getLocalizedString( 30020 ), iconImage="DefaultPicture.png")
        xbmcplugin.addDirectoryItem( handle=int( handle ), url="%s?showAlbums&uid=%s" % (path, fb.uid) , listitem=listitem, isFolder=True)
        listitem = xbmcgui.ListItem(xbmc.getLocalizedString( 30021 ), iconImage="DefaultPicture.png")
        xbmcplugin.addDirectoryItem( handle=int( handle ), url="%s?showFriends" % (path), listitem=listitem, isFolder=True)
        listitem = xbmcgui.ListItem(xbmc.getLocalizedString( 30022 ), iconImage="DefaultPicture.png")
        xbmcplugin.addDirectoryItem( handle=int( handle ), url="%s?showRecent" % (path), listitem=listitem, isFolder=True)
        listitem = xbmcgui.ListItem(xbmc.getLocalizedString( 30023 ), iconImage="DefaultPicture.png")
        xbmcplugin.addDirectoryItem( handle=int( handle ), url="%s?showPhotosBySubject&uid=%s" % (path,fb.uid), listitem=listitem, isFolder=True)
        listitem = xbmcgui.ListItem(xbmc.getLocalizedString( 30024 ), iconImage="DefaultPicture.png")
        xbmcplugin.addDirectoryItem( handle=int( handle ), url="%s?showMyFriendsPhotos" % (path), listitem=listitem, isFolder=True)

def read_params(params_str):        
        params = {}
        if (len(params_str.split("?"))==2):
                args=params_str.split("?")[1].split("&")
                for arg in args:
                        pair = arg.split("=")
                        if (len(pair)==2):
                                params[pair[0]]=pair[1]
                        else:
                                params[pair[0]]=True
        return params
            
################ MAIN ####################
# read paramters
path = sys.argv[0]
handle = sys.argv[1]
params_str = sys.argv[2]
params = read_params(params_str)
            
# read settings from settings.xml
get_settings()                                       
fb = Facebook(settings[API_KEY], settings[SECRET_KEY])

# if there is no facebook session id
if (settings[SESSION_KEY] == ""):
        # login for the first time
        facebook_login()
else:
        # try to connect with the session id
        if (not facebook_login_with_session()):
                # if doesn't work - open browser login to get a new session id
                facebook_login()

if (len(params)==0):
        show_main_menu()
else:
        if params.has_key("showAlbums"):
                show_albums(params["uid"])
        elif params.has_key("showFriends"):
                show_friends()
        elif params.has_key("showRecent"):
                show_recent()
        elif params.has_key("showAlbum"):
                show_album(params["aid"])
        elif params.has_key("showPhotosBySubject"):
                show_photos_by_subject(params["uid"])
        elif params.has_key("showMyFriendsPhotos"):
                show_friends(True)
             
xbmcplugin.endOfDirectory(int(handle))
